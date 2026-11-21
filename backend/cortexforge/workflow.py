import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from cortexforge.contracts import Design, Implementation, Resolution, Specification
from cortexforge.execution import DockerExecutor, ExecutionBlocked
from cortexforge.providers import BASE, DemoProvider, GroqProvider, ProviderMalformed, ProviderUnavailable
from cortexforge.repository import PolicyViolation, Repository, digest
from cortexforge.store import Store, now

TERMINAL = {
    "APPROVED",
    "REJECTED",
    "BLOCKED",
    "FAILED",
    "AWAITING_HUMAN_APPROVAL",
    "AWAITING_CLARIFICATION",
    "CANCELLED",
}


class CancellationRequested(RuntimeError):
    pass


TRANSITIONS = {
    "CREATED": {"REQUIREMENT_ANALYSIS"},
    "REQUIREMENT_ANALYSIS": {"ARCHITECTURE_PLANNING", "AWAITING_CLARIFICATION"},
    "AWAITING_CLARIFICATION": {"REQUIREMENT_ANALYSIS"},
    "ARCHITECTURE_PLANNING": {"BASELINE"},
    "BASELINE": {"IMPLEMENTING"},
    "IMPLEMENTING": {"TESTING"},
    "REPAIRING": {"TESTING"},
    "TESTING": {"REPAIRING", "SECURITY_REVIEW"},
    "SECURITY_REVIEW": {"RELEASE_REVIEW"},
    "RELEASE_REVIEW": {"AWAITING_HUMAN_APPROVAL"},
    "AWAITING_HUMAN_APPROVAL": {"APPROVED", "REJECTED"},
}
AGENTS = {
    "analyst": {
        "input": "requirement, repository metadata",
        "output": "Specification",
        "responsibility": "Clarify acceptance and tasks",
    },
    "architect": {
        "input": "specification, source, dependencies",
        "output": "Design",
        "responsibility": "Select minimal scope and validation",
    },
    "developer": {
        "input": "design, source, check failures",
        "output": "Implementation",
        "responsibility": "Propose scoped file changes and repair",
    },
    "qa": {
        "input": "isolated source",
        "output": "tool records",
        "responsibility": "Execute unit and lint checks",
    },
    "security": {
        "input": "isolated source and diff",
        "output": "verified scan",
        "responsibility": "Run Bandit and enforce scope",
    },
    "release": {
        "input": "diff, verified checks, risks",
        "output": "review evidence",
        "responsibility": "Assemble report; cannot approve",
    },
}


class GraphState(TypedDict):
    run_id: str


class Engine:
    def __init__(self, data=None, executor=None, provider=None):
        self.data = Path(data or ".cortexforge").resolve()
        self.data.mkdir(parents=True, exist_ok=True)
        self.store = Store(os.getenv("DATABASE_URL") or f"sqlite:///{self.data / 'state.db'}")
        self.repo = Repository(self.data / "runs")
        self.executor = executor or DockerExecutor()
        self.provider = provider
        self.limit = int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
        if not 0 <= self.limit <= 5:
            raise ValueError("MAX_REPAIR_ATTEMPTS must be between 0 and 5")
        self.checkpoint_connection = sqlite3.connect(self.data / "checkpoints.db", check_same_thread=False)
        graph = StateGraph(GraphState)
        graph.add_node("advance", self._node)
        graph.add_edge(START, "advance")
        graph.add_conditional_edges("advance", self._route, {"next": "advance", "end": END})
        self.graph = graph.compile(checkpointer=SqliteSaver(self.checkpoint_connection))
        self.recover_interrupted()

    def recover_interrupted(self):
        from cortexforge.locking import run_lock

        for run in self.store.list():
            if run["state"] in TERMINAL or not (run.get("worker_active") or run.get("pending")):
                continue
            try:
                with run_lock(self.data / f"{run['id']}.lock"):
                    run = self.store.get(run["id"])
                    if run["state"] in TERMINAL or not (run.get("worker_active") or run.get("pending")):
                        continue
                    run["resume_state"] = run["state"]
                    run["error"] = "Process interrupted; inspect pending operation and explicitly resume"
                    run["worker_active"] = False
                    self._transition(run, "BLOCKED")
                    self.store.event(run["id"], "restart_recovery", {"pending": run["pending"]})
            except PolicyViolation:
                # Another live process still owns the operation; do not interfere.
                continue

    def create(self, request):
        run_id = uuid.uuid4().hex
        if request.mode == "live" and request.fault != "none":
            raise PolicyViolation("Controlled fault injection is available only in labelled demo mode")
        isolated = self.repo.isolate(request.repository, run_id)
        inspection = self.repo.inspect(isolated["workspace"])
        if request.mode == "demo" and (
            inspection["files"].get("payments.py", "").strip() != BASE.strip()
            or "apply_discount" not in request.requirement
        ):
            raise PolicyViolation("Demo fixtures support only the bundled apply_discount requirement")
        run = {
            "id": run_id,
            **request.model_dump(),
            **isolated,
            "state": "CREATED",
            "created": now(),
            "repairs": 0,
            "disagreements": 0,
            "resumes": 0,
            "actions": [],
            "pending": None,
            "checks": [],
            "baseline": [],
            "inspection": inspection,
            "error": None,
            "decision": None,
        }
        if (
            request.acceptance_profile == "payments_discount"
            and inspection["files"].get("payments.py", "").strip() != BASE.strip()
        ):
            raise PolicyViolation("Payments acceptance profile requires the unchanged payments sample")
        if request.acceptance_profile == "refunds" and not {"api.py", "service.py", "ledger.py"}.issubset(
            inspection["files"]
        ):
            raise PolicyViolation("Refunds profile requires the documented refund service interface")
        run["acceptance_oracle"] = request.mode == "demo" or request.acceptance_profile != "none"
        self.store.create(run)
        self.store.event(run_id, "created", {"mode": request.mode, "branch": run["branch"]})
        return run

    def _transition(self, run, state):
        previous = run["state"]
        if state not in {"FAILED", "BLOCKED", "CANCELLED"} and state not in TRANSITIONS.get(previous, set()):
            if previous != "BLOCKED" or state != run.get("resume_state"):
                raise PolicyViolation(f"Illegal transition: {previous} -> {state}")
        run["state"] = state
        self.store.save(run)
        self.store.event(run["id"], "transition", {"from": previous, "to": state})

    def _call(self, run, agent, schema, extra=None):
        repository = self.repo.inspect(run["workspace"])
        latest = {check["operation"]: check for check in run["checks"]}
        feedback = []
        for check in latest.values():
            failure_lines = [
                line
                for line in check["output"].splitlines()
                if line.startswith(("E ", "FAILED ", "ERROR ", "> "))
            ]
            feedback.append(
                {
                    "operation": check["operation"],
                    "exit_code": check["exit_code"],
                    "iteration": check.get("iteration"),
                    "test_counts": check.get("test_counts"),
                    "output": check["output"][-2500:] if check["exit_code"] else "Passed",
                    "output_is_tail": bool(check["exit_code"] and len(check["output"]) > 2500),
                    "failure_excerpt": "\n".join(failure_lines)[:1600],
                }
            )
        if agent in {"developer", "resolver"}:
            # Keep source/interfaces and scoped tests, omit repeated prose. Full raw
            # check evidence remains in storage/UI, separate from bounded model feedback.
            repository["files"] = {
                name: content for name, content in repository["files"].items() if name.endswith(".py")
            }
        context = {
            "requirement": run["requirement"],
            "repository": repository,
            "specification": run.get("specification"),
            "design": run.get("design"),
            "checks": feedback,
            "repairs": run["repairs"],
            "fault": run["fault"],
            **(extra or {}),
        }
        context["resolution"] = run.get("resolution")
        if agent in {"developer", "resolver"} and run.get("specification"):
            context["specification"] = {
                key: run["specification"][key] for key in ("acceptance", "constraints")
            }
            context["design"] = {key: run["design"][key] for key in ("files", "risks", "validation")}
            if run["repairs"]:
                # Repair keeps the original requirement and scoped source. Avoid
                # repeating paraphrased planning prose in a constrained provider window.
                context["specification"] = {"constraints": run["specification"]["constraints"]}
                context["design"] = {"files": run["design"]["files"]}
                for check in feedback:
                    if len(check["output"]) > 1200:
                        check["output"] = check["output"][-1200:]
                        check["output_is_tail"] = True
        provider = self.provider or (DemoProvider() if run["mode"] == "demo" else GroqProvider())
        if agent == "resolver":
            # Resolution returns a complete Design; retaining it must not lose
            # required rationale/validation fields through prompt compaction.
            context["design"] = run.get("design")
        for attempt in range(2):
            started = time.monotonic()
            self.store.event(run["id"], "agent_input", {"agent": agent, "attempt": attempt, "input": context})
            try:
                response = provider.generate(agent, context, schema.model_json_schema())
                self.store.event(
                    run["id"], "model_usage", {"agent": agent, "attempt": attempt + 1, **response.usage}
                )
            except ProviderUnavailable as exc:
                self.store.event(
                    run["id"],
                    "model_usage",
                    {
                        "agent": agent,
                        "provider": "fixture" if run["mode"] == "demo" else os.getenv("LLM_PROVIDER", "groq"),
                        "model": "seeded-demo-v1"
                        if run["mode"] == "demo"
                        else (os.getenv("MODEL_" + agent.upper()) or os.getenv("LLM_MODEL")),
                        "attempt": attempt + 1,
                        "status": "failed",
                        "latency_ms": round((time.monotonic() - started) * 1000),
                        "cost_usd": None,
                        "cost_status": "unknown",
                        "input_tokens": None,
                        "output_tokens": None,
                    },
                )
                if isinstance(exc, ProviderMalformed):
                    errors = [{"type": "provider_json_validation_failed"}]
                    self.store.event(run["id"], "validation_error", {"agent": agent, "errors": errors})
                    context["validation_errors"] = errors
                    continue
                raise exc
            if response.usage.get("finish_reason") not in (None, "stop"):
                errors = [{"type": "incomplete_response", "finish_reason": response.usage["finish_reason"]}]
                self.store.event(run["id"], "validation_error", {"agent": agent, "errors": errors})
                context["validation_errors"] = errors
                continue
            try:
                output = schema.model_validate_json(response.text)
                self.store.event(run["id"], "agent_output", {"agent": agent, "output": output.model_dump()})
                return output
            except ValidationError as exc:
                errors = [{"loc": list(e["loc"]), "type": e["type"]} for e in exc.errors()]
                self.store.event(run["id"], "validation_error", {"agent": agent, "errors": errors})
                context["validation_errors"] = errors
        raise PolicyViolation("Malformed structured output after two attempts")

    def _check(self, run, operation, baseline=False):
        self._ensure_not_cancelled(run)
        before_hash = self.repo.fingerprint(run["workspace"])
        # A completed, persisted read-only result is reusable after interruption,
        # but only for the identical content, operation and repair iteration.
        for previous in reversed(run["baseline" if baseline else "checks"]):
            if (
                previous["operation"] == operation
                and previous.get("tree_hash") == before_hash
                and previous.get("iteration") == run["repairs"]
            ):
                self.store.event(
                    run["id"],
                    "check_reused",
                    {
                        "operation": operation,
                        "tree_hash": before_hash,
                        "iteration": run["repairs"],
                    },
                )
                return previous
        run["pending"] = {"kind": "check", "operation": operation}
        self.store.save(run)
        if operation == "acceptance" and run.get("acceptance_profile") == "refunds":
            result = self.executor.run(run["workspace"], operation, profile="refunds")
        else:
            result = self.executor.run(run["workspace"], operation)
        if self.repo.fingerprint(run["workspace"]) != before_hash:
            raise PolicyViolation("Workspace changed during check; evidence invalid")
        result["tree_hash"] = before_hash
        result["phase"] = "baseline" if baseline else "candidate"
        result["iteration"] = run["repairs"]
        self.store.event(
            run["id"], "tool_execution", {"agent": "security" if operation == "security" else "qa", **result}
        )
        run["baseline" if baseline else "checks"].append(result)
        run["pending"] = None
        self.store.save(run)
        return result

    def advance(self, run_id):
        run = self.store.get(run_id)
        if self.store.cancellation_requested(run_id) and run["state"] not in {
            "APPROVED",
            "REJECTED",
            "FAILED",
            "CANCELLED",
        }:
            run["error"] = "Cancelled by human request; isolated artifacts retained for inspection"
            self._transition(run, "CANCELLED")
            return run
        if run["state"] in TERMINAL:
            return run
        if run["pending"]:
            run["resume_state"] = run["state"]
            run["error"] = "Interrupted operation; explicit resume required"
            self._transition(run, "BLOCKED")
            return run
        try:
            state = run["state"]
            if state == "CREATED":
                self._transition(run, "REQUIREMENT_ANALYSIS")
            elif state == "REQUIREMENT_ANALYSIS":
                specification = self._call(run, "analyst", Specification)
                run["specification"] = specification.model_dump()
                self._transition(
                    run, "AWAITING_CLARIFICATION" if specification.questions else "ARCHITECTURE_PLANNING"
                )
            elif state == "ARCHITECTURE_PLANNING":
                design = self._call(run, "architect", Design)
                self.repo.validate_scope(run["workspace"], design.files)
                run["design"] = design.model_dump()
                self._transition(run, "BASELINE")
            elif state == "BASELINE":
                done = {c["operation"] for c in run["baseline"]}
                operations = ["unit", "lint", "security"] + (
                    ["acceptance"] if run["acceptance_oracle"] else []
                )
                for operation in operations:
                    if operation not in done:
                        self._check(run, operation, baseline=True)
                if any(c["exit_code"] != 0 for c in run["baseline"] if c["operation"] != "acceptance"):
                    raise PolicyViolation("Baseline repository checks failed; provide a clean baseline")
                self._transition(run, "IMPLEMENTING")
            elif state in ("IMPLEMENTING", "REPAIRING"):
                proposal = self._call(run, "developer", Implementation)
                if not proposal.agrees_with_design:
                    run["disagreements"] += 1
                    self.store.event(
                        run_id,
                        "disagreement",
                        {"reason": proposal.disagreement, "round": run["disagreements"]},
                    )
                    if run["disagreements"] > 2:
                        raise PolicyViolation(
                            "Architect–Developer disagreement exhausted; human escalation required"
                        )
                    resolution = self._call(
                        run, "resolver", Resolution, {"developer_objection": proposal.disagreement}
                    )
                    run["resolution"] = resolution.model_dump()
                    if resolution.decision == "escalate":
                        raise PolicyViolation("Architect escalated disagreement to human")
                    if set(resolution.design.files) - set(run["design"]["files"]):
                        raise PolicyViolation("Disagreement resolution cannot expand authorized scope")
                    if resolution.decision == "revise":
                        run["design"] = resolution.design.model_dump()
                    self.store.save(run)
                    return run
                if not proposal.changes:
                    raise PolicyViolation("Developer returned no code changes")
                action = digest(json.dumps([c.model_dump() for c in proposal.changes], sort_keys=True))
                if action in run["actions"]:
                    raise PolicyViolation("Repeated action detected; stopped before reapplying")
                self._ensure_not_cancelled(run)
                run["pending"] = {"kind": "patch", "hash": action}
                self.store.save(run)
                run["diff"] = self.repo.apply(run["workspace"], proposal.changes, run["design"]["files"])
                run["actions"].append(action)
                run["pending"] = None
                run["summary"] = proposal.summary
                self.store.event(
                    run_id, "patch_applied", {"hash": action, "files": [c.path for c in proposal.changes]}
                )
                self._transition(run, "TESTING")
            elif state == "TESTING":
                operations = ["unit", "lint"] + (["acceptance"] if run["acceptance_oracle"] else [])
                results = [self._check(run, op) for op in operations]
                if any(r["exit_code"] for r in results):
                    if run["repairs"] >= self.limit:
                        raise PolicyViolation("Repair budget exhausted")
                    run["repairs"] += 1
                    self._transition(run, "REPAIRING")
                else:
                    self._transition(run, "SECURITY_REVIEW")
            elif state == "SECURITY_REVIEW":
                result = self._check(run, "security")
                if result["exit_code"]:
                    raise PolicyViolation(
                        "Security gate failed; human correction required, approval prohibited"
                    )
                self._transition(run, "RELEASE_REVIEW")
            elif state == "RELEASE_REVIEW":
                changed = self.repo.changed_files(run["workspace"])
                if changed - set(run["design"]["files"]):
                    raise PolicyViolation("Unrelated workspace modifications invalidate release")
                existing = set(run["inspection"]["tracked"])
                sources = {
                    name
                    for name in changed
                    if name in existing and name.endswith(".py") and not name.startswith("tests/")
                }
                if not self.repo.source_changed(run["workspace"], sources):
                    raise PolicyViolation("A nonempty existing source code change is required for release")
                run["diff"] = self.repo.diff(run["workspace"])
                run["tree_hash"] = self.repo.fingerprint(run["workspace"])
                latest = {r["operation"]: r for r in run["checks"]}
                required = {"unit", "lint", "security"} | (
                    {"acceptance"} if run["acceptance_oracle"] else set()
                )
                if set(latest) != required or any(r["exit_code"] for r in latest.values()):
                    raise PolicyViolation("Missing or failing release evidence")
                if any(c["tree_hash"] != run["tree_hash"] for c in latest.values()):
                    raise PolicyViolation("Checks do not match current source content")
                run["rubric"] = {
                    "baseline_passed": sum(c["exit_code"] == 0 for c in run["baseline"]),
                    "candidate_passed": sum(c["exit_code"] == 0 for c in latest.values()),
                    "repair_attempts": run["repairs"],
                    "scoped_change": bool(run["diff"]),
                    "unexpected_files_modified": len(
                        self.repo.changed_files(run["workspace"]) - set(run["design"]["files"])
                    ),
                    "tests": latest["unit"].get("test_counts"),
                    "trusted_acceptance_tests": latest.get("acceptance", {}).get("test_counts"),
                    "acceptance": "Test-backed proxy; human must confirm semantic completeness",
                }
                run["risks"] = run["design"]["risks"] + [
                    "No deployment performed",
                    "Tests cannot prove all acceptance criteria",
                ]
                run["evidence_hash"] = digest(
                    json.dumps(
                        {
                            "tree": run["tree_hash"],
                            "checks": run["checks"],
                            "diff": run["diff"],
                            "risks": run["risks"],
                        },
                        sort_keys=True,
                    )
                )
                self.store.event(
                    run_id,
                    "release_report",
                    {
                        "agent": "release",
                        "rubric": run["rubric"],
                        "risks": run["risks"],
                        "evidence_hash": run["evidence_hash"],
                    },
                )
                self._transition(run, "AWAITING_HUMAN_APPROVAL")
            else:
                raise PolicyViolation(f"Unsupported state: {state}")
        except CancellationRequested:
            run["error"] = "Cancelled by human request; isolated artifacts retained for inspection"
            self._transition(run, "CANCELLED")
        except (ProviderUnavailable, ExecutionBlocked) as exc:
            run["resume_state"] = run["state"]
            run["error"] = str(exc)
            # Checks are read-only and may be retried explicitly.
            if run["pending"] and run["pending"]["kind"] == "check":
                run["pending"] = None
            self.store.event(run_id, "blocked", {"error": str(exc)})
            self._transition(run, "BLOCKED")
        except PolicyViolation as exc:
            run["error"] = str(exc)
            self.store.event(run_id, "policy_violation", {"error": str(exc)})
            self._transition(run, "FAILED")
        return run

    def _node(self, state):
        self.advance(state["run_id"])
        return state

    def _route(self, state):
        return "end" if self.store.get(state["run_id"])["state"] in TERMINAL else "next"

    def run(self, run_id):
        # OS lock is automatically released on process death. Prevents duplicate side effects.
        from cortexforge.locking import run_lock

        with run_lock(self.data / f"{run_id}.lock"):
            run = self.store.get(run_id)
            run["worker_active"] = True
            self.store.save(run)
            try:
                self.graph.invoke(
                    {"run_id": run_id}, {"configurable": {"thread_id": run_id}, "recursion_limit": 60}
                )
            except Exception as exc:
                run = self.store.get(run_id)
                run["resume_state"] = run["state"]
                run["error"] = f"Unexpected {type(exc).__name__}; inspect evidence before retry"
                self.store.event(run_id, "execution_error", {"type": type(exc).__name__})
                self._transition(run, "BLOCKED")
                raise
            finally:
                run = self.store.get(run_id)
                run["worker_active"] = False
                self.store.save(run)
        return self.store.get(run_id)

    def _ensure_not_cancelled(self, run):
        if self.store.cancellation_requested(run["id"]):
            raise CancellationRequested()

    def cancel(self, run_id):
        """Durable cooperative cancellation; in-flight calls retain their deadlines."""
        from cortexforge.locking import run_lock

        run = self.store.get(run_id)
        if run["state"] in {"APPROVED", "REJECTED", "FAILED", "CANCELLED"}:
            raise PolicyViolation("Completed runs cannot be cancelled")
        if not self.store.cancellation_requested(run_id):
            self.store.event(run_id, "cancellation_requested", {"authority": "human_token"})
        try:
            with run_lock(self.data / f"{run_id}.lock"):
                return self.advance(run_id)
        except PolicyViolation as exc:
            if str(exc) != "Run already executing":
                raise
        return self.store.get(run_id)

    def resume(self, run_id, clear_demo_fault=False):
        run = self.store.get(run_id)
        if run["state"] != "BLOCKED" or run["resumes"] >= 3:
            raise PolicyViolation("Run is not resumable or resume budget exhausted")
        if run["pending"] and run["pending"]["kind"] == "patch":
            raise PolicyViolation(
                "Interrupted patch requires human inspection; create a fresh run to avoid duplicate writes"
            )
        if clear_demo_fault:
            if run["mode"] != "demo" or run["fault"] != "provider":
                raise PolicyViolation("Only an injected demo provider outage can be cleared")
            run["fault"] = "none"
            self.store.event(run_id, "fault_cleared", {"fault": "provider", "authority": "human_request"})
        run["pending"] = None
        run["resumes"] += 1
        run["error"] = None
        self._transition(run, run["resume_state"])
        return run

    def clarify(self, run_id, answer):
        run = self.store.get(run_id)
        if run["state"] != "AWAITING_CLARIFICATION":
            raise PolicyViolation("Run is not awaiting clarification")
        run["requirement"] += "\nHuman clarification: " + answer
        self._transition(run, "REQUIREMENT_ANALYSIS")
        return run

    def review(self, run_id, review):
        run = self.store.get(run_id)
        if self.store.cancellation_requested(run_id):
            raise PolicyViolation("Cancellation requested; approval prohibited")
        if run["state"] != "AWAITING_HUMAN_APPROVAL":
            raise PolicyViolation("Run is not ready for approval")
        if (
            review.evidence_hash != run["evidence_hash"]
            or self.repo.fingerprint(run["workspace"]) != run["tree_hash"]
        ):
            raise PolicyViolation("Evidence changed; approval rejected")
        run["decision"] = {**review.model_dump(), "time": now(), "authority": "human_token"}
        self.store.event(run_id, "human_decision", run["decision"])
        self._transition(run, "APPROVED" if review.decision == "approve" else "REJECTED")
        return run
