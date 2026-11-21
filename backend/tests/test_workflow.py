import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from cortexforge.api import create_app
from cortexforge.contracts import CreateRun, Review
from cortexforge.execution import DockerExecutor, ExecutionBlocked
from cortexforge.providers import DemoProvider, Response
from cortexforge.repository import PolicyViolation, git, safe_path
from cortexforge.workflow import Engine
from fastapi.testclient import TestClient


def create(engine, sample, fault="none"):
    return engine.create(
        CreateRun(
            repository=str(sample),
            mode="demo",
            fault=fault,
            requirement="Add apply_discount with validated percentage and integer paise",
        )
    )


def test_vertical_slice_repair_review_and_source_preserved(engine, sample):
    before = (sample / "payments.py").read_bytes()
    run = engine.run(create(engine, sample, "test")["id"])
    assert run["state"] == "AWAITING_HUMAN_APPROVAL"
    assert run["repairs"] == 1
    assert any(c["exit_code"] == 1 for c in run["checks"])
    assert run["rubric"]["baseline_passed"] == 3
    assert run["rubric"]["candidate_passed"] == 4
    assert (sample / "payments.py").read_bytes() == before
    assert git(sample, "status", "--porcelain") == ""
    assert "cortexforge/" in git(run["workspace"], "branch", "--show-current")
    assert "test_discount.py" in run["diff"]
    approved = engine.review(
        run["id"],
        Review(
            decision="approve",
            reviewer="Test human",
            comment="Checked evidence",
            evidence_hash=run["evidence_hash"],
        ),
    )
    assert approved["state"] == "APPROVED"
    assert engine.store.history(run["id"])[-2]["kind"] == "human_decision"


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("security", "Security gate"),
        ("scope", "New files"),
        ("repeat", "Repeated action"),
        ("malformed", "Malformed"),
        ("disagree", "disagreement exhausted"),
    ],
)
def test_failure_scenarios(engine, sample, fault, reason):
    run = engine.run(create(engine, sample, fault)["id"])
    assert run["state"] == "FAILED"
    assert reason in run["error"]
    with pytest.raises(PolicyViolation):
        engine.review(
            run["id"],
            Review(decision="approve", reviewer="test", comment="must not approve", evidence_hash=""),
        )
    if fault == "scope":
        assert engine.repo.diff(run["workspace"]) == ""
    if fault == "malformed":
        assert len([e for e in engine.store.history(run["id"]) if e["kind"] == "validation_error"]) == 2
    if fault == "repeat":
        assert len(run["actions"]) == 1
    if fault == "disagree":
        assert run["disagreements"] == 3
        assert not run["actions"]


def test_provider_outage_resume_and_usage(engine, sample):
    run = engine.run(create(engine, sample, "provider")["id"])
    assert run["state"] == "BLOCKED"
    assert run["resume_state"] == "IMPLEMENTING"
    usage = [e["payload"] for e in engine.store.history(run["id"]) if e["kind"] == "model_usage"]
    assert usage[-1]["cost_status"] == "unknown"
    assert usage[-1]["agent"] == "developer"
    engine.resume(run["id"], clear_demo_fault=True)
    assert engine.run(run["id"])["state"] == "AWAITING_HUMAN_APPROVAL"


def test_docker_blocker_does_not_fall_back(engine, sample):
    class Unavailable:
        def run(self, *args):
            raise ExecutionBlocked("Docker unavailable")

    engine.executor = Unavailable()
    run = engine.run(create(engine, sample)["id"])
    assert run["state"] == "BLOCKED"
    assert run["resume_state"] == "BASELINE"
    assert run["actions"] == []


@pytest.mark.parametrize("name", ["../escape.py", "C:/escape.py", "/escape.py", ".git/config", "a\\b.py"])
def test_path_escape(tmp_path, name):
    with pytest.raises(PolicyViolation):
        safe_path(tmp_path, name)


def test_approval_auth_tamper_and_patch(engine, sample, monkeypatch):
    monkeypatch.setenv("REVIEW_TOKEN", "private-test-token")
    run = engine.run(create(engine, sample)["id"])
    client = TestClient(create_app(engine))
    body = {
        "decision": "approve",
        "reviewer": "Reviewer",
        "comment": "Reviewed",
        "evidence_hash": run["evidence_hash"],
    }
    assert client.post(f"/api/runs/{run['id']}/review", json=body).status_code == 401
    headers = {"X-Review-Token": "private-test-token"}
    assert client.get(f"/api/runs/{run['id']}/patch", headers=headers).status_code == 409
    source = Path(run["workspace"]) / "payments.py"
    original = source.read_text()
    source.write_text(original + "\n# tamper\n")
    assert client.post(f"/api/runs/{run['id']}/review", json=body, headers=headers).status_code == 409
    source.write_text(original, newline="\n")
    assert client.post(f"/api/runs/{run['id']}/review", json=body, headers=headers).status_code == 200
    assert "apply_discount" in client.get(f"/api/runs/{run['id']}/patch", headers=headers).text
    assert client.post(f"/api/runs/{run['id']}/review", json=body, headers=headers).status_code == 409


def test_api_create_run(engine, sample, monkeypatch):
    monkeypatch.setenv("REVIEW_TOKEN", "test-token")
    client = TestClient(create_app(engine))
    response = client.post(
        "/api/runs",
        headers={"X-Review-Token": "test-token"},
        json={
            "requirement": "Add apply_discount with integer paise",
            "repository": str(sample),
            "mode": "demo",
        },
    )
    assert response.status_code == 200
    run_id = response.json()["id"]
    detail = client.get(f"/api/runs/{run_id}", headers={"X-Review-Token": "test-token"}).json()
    assert detail["state"] == "AWAITING_HUMAN_APPROVAL"
    assert detail["events"]


def test_process_restart_retains_state_and_checkpoint(tmp_path, sample):
    data = str(tmp_path / "process-data")

    def cli(*args):
        proc = subprocess.run(
            [sys.executable, "-m", "cortexforge.cli", *args, "--data", data],
            capture_output=True,
            text=True,
            timeout=40,
            env={k: v for k, v in os.environ.items() if k != "DATABASE_URL"},
        )
        assert proc.returncode == 0, proc.stderr
        return json.loads(proc.stdout)

    created = cli("create", "--repository", str(sample))
    first = cli("step", "--id", created["id"])
    assert first["state"] == "REQUIREMENT_ANALYSIS"
    second = cli("step", "--id", created["id"])
    assert second["state"] == "ARCHITECTURE_PLANNING"
    third = cli("show", "--id", created["id"])
    assert third["specification"] == second["specification"]
    assert third["version"] > first["version"]


def test_interrupted_patch_never_reapplied_across_processes(tmp_path, sample):
    data = tmp_path / "crash"
    engine = Engine(data)
    run = create(engine, sample)
    run["state"] = "IMPLEMENTING"
    run["pending"] = {"kind": "patch", "hash": "interrupted"}
    engine.store.save(run)
    proc = subprocess.run(
        [sys.executable, "-m", "cortexforge.cli", "run", "--data", str(data), "--id", run["id"]],
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert proc.returncode == 0, proc.stderr
    recovered = json.loads(proc.stdout)
    assert recovered["state"] == "BLOCKED"
    assert not recovered["actions"]
    with pytest.raises(PolicyViolation, match="Interrupted patch"):
        engine.resume(run["id"])
    assert engine.graph.get_state({"configurable": {"thread_id": run["id"]}}).values["run_id"] == run["id"]


def test_clarification(engine, sample):
    class Clarifier(DemoProvider):
        def generate(self, agent, context, schema):
            if agent == "analyst" and "Human clarification" not in context["requirement"]:
                return Response(
                    json.dumps(
                        {
                            "acceptance": ["Clarify currency"],
                            "tasks": ["Clarify"],
                            "questions": ["Which currency?"],
                            "constraints": [],
                        }
                    ),
                    {},
                )
            return super().generate(agent, context, schema)

    engine.provider = Clarifier()
    run = engine.run(create(engine, sample)["id"])
    assert run["state"] == "AWAITING_CLARIFICATION"
    engine.clarify(run["id"], "Integer INR paise")
    assert engine.run(run["id"])["state"] == "AWAITING_HUMAN_APPROVAL"


def test_repair_exhaustion(engine, sample):
    engine.limit = 0
    run = engine.run(create(engine, sample, "test")["id"])
    assert run["state"] == "FAILED"
    assert run["error"] == "Repair budget exhausted"


def test_disagreement_can_resolve(engine, sample):
    class Resolving(DemoProvider):
        def generate(self, agent, context, schema):
            if agent == "developer" and context.get("resolution"):
                context = {**context, "fault": "none"}
            return super().generate(agent, context, schema)

    engine.provider = Resolving()
    run = engine.run(create(engine, sample, "disagree")["id"])
    assert run["state"] == "AWAITING_HUMAN_APPROVAL"
    assert run["disagreements"] == 1
    assert run["resolution"]["decision"] == "retain"


def test_malformed_output_can_recover(engine, sample):
    class Recovering(DemoProvider):
        def generate(self, agent, context, schema):
            if agent != "analyst" or context.get("validation_errors"):
                context = {**context, "fault": "none"}
            return super().generate(agent, context, schema)

    engine.provider = Recovering()
    run = engine.run(create(engine, sample, "malformed")["id"])
    assert run["state"] == "AWAITING_HUMAN_APPROVAL"
    assert len([e for e in engine.store.history(run["id"]) if e["kind"] == "validation_error"]) == 1


def test_provider_retry_budget(engine, sample):
    run = engine.run(create(engine, sample, "provider")["id"])
    for _ in range(3):
        engine.resume(run["id"])
        run = engine.run(run["id"])
        assert run["state"] == "BLOCKED"
    with pytest.raises(PolicyViolation, match="budget"):
        engine.resume(run["id"])


def test_live_acceptance_profile_uses_trusted_gate(engine, sample):
    engine.provider = DemoProvider()  # Explicit injected test adapter, never a live-mode fallback.
    run = engine.create(
        CreateRun(
            repository=str(sample),
            mode="live",
            acceptance_profile="payments_discount",
            requirement="Add apply_discount with integer paise and validated percentages",
        )
    )
    result = engine.run(run["id"])
    assert result["state"] == "AWAITING_HUMAN_APPROVAL"
    assert result["acceptance_oracle"]
    assert {c["operation"] for c in result["checks"]} == {"unit", "lint", "security", "acceptance"}


def test_docker_operations_restricted():
    with pytest.raises(ExecutionBlocked, match="Unsupported"):
        DockerExecutor().run(".", "curl secret")


@pytest.mark.skipif(not DockerExecutor().available(), reason="Docker engine/image unavailable")
def test_real_docker_repair_and_security(tmp_path, sample):
    engine = Engine(tmp_path / "docker")
    run = engine.run(create(engine, sample, "test")["id"])
    assert run["state"] == "AWAITING_HUMAN_APPROVAL", run.get("error")
    assert run["repairs"] == 1
    assert "failed" in run["checks"][0]["output"]
    assert all(c["executor"] == "docker" for c in run["checks"])
    assert run["rubric"]["trusted_acceptance_tests"]["passed"] == 12
    assert next(c for c in run["baseline"] if c["operation"] == "acceptance")["exit_code"] != 0
    blocked = engine.run(create(engine, sample, "security")["id"])
    assert blocked["state"] == "FAILED"
    assert "B307" in blocked["checks"][-1]["output"]
    assert any(f["policy_severity"] == "critical" for f in blocked["checks"][-1]["findings"])


@pytest.mark.skipif(not DockerExecutor().available(), reason="Docker engine/image unavailable")
def test_real_workflow_resumes_after_process_exit(tmp_path, sample):
    data = str(tmp_path / "restart-docker")
    worker = """
import json, sys
from cortexforge.workflow import Engine
from cortexforge.contracts import CreateRun
engine = Engine(sys.argv[1])
run = engine.create(CreateRun(repository=sys.argv[2], mode='demo', requirement='Add apply_discount with integer paise'))
while run['state'] != 'TESTING':
    run = engine.advance(run['id'])
    if run['state'] in {'FAILED', 'BLOCKED'}:
        raise RuntimeError(run['error'])
print(json.dumps(run))
"""
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    first = subprocess.run(
        [sys.executable, "-c", worker, data, str(sample)],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    assert first.returncode == 0, first.stderr
    checkpoint = json.loads(first.stdout)
    assert len(checkpoint["actions"]) == 1
    restarted = subprocess.run(
        [sys.executable, "-m", "cortexforge.cli", "run", "--data", data, "--id", checkpoint["id"]],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    assert restarted.returncode == 0, restarted.stderr
    final = json.loads(restarted.stdout)
    assert final["state"] == "AWAITING_HUMAN_APPROVAL", final.get("error")
    assert final["actions"] == checkpoint["actions"]
    assert final["rubric"]["trusted_acceptance_tests"]["passed"] == 12
