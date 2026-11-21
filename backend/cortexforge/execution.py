import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

from cortexforge.acceptance import PAYMENTS_ORACLE
from cortexforge.refund_acceptance import REFUND_ORACLE
from cortexforge.repository import digest, safe_path


class ExecutionBlocked(RuntimeError):
    pass


def bounded_run(command, timeout):
    """Drain output continuously with bounded host memory, even for noisy code."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    tail = bytearray()
    total = 0

    def drain():
        nonlocal total
        while chunk := process.stdout.read(8192):
            total += len(chunk)
            tail.extend(chunk)
            if len(tail) > 50_000:
                del tail[:-50_000]

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    timed_out = False
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait(timeout=10)
        code = 124
    reader.join(timeout=5)
    if not reader.is_alive():
        process.stdout.close()
    return code, tail.decode("utf-8", errors="replace"), timed_out, total > 50_000


COMMANDS = {
    "unit": ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
    "lint": ["ruff", "check", "--no-cache", "."],
    "security": ["bandit", "--ignore-nosec", "-r", ".", "-x", "./tests", "-f", "json"],
    "acceptance": ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "_cortexforge_acceptance.py"],
}

# This is a container-only mount target. Host paths use TemporaryDirectory.
CONTAINER_TMPFS = "/tmp:rw,noexec,nosuid,size=64m"  # nosec B108


def summarize(result):
    """Derive counts/findings from actual tool output, never model assertions."""
    if result["operation"] in {"unit", "acceptance"}:
        counts = {}
        found = False
        for kind in ("passed", "failed", "error", "skipped"):
            matches = re.findall(r"(\d+) " + kind, result["output"])
            counts[kind] = int(matches[-1]) if matches else 0
            found |= bool(matches)
        result["test_counts"] = counts if found else None
    if result["operation"] == "security":
        import json

        try:
            raw = result["output"]
            start = raw.index("{")
            report, _ = json.JSONDecoder().raw_decode(raw[start:])
            if not isinstance(report.get("results"), list) or not isinstance(report.get("errors"), list):
                raise ValueError("Missing scanner report fields")
            if report["errors"] and result["exit_code"] == 0:
                result["exit_code"] = 125
            result["findings"] = [
                {
                    "rule": f["test_id"],
                    "tool_severity": f["issue_severity"],
                    "policy_severity": "critical"
                    if f["test_id"] in {"B307", "B602"}
                    else f["issue_severity"].lower(),
                    "file": f["filename"],
                    "line": f["line_number"],
                    "message": f["issue_text"],
                }
                for f in report.get("results", [])
            ]
        except (ValueError, KeyError):
            result["findings"] = None
            result["parse_error"] = "Scanner report could not be parsed; exit status remains authoritative"
            if result["exit_code"] == 0:
                result["exit_code"] = 125
    return result


class DockerExecutor:
    """Only fixed operations; generated commands are never accepted."""

    def __init__(self, image=None, timeout=60):
        if os.getenv("EXECUTION_MODE", "docker") != "docker":
            raise ExecutionBlocked("Only EXECUTION_MODE=docker is supported")
        self.image = image or os.getenv("SANDBOX_IMAGE", "cortexforge-sandbox:local")
        self.timeout = timeout

    def available(self):
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.image], capture_output=True, timeout=10
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def run(self, workspace, operation, profile="payments_discount"):
        if operation not in COMMANDS:
            raise ExecutionBlocked("Unsupported execution operation")
        if not self.available():
            raise ExecutionBlocked("Docker engine or sandbox image unavailable; host fallback is forbidden")
        image_info = subprocess.run(
            ["docker", "image", "inspect", "--format={{.Id}}", self.image],
            capture_output=True, timeout=10,
        )
        image_id = image_info.stdout.decode().strip() or self.image
        oracle_hash = None
        name = "cortexforge-" + uuid.uuid4().hex
        start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="cortexforge-sandbox-") as tmp:
            root = Path(workspace)
            # Export source only; do not mount Git metadata or host environment.
            for path in root.rglob("*"):
                relative = path.relative_to(root).as_posix()
                if path.name == ".git" or any(p.startswith(".") for p in path.relative_to(root).parts):
                    continue
                safe_path(root, relative)
                if path.is_file():
                    destination = Path(tmp) / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, destination)
            if operation == "acceptance":
                oracle = Path(tmp) / "_cortexforge_acceptance.py"
                if oracle.exists():
                    raise ExecutionBlocked("Reserved acceptance oracle path already exists")
                oracles = {"payments_discount": PAYMENTS_ORACLE, "refunds": REFUND_ORACLE}
                if profile not in oracles:
                    raise ExecutionBlocked("Unsupported acceptance profile")
                oracle_hash = digest(oracles[profile])
                oracle.write_text(oracles[profile], encoding="utf-8")
            command = [
                "docker",
                "run",
                "--rm",
                "--name",
                name,
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "64",
                "--cpus",
                "1",
                "--memory",
                "256m",
                "--memory-swap",
                "256m",
                "--user",
                "65534:65534",
                "--tmpfs",
                CONTAINER_TMPFS,
                "--mount",
                f"type=bind,src={tmp},dst=/workspace,readonly",
                image_id,
                *COMMANDS[operation],
            ]
            try:
                code, output, timed_out, truncated = bounded_run(command, self.timeout)
            finally:
                subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=15)
        return summarize(
            {
                "operation": operation,
                "command": COMMANDS[operation],
                "exit_code": code,
                "output": output,
                "truncated": truncated,
                "duration_ms": round((time.monotonic() - start) * 1000),
                "timeout": timed_out,
                "executor": "docker",
                "image": self.image,
                "image_id": image_id,
                "oracle_hash": oracle_hash,
            }
        )
