import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from cortexforge.contracts import FileChange
from cortexforge.execution import DockerExecutor, bounded_run, summarize
from cortexforge.locking import run_lock
from cortexforge.providers import GroqProvider, ProviderUnavailable, strict_schema
from cortexforge.repository import PolicyViolation
from test_workflow import create


def test_existing_tests_immutable_and_batch_atomic(engine, sample):
    run = create(engine, sample)
    source = Path(run["workspace"]) / "payments.py"
    before = source.read_bytes()
    with pytest.raises(PolicyViolation, match="Existing tests"):
        engine.repo.apply(
            run["workspace"],
            [
                FileChange(path="payments.py", content="changed"),
                FileChange(path="tests/test_payments.py", content=""),
            ],
            ["payments.py", "tests/test_payments.py"],
        )
    assert source.read_bytes() == before


def test_secrets_rejected_before_write(engine, sample):
    run = create(engine, sample)
    with pytest.raises(PolicyViolation, match="secret"):
        engine.repo.apply(
            run["workspace"],
            [FileChange(path="payments.py", content='API_KEY = "abcdef123456789"')],
            ["payments.py"],
        )
    assert not engine.repo.diff(run["workspace"])


def test_execution_isolation_flags_and_timeout_cleanup(tmp_path):
    (tmp_path / "payments.py").write_text("# inert fixture")
    executor = DockerExecutor(timeout=1)
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    def fake_bounded(command, timeout):
        calls.append(command)
        return 124, "timeout evidence", True, False

    with patch("cortexforge.execution.subprocess.run", side_effect=fake_run):
        with patch("cortexforge.execution.bounded_run", side_effect=fake_bounded):
            result = executor.run(tmp_path, "unit")
    command = next(c for c in calls if c[1] == "run")
    for flag in [
        "--network",
        "--read-only",
        "--cap-drop",
        "--security-opt",
        "--pids-limit",
        "--cpus",
        "--memory",
        "--user",
    ]:
        assert flag in command
    assert "none" in command and "ALL" in command
    assert not any("docker.sock" in arg for arg in command)
    assert result["timeout"] and result["exit_code"] == 124
    assert calls[-1][1:3] == ["rm", "-f"]


def test_tool_output_buffer_and_timeout():
    # Trusted infrastructure probes, not generated repository code.
    code, output, timeout, truncated = bounded_run([sys.executable, "-c", "print('x' * 100000)"], 5)
    assert code == 0 and not timeout and truncated
    assert len(output) <= 50_000
    code, _, timeout, _ = bounded_run([sys.executable, "-c", "import time; time.sleep(5)"], 0.1)
    assert code == 124 and timeout


def test_unparseable_security_result_fails_closed():
    result = summarize({"operation": "security", "output": "not a report", "exit_code": 0})
    assert result["exit_code"] == 125
    assert result["findings"] is None
    assert summarize({"operation": "security", "output": "{}", "exit_code": 0})["exit_code"] == 125


def test_pytest_summary_does_not_double_count_collection_errors():
    result = summarize(
        {
            "operation": "unit",
            "output": "Interrupted: 1 error during collection\n1 error in 0.2s",
            "exit_code": 2,
        }
    )
    assert result["test_counts"]["error"] == 1


def test_provider_usage_and_cost_are_measured(monkeypatch):
    import httpx

    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("INPUT_PRICE_PER_MILLION", "1")
    monkeypatch.setenv("OUTPUT_PRICE_PER_MILLION", "2")
    body = {
        "choices": [{"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "completion_tokens_details": {"reasoning_tokens": 10},
        },
    }
    response = httpx.Response(200, json=body, headers={"x-ratelimit-limit-tokens": "8000"})
    with patch("httpx.Client") as factory:
        factory.return_value.__enter__.return_value.post.return_value = response
        result = GroqProvider().generate("developer", {}, {"type": "object"})
        payload = factory.return_value.__enter__.return_value.post.call_args.kwargs["json"]
    assert payload["response_format"]["json_schema"]["strict"]
    assert result.usage["input_tokens"] == 100
    assert result.usage["output_tokens"] == 50
    assert result.usage["cost_usd"] == pytest.approx(0.0002)  # Reasoning is already in completion tokens.
    assert result.usage["cost_status"] == "estimated"
    assert result.usage["rate_limits"]["x-ratelimit-limit-tokens"] == "8000"
    monkeypatch.delenv("INPUT_PRICE_PER_MILLION")
    with patch("httpx.Client") as factory:
        factory.return_value.__enter__.return_value.post.return_value = response
        result = GroqProvider().generate("developer", {}, {"type": "object"})
    assert result.usage["cost_usd"] is None
    assert result.usage["cost_status"] == "unknown"


def test_groq_rate_limit_is_safe_and_resumable(monkeypatch):
    import httpx

    monkeypatch.setenv("GROQ_API_KEY", "private-test-credential")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-oss-120b")
    response = httpx.Response(429, json={"error": "private-test-credential"}, headers={"retry-after": "12"})
    with patch("httpx.Client") as factory:
        factory.return_value.__enter__.return_value.post.return_value = response
        with pytest.raises(ProviderUnavailable) as error:
            GroqProvider().generate("analyst", {}, {"type": "object"})
    assert "status=429" in str(error.value) and "retry_after=12" in str(error.value)
    assert "private-test-credential" not in str(error.value)


def test_strict_schema_makes_nested_properties_required():
    from cortexforge.contracts import Implementation

    schema = strict_schema(Implementation.model_json_schema())
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["additionalProperties"] is False
    assert "default" not in schema["properties"]["disagreement"]
    assert schema["$defs"]["FileChange"]["additionalProperties"] is False


def test_os_lock_prevents_concurrent_work(tmp_path):
    with run_lock(tmp_path / "run.lock"):
        with pytest.raises(PolicyViolation, match="already executing"):
            with run_lock(tmp_path / "run.lock"):
                pytest.fail("Must not acquire a second lock")


def test_actual_process_kill_during_patch(engine, sample):
    run = create(engine, sample)
    worker = """
import sys, time
from pathlib import Path
from cortexforge.workflow import Engine
from cortexforge.locking import run_lock
engine = Engine(sys.argv[1])
run = engine.store.get(sys.argv[2])
with run_lock(engine.data / (run['id'] + '.lock')):
    run['state'] = 'IMPLEMENTING'
    run['pending'] = {'kind': 'patch', 'hash': 'crash-injected'}
    engine.store.save(run)
    Path(run['workspace'], 'payments.py').write_text('# partial write\\n')
    print('PENDING_WRITE_DURABLE', flush=True)
    time.sleep(30)
"""
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    proc = subprocess.Popen(
        [sys.executable, "-c", worker, str(engine.data), run["id"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert proc.stdout.readline().strip() == "PENDING_WRITE_DURABLE"
        proc.kill()
        proc.wait(timeout=10)
    finally:
        if proc.poll() is None:
            proc.kill()
    restarted = subprocess.run(
        [sys.executable, "-m", "cortexforge.cli", "run", "--data", str(engine.data), "--id", run["id"]],
        capture_output=True,
        text=True,
        timeout=40,
        env=env,
    )
    assert restarted.returncode == 0, restarted.stderr
    restored = json.loads(restarted.stdout)
    assert restored["state"] == "BLOCKED"
    assert restored["pending"]["hash"] == "crash-injected"
    assert Path(restored["workspace"], "payments.py").read_text() == "# partial write\n"
    assert not restored["actions"]


def test_tamper_between_checks_blocks_release(engine, sample):
    run = create(engine, sample)
    while run["state"] != "RELEASE_REVIEW":
        run = engine.advance(run["id"])
    Path(run["workspace"], "payments.py").write_text("# Changed after checks\n")
    result = engine.advance(run["id"])
    assert result["state"] == "FAILED"
    assert "current source" in result["error"]


def test_missing_repository_reports_policy_error(engine, tmp_path):
    with pytest.raises(PolicyViolation, match="does not exist"):
        create(engine, tmp_path / "missing")


@pytest.mark.skipif(not DockerExecutor().available(), reason="Docker engine/image unavailable")
def test_real_security_cannot_be_suppressed(tmp_path):
    (tmp_path / "unsafe.py").write_text("def run(value):\n    return eval(value)  # nosec B307\n")
    result = DockerExecutor().run(tmp_path, "security")
    assert result["exit_code"] == 1
    assert any(f["rule"] == "B307" and f["policy_severity"] == "critical" for f in result["findings"])
