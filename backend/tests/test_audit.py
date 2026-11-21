"""Independent audit regressions; injected providers are explicitly test doubles."""

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from cortexforge.contracts import CreateRun, FileChange
from cortexforge.providers import BASE, DemoProvider, GroqProvider, ProviderUnavailable, Response
from cortexforge.repository import PolicyViolation, git, safe_path
from test_workflow import create


@pytest.mark.parametrize(
    "name",
    [
        "./tests/test_payments.py",
        "tests//test_payments.py",
        ".GIT/config",
        "folder./x.py",
        "tests/test_x/conftest.py",
    ],
)
def test_test_infrastructure_aliases_rejected(engine, sample, name):
    run = create(engine, sample)
    with pytest.raises(PolicyViolation):
        engine.repo.apply(run["workspace"], [FileChange(path=name, content="# inert")], [name])


def test_root_conftest_is_immutable(engine, sample):
    (sample / "conftest.py").write_text("# baseline configuration\n")
    git(sample, "add", ".")
    git(
        sample,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "test configuration",
    )
    run = create(engine, sample)
    with pytest.raises(PolicyViolation):
        engine.repo.apply(
            run["workspace"], [FileChange(path="conftest.py", content="# changed")], ["conftest.py"]
        )


def test_noop_cannot_reach_review(engine, sample):
    class Noop(DemoProvider):
        def generate(self, agent, context, schema):
            response = super().generate(agent, context, schema)
            if agent == "developer":
                value = json.loads(response.text)
                value["changes"] = [{"path": "payments.py", "content": BASE}]
                return Response(json.dumps(value), response.usage)
            return response

    engine.provider = Noop()
    run = engine.create(CreateRun(repository=str(sample), requirement="Preserve the original totals API"))
    result = engine.run(run["id"])
    assert result["state"] == "FAILED"
    assert "source code change" in result["error"]


def test_link_escape_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    try:
        (root / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(root / "linked"), str(outside)], check=True, capture_output=True
        )
    with pytest.raises(PolicyViolation):
        safe_path(root, "linked/test.py")


@pytest.mark.parametrize(
    "body",
    [
        [],
        {"choices": []},
        {"choices": [{"message": []}]},
        {"choices": [{"message": {"content": ["bad"]}}]},
        {"choices": [{"message": {"content": "{}"}}], "usage": [1]},
    ],
)
def test_provider_invalid_envelopes_are_sanitized(monkeypatch, body):
    import httpx

    monkeypatch.setenv("GROQ_API_KEY", "test-only-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    with patch("httpx.Client") as client:
        client.return_value.__enter__.return_value.post.return_value = httpx.Response(200, json=body)
        with pytest.raises(ProviderUnavailable, match="unsupported response envelope"):
            GroqProvider().generate("analyst", {}, {})


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 503])
def test_provider_http_errors_do_not_leak(monkeypatch, status):
    import httpx

    monkeypatch.setenv("GROQ_API_KEY", "test-only-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    with patch("httpx.Client") as client:
        client.return_value.__enter__.return_value.post.return_value = httpx.Response(
            status, json={"error": "test-only-key"}
        )
        with pytest.raises(ProviderUnavailable) as error:
            GroqProvider().generate("analyst", {}, {})
        assert f"status={status}" in str(error.value)
        assert "test-only-key" not in str(error.value)


def test_missing_and_invalid_usage_remains_unknown(monkeypatch):
    import httpx

    monkeypatch.setenv("GROQ_API_KEY", "test-only-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("INPUT_PRICE_PER_MILLION", "nan")
    monkeypatch.setenv("OUTPUT_PRICE_PER_MILLION", "invalid")
    for usage in [
        {},
        {"prompt_tokens": -2, "completion_tokens": "50", "total_tokens": True},
        {"prompt_tokens": 10, "completion_tokens": 20, "completion_tokens_details": [1]},
    ]:
        body = {"choices": [{"message": {"content": "{}"}}], "usage": usage}
        with patch("httpx.Client") as client:
            client.return_value.__enter__.return_value.post.return_value = httpx.Response(200, json=body)
            result = GroqProvider().generate("analyst", {}, {})
        assert result.usage["cost_usd"] is None
        assert result.usage["total_tokens"] is None


def test_partial_response_cannot_be_accepted(engine, sample):
    class Partial(DemoProvider):
        def generate(self, agent, context, schema):
            result = super().generate(agent, context, schema)
            result.usage["finish_reason"] = "length"
            return result

    engine.provider = Partial()
    result = engine.run(create(engine, sample)["id"])
    assert result["state"] == "FAILED"
    events = engine.store.history(result["id"])
    assert len([e for e in events if e["kind"] == "model_usage"]) == 2
    assert not result["actions"]


def test_completed_check_reused_only_for_same_revision(engine, sample):
    run = create(engine, sample)
    while run["state"] != "TESTING":
        run = engine.advance(run["id"])
    engine._check(run, "unit")
    before = len([e for e in engine.store.history(run["id"]) if e["kind"] == "tool_execution"])
    engine.advance(run["id"])
    events = engine.store.history(run["id"])
    assert any(e["kind"] == "check_reused" for e in events)
    assert len([e for e in events if e["kind"] == "tool_execution"]) == before + 2


def test_two_concurrent_runs_are_isolated(engine, sample):
    runs = [create(engine, sample) for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(engine.run, [r["id"] for r in runs]))
    assert all(r["state"] == "AWAITING_HUMAN_APPROVAL" for r in results)
    assert results[0]["workspace"] != results[1]["workspace"]
    for run in results:
        assert len([e for e in engine.store.history(run["id"]) if e["kind"] == "patch_applied"]) == 1


def test_rejection_and_post_approval_tamper_block_export(engine, sample, monkeypatch):
    from cortexforge.api import create_app
    from fastapi.testclient import TestClient

    monkeypatch.setenv("REVIEW_TOKEN", "test-review")
    client = TestClient(create_app(engine))
    headers = {"X-Review-Token": "test-review"}
    for decision in ["reject", "approve"]:
        run = engine.run(create(engine, sample)["id"])
        body = {
            "decision": decision,
            "reviewer": "test",
            "comment": "controlled test",
            "evidence_hash": "outdated",
        }
        url = f"/api/runs/{run['id']}"
        assert client.post(url + "/review", headers=headers, json=body).status_code == 409
        body["evidence_hash"] = run["evidence_hash"]
        assert client.post(url + "/review", headers=headers, json=body).status_code == 200
        if decision == "approve":
            from pathlib import Path

            Path(run["workspace"], "payments.py").write_text("# harmless post-approval tamper")
        assert client.get(url + "/patch", headers=headers).status_code == 409


def test_cancel_during_model_call_prevents_patch(engine, sample):
    from cortexforge.locking import run_lock

    run = create(engine, sample)
    while run["state"] != "IMPLEMENTING":
        run = engine.advance(run["id"])

    class Cancelling(DemoProvider):
        def generate(self, agent, context, schema):
            if agent == "developer":
                engine.cancel(run["id"])
            return super().generate(agent, context, schema)

    engine.provider = Cancelling()
    with run_lock(engine.data / f"{run['id']}.lock"):
        result = engine.advance(run["id"])
    assert result["state"] == "CANCELLED"
    assert not result["actions"]
    assert not engine.repo.diff(run["workspace"])


def test_cancel_blocked_run_and_approval_gate(engine, sample, monkeypatch):
    from cortexforge.api import create_app
    from fastapi.testclient import TestClient

    monkeypatch.setenv("REVIEW_TOKEN", "test-review")
    run = engine.run(create(engine, sample, "provider")["id"])
    client = TestClient(create_app(engine))
    url = f"/api/runs/{run['id']}/cancel"
    assert client.post(url).status_code == 401
    response = client.post(url, headers={"X-Review-Token": "test-review"})
    assert response.status_code == 200 and response.json()["state"] == "CANCELLED"
    with pytest.raises(PolicyViolation):
        engine.resume(run["id"])


def test_provider_rejected_json_uses_bounded_schema_retry(engine, sample):
    from cortexforge.providers import ProviderMalformed

    class Invalid(DemoProvider):
        def generate(self, agent, context, schema):
            raise ProviderMalformed("Groq rejected JSON generation")

    engine.provider = Invalid()
    result = engine.run(create(engine, sample)["id"])
    assert result["state"] == "FAILED"
    assert "Malformed" in result["error"]
    assert len([e for e in engine.store.history(result["id"]) if e["kind"] == "model_usage"]) == 2


def test_model_feedback_is_bounded_but_raw_evidence_preserved(engine, sample):
    from cortexforge.contracts import Implementation

    run = create(engine, sample)
    run["checks"] = [{"operation": "unit", "exit_code": 1, "output": "x" * 10000}]
    engine._call(run, "developer", Implementation)
    context = next(e["payload"]["input"] for e in engine.store.history(run["id"])
                   if e["kind"] == "agent_input")
    assert len(context["checks"][0]["output"]) == 2500
    assert context["checks"][0]["output_is_tail"]
    assert len(run["checks"][0]["output"]) == 10000


def test_completed_check_survives_real_process_restart(engine, sample):
    import sys
    from pathlib import Path

    run = create(engine, sample)
    while run["state"] != "TESTING":
        run = engine.advance(run["id"])
    engine._check(run, "unit")
    run["worker_active"] = True
    engine.store.save(run)
    worker = '''
import sys, json
sys.path.insert(0, sys.argv[3])
from conftest import ContractExecutor
from cortexforge.workflow import Engine
engine = Engine(sys.argv[1], executor=ContractExecutor())
assert engine.store.get(sys.argv[2])["state"] == "BLOCKED"
engine.resume(sys.argv[2])
run = engine.run(sys.argv[2])
events = engine.store.history(run["id"])
print(json.dumps({"state": run["state"], "reused": sum(e["kind"] == "check_reused" for e in events)}))
'''
    proc = subprocess.run([sys.executable, "-c", worker, str(engine.data), run["id"],
                           str(Path(__file__).parent)], capture_output=True, text=True, timeout=40)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"state": "AWAITING_HUMAN_APPROVAL", "reused": 1}
