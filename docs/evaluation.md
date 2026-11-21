# Evaluation

Run `python evaluation/run.py` after preparing the sandbox image. Eight labelled
fixture cases use actual Git worktrees and Docker pytest/Ruff/Bandit operations:
feature success (A), failing test then repair (B), security/scope rejection (C),
malformed output, provider outage, repeated action and architect disagreement.
Results go to `evaluation/results.json`, including exact tool output, exit codes,
durations, model usage, repair counts, policy violations and review status.
The harness stops at the human checkpoint; it never fabricates human approval.

Baseline: execute the same three checks against unchanged committed source.
Candidate: execute checks after modification and compare deterministic outcomes.
For the bundled demonstration, an additional immutable acceptance oracle is
injected into the sandbox snapshot (never the worktree). Its 12 parameterized
cases independently check rounding, boundaries, invalid inputs and total()
regression. It fails against the baseline's missing feature and must pass against
the candidate, independently of any developer-authored tests.
This is a before/after rubric, not a benchmark proving multi-agent superiority
over a single-agent model. Semantic acceptance remains a human review item;
passing agent-authored tests alone cannot prove arbitrary requirements.

Backend contract tests deliberately use a labelled ContractExecutor to validate
orchestration cheaply. These are not reported as real sandbox evidence. The
Docker integration test and evaluation harness exercise real checks. Subprocess
tests validate persistence after actual interpreter exits and restart.

Live verification: configure `.env` locally, then run `python evaluation/live.py`.
This makes actual Groq calls for the same controlled sample and enables the
trusted `payments_discount` acceptance profile inside the release gate. It writes
`evaluation/live-results.json`, preserves per-agent provider usage, and stops at
human review. Without a key/model it reports BLOCKED; no fixture fallback exists.
No credentials are included in the report. Automated tests isolate their database
configuration and credentials from the user's `.env`.


Audit extension: `live.py --scenario refunds --pace-seconds 62` exercises the
multi-file FastAPI sample with a 20-case independent oracle. Unique report names
preserve attempts; use `--output` only when intentionally choosing a destination.
Fixture batches now have isolated runtime databases. Raw tool output remains
complete up to the documented output cap; model feedback is a bounded excerpt.
A successful old 18-case result was superseded after manual review found missing
stored-status coverage; see FINAL_AUDIT.md. Historical results are not silently
upgraded to the stronger oracle.
