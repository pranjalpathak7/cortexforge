"""Opt-in live evaluation; actual calls/checks, immutable oracles, no self-approval."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from cortexforge.contracts import CreateRun  # noqa: E402
from cortexforge.providers import GroqProvider  # noqa: E402
from cortexforge.workflow import Engine  # noqa: E402
from init_sample import prepare  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["discount", "refunds"], default="discount")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume", help="Explicitly resume a blocked live run within its persisted budget")
    parser.add_argument(
        "--pace-seconds",
        type=float,
        default=0,
        help="Space live requests for limited free-tier quotas; no hidden retries",
    )
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    if not os.getenv("GROQ_API_KEY") or not os.getenv("LLM_MODEL"):
        print("BLOCKED: configure GROQ_API_KEY and LLM_MODEL locally; credentials are never printed")
        return 2
    engine = Engine()
    if args.pace_seconds:
        if not 0 <= args.pace_seconds <= 120:
            raise ValueError("Pacing must be between 0 and 120 seconds")

        class PacedProvider(GroqProvider):
            last_call = 0.0

            def generate(self, agent, context, schema):
                remaining = args.pace_seconds - (time.monotonic() - self.last_call)
                if remaining > 0:
                    print(f"Quota pacing before {agent}: {remaining:.0f}s", flush=True)
                    time.sleep(remaining)
                self.last_call = time.monotonic()
                return super().generate(agent, context, schema)

        engine.provider = PacedProvider()
    if not engine.executor.available():
        print("BLOCKED: Docker engine or sandbox image unavailable")
        return 2
    repository = prepare(".cortexforge/sample")
    requirement = (
        "Add apply_discount(amount: int, percent: int) -> int to payments.py. "
        "Amounts are integer paise. Allow percentage 0 through 100 inclusive. "
        "Reject negative amounts and out-of-range percentages with ValueError. "
        "Return amount * (100 - percent) // 100, rounding down to whole paise. "
        "Preserve existing total() behavior and add boundary and invalid-input tests "
        "in a new tests/test_discount.py file. Existing regression tests must remain unchanged."
    )
    if args.scenario == "refunds":
        repository = prepare(".cortexforge/refund-service", "refund-service")
        requirement = (repository / "README.md").read_text(encoding="utf-8")
        # A multi-file implementation needs more output than the small discount task.
        os.environ["LLM_MAX_OUTPUT_TOKENS"] = "3072"
    if args.resume:
        existing = engine.store.get(args.resume)
        profile = "refunds" if args.scenario == "refunds" else "payments_discount"
        if existing["mode"] != "live" or existing.get("acceptance_profile") != profile:
            raise ValueError("Resume target must match the selected live scenario")
        created = engine.resume(args.resume)
    else:
        created = engine.create(
            CreateRun(
                repository=str(repository),
                mode="live",
                requirement=requirement,
                acceptance_profile="refunds" if args.scenario == "refunds" else "payments_discount",
            )
        )
    print(f"Live run created: {created['id']}", flush=True)
    run = engine.run(created["id"])
    oracle = next((c for c in reversed(run["checks"]) if c["operation"] == "acceptance"), None)
    events = engine.store.history(run["id"])
    passed = run["state"] == "AWAITING_HUMAN_APPROVAL" and oracle is not None and oracle["exit_code"] == 0
    result = {
        "mode": "live Groq; real Docker checks",
        "run_id": run["id"],
        "state": run["state"],
        "passed": passed,
        "error": run["error"],
        "scenario": args.scenario,
        "created": run["created"],
        "requirement": run["requirement"],
        "base": run["base"],
        "evidence_hash": run.get("evidence_hash"),
        "tree_hash": run.get("tree_hash"),
        "diff": run.get("diff"),
        "baseline": run["baseline"],
        "repairs": run["repairs"],
        "attempted_changes": len(run["actions"]),
        "changed_files": sorted(engine.repo.changed_files(run["workspace"])),
        "agent_outputs": [e["payload"] for e in events if e["kind"] == "agent_output"],
        "rubric": run.get("rubric"),
        "model_usage": [e["payload"] for e in events if e["kind"] == "model_usage"],
        "independent_acceptance": oracle,
        "checks": run["checks"],
        "human_decision": "Not supplied; evaluation never approves itself",
    }
    output = args.output or Path(f"evaluation/live-{args.scenario}-{run['id']}-resume{run['resumes']}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Evidence: {output}", flush=True)
    print(json.dumps({"state": run["state"], "passed": passed, "error": run["error"]}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
