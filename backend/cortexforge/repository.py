import ast
import hashlib
import os
import re
import subprocess
from pathlib import Path, PurePosixPath


class PolicyViolation(RuntimeError):
    pass


def git(root, *args):
    env = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "core.fsmonitor=false", "-C", str(root), *args],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    if result.returncode:
        raise PolicyViolation(result.stderr[-2000:])
    return result.stdout


def safe_path(root: Path, name: str):
    if (
        not name
        or "\\" in name
        or ":" in name
        or "\x00" in name
        or PurePosixPath(name).is_absolute()
        or any(
            p in ("", ".", "..") or p.casefold() == ".git" or p.endswith((".", " ")) for p in name.split("/")
        )
    ):
        raise PolicyViolation(f"Unsafe repository path: {name!r}")
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()):
        raise PolicyViolation("Repository escape rejected")
    for parent in [path, *path.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise PolicyViolation("Links and junctions are not allowed")
    return path


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


class Repository:
    def __init__(self, data: Path):
        self.data = data.resolve()
        self.data.mkdir(parents=True, exist_ok=True)

    def isolate(self, source: str, run_id: str):
        try:
            source = Path(source).resolve(strict=True)
        except OSError:
            raise PolicyViolation("Supplied repository path does not exist or is inaccessible") from None
        if not source.is_dir():
            raise PolicyViolation("Repository must be a local directory")
        if git(source, "status", "--porcelain").strip():
            raise PolicyViolation("Commit supplied repository changes before import")
        # No checkout until tree entries have passed policy. Clone never alters source refs.
        target = self.data / run_id
        target.mkdir()
        git(target, "clone", "--bare", "--no-local", "--", str(source), str(target / "repo.git"))
        bare = target / "repo.git"
        entries = git(bare, "ls-tree", "-r", "HEAD").splitlines()
        if len(entries) > 1000:
            raise PolicyViolation("Initial supported repository limit is 1000 files")
        for entry in entries:
            mode, rest = entry.split(" ", 1)
            name = rest.split("\t", 1)[1]
            safe_path(target / "worktree", name)
            if mode not in ("100644", "100755"):
                raise PolicyViolation("Symlinks and submodules are unsupported")
        git(bare, "worktree", "add", "-b", f"cortexforge/{run_id}", str(target / "worktree"), "HEAD")
        return {
            "workspace": str(target / "worktree"),
            "branch": f"cortexforge/{run_id}",
            "base": git(bare, "rev-parse", "HEAD").strip(),
            "source": str(source),
        }

    def inspect(self, workspace):
        root = Path(workspace)
        names = git(root, "ls-files").splitlines()
        files = {}
        budget = 120_000
        for name in names:
            if name.endswith((".py", "pyproject.toml", "requirements.txt", "README.md")):
                path = safe_path(root, name)
                if path.stat().st_size > 50_000:
                    continue
                content = path.read_text(encoding="utf-8")
                if re.search(r"(?i)(api_key|password|secret)\s*=\s*['\"][^'\"]{8,}", content):
                    raise PolicyViolation(f"Potential secret in {name}; remove before model inspection")
                budget -= len(content)
                if budget < 0:
                    break
                files[name] = content
        return {
            "files": files,
            "tracked": names,
            "status": git(root, "status", "--porcelain"),
            "dependencies": {k: v for k, v in files.items() if k.endswith(("toml", "requirements.txt"))},
        }

    def validate_scope(self, workspace, files):
        root = Path(workspace)
        tracked = set(git(root, "ls-tree", "--name-only", "-r", "HEAD").splitlines())
        for name in files:
            safe_path(root, name)
            path = PurePosixPath(name)
            if path.name in {"conftest.py", "pytest.py", "bandit.py", "sitecustomize.py", "usercustomize.py"}:
                raise PolicyViolation("Test infrastructure and tool modules are immutable")
            if name in tracked and (
                "tests" in path.parts
                or "test" in path.parts
                or path.name.startswith("test_")
                or path.name.endswith("_test.py")
            ):
                raise PolicyViolation("Existing tests are immutable regression evidence")
            if not name.endswith(".py") or name.startswith("."):
                raise PolicyViolation("Only explicitly scoped Python files are writable")
            if name not in tracked and not (
                path.parent == PurePosixPath("tests") and path.name.startswith("test_")
            ):
                raise PolicyViolation("New files must be explicitly scoped tests/test_*.py")

    def apply(self, workspace, changes, scope):
        root = Path(workspace)
        names = [c.path for c in changes]
        if len(set(names)) != len(names):
            raise PolicyViolation("Duplicate file changes")
        self.validate_scope(workspace, names)
        for name in names:
            if name not in scope:
                raise PolicyViolation(f"Out-of-scope modification rejected: {name}")
        for change in changes:
            if re.search(r"(?i)(api_key|password|secret)\s*=\s*['\"][^'\"]{8,}", change.content):
                raise PolicyViolation("Potential hardcoded secret rejected before write")
        # Validate the entire batch before any writes.
        for change in changes:
            path = safe_path(root, change.path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(change.content, encoding="utf-8", newline="\n")
        # Intent-to-add makes new tests visible in the human-reviewed diff.
        if names:
            git(root, "add", "-N", "--", *names)
        return self.diff(workspace)

    def diff(self, workspace):
        return git(workspace, "diff", "--no-ext-diff", "--no-textconv", "HEAD", "--")

    def fingerprint(self, workspace):
        root = Path(workspace)
        # Includes untracked content so approval cannot overlook injected files.
        items = []
        for path in sorted(root.rglob("*")):
            if path.name == ".git":
                continue
            if path.is_file():
                name = path.relative_to(root).as_posix()
                safe_path(root, name)
                items.append(name + ":" + hashlib.sha256(path.read_bytes()).hexdigest())
        return digest("\n".join(items))

    def changed_files(self, workspace):
        return set(git(workspace, "diff", "--name-only", "HEAD", "--").splitlines()) | set(
            git(workspace, "ls-files", "--others", "--exclude-standard").splitlines()
        )

    def source_changed(self, workspace, names):
        """Ignore whitespace/comment-only edits when enforcing a code-path change."""
        for name in names:
            before = git(workspace, "show", "HEAD:" + name)
            after = safe_path(Path(workspace), name).read_text(encoding="utf-8")
            try:
                if ast.dump(ast.parse(before)) != ast.dump(ast.parse(after)):
                    return True
            except SyntaxError:
                raise PolicyViolation("Cannot release syntactically invalid Python source") from None
        return False
