import shutil
from pathlib import Path

import pytest
from cortexforge.repository import git


@pytest.fixture(autouse=True)
def isolate_test_configuration(monkeypatch):
    # User .env must never redirect tests into the application's database or provider account.
    for name in (
        "DATABASE_URL",
        "GROQ_API_KEY",
        "LLM_MODEL",
        "MODEL_ANALYST",
        "MODEL_ARCHITECT",
        "MODEL_DEVELOPER",
        "MODEL_RESOLVER",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def sample(tmp_path):
    target = tmp_path / "sample"
    shutil.copytree(
        Path(__file__).resolve().parents[2] / "sample-repos/payments",
        target,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    git(target, "init")
    git(target, "add", ".")
    git(target, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "baseline")
    return target


class ContractExecutor:
    """Test double for orchestration only. Does not claim actual test execution."""

    def available(self):
        return True

    def run(self, workspace, operation):
        source = (Path(workspace) / "payments.py").read_text()
        failure = (operation in {"unit", "acceptance"} and "// 10\n" in source) or (
            operation == "security" and "eval(" in source
        )
        failure |= operation == "acceptance" and "def apply_discount" not in source
        return {
            "operation": operation,
            "command": ["TEST_DOUBLE", operation],
            "exit_code": int(failure),
            "output": "Injected contract result",
            "executor": "test_double",
            "duration_ms": 0,
        }


@pytest.fixture
def engine(tmp_path, monkeypatch):
    from cortexforge.workflow import Engine

    monkeypatch.delenv("DATABASE_URL", raising=False)
    return Engine(tmp_path / "data", executor=ContractExecutor())
