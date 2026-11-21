"""Deterministic rubric on real Docker evidence; never creates human approval."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cortexforge.contracts import CreateRun  # noqa: E402
from cortexforge.workflow import Engine  # noqa: E402
from init_sample import prepare  # noqa: E402


def main():
    # Keep automated fault runs out of the user's human-review database.
    batch = uuid.uuid4().hex
    engine = Engine(Path(".cortexforge/evaluation") / batch)
    if not engine.executor.available():
        print("BLOCKED: start Docker and build scripts/Dockerfile.sandbox", file=sys.stderr)
        return 2
    repository = prepare(".cortexforge/sample")
    results = []
    expectations = {
        "none": "AWAITING_HUMAN_APPROVAL",
        "test": "AWAITING_HUMAN_APPROVAL",
        "security": "FAILED",
        "scope": "FAILED",
        "repeat": "FAILED",
        "malformed": "FAILED",
        "provider": "BLOCKED",
        "disagree": "FAILED",
    }
    for fault, expected in expectations.items():
        created = engine.create(
            CreateRun(
                repository=str(repository),
                mode="demo",
                fault=fault,
                requirement="Add apply_discount with validated 0..100 percent and integer paise",
            )
        )
        run = engine.run(created["id"])
        events = engine.store.history(run["id"])
        usage = [e["payload"] for e in events if e["kind"] == "model_usage"]
        passed = run["state"] == expected
        if fault == "test":
            passed &= run["repairs"] == 1 and any(c["exit_code"] != 0 for c in run["checks"])
        if fault == "scope":
            passed &= not engine.repo.diff(run["workspace"])
        results.append(
            {
                "task": fault,
                "id": run["id"],
                "expected": expected,
                "actual": run["state"],
                "passed": passed,
                "repairs": run["repairs"],
                "rubric": run.get("rubric"),
                "policy_violations": sum(e["kind"] == "policy_violation" for e in events),
                "model_calls": len(usage),
                "model_usage": usage,
                "tool_duration_ms": sum(c["duration_ms"] for c in run["checks"] + run["baseline"]),
                "check_evidence": run["checks"],
                "baseline": run["baseline"],
                "error": run["error"],
            }
        )
        print(f"{fault}: {run['state']} {'PASS' if passed else 'FAIL'}", flush=True)
    output = Path(f"evaluation/fixtures-{batch}.json")
    output.write_text(json.dumps({"mode": "fixture plans; real Docker checks", "results": results}, indent=2))
    print(f"Evidence: {output}", flush=True)
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
