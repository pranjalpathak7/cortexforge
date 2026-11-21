# Interview walkthrough

## Introduction (30 seconds)

“CortexForge takes a requirement and a clean local Python Git repository,
generates typed plans and code, executes isolated checks, repairs within a
budget, and requests a human decision on the exact verified patch. Analyst,
Architect and Developer use Groq. QA, Security and Release enforce deterministic
checks. The system never merges or deploys.”

## Prepare

Follow README setup, start Docker and both servers. Keep `.env` and credentials
off screen. Connect the UI using the local REVIEW_TOKEN. Run
`python scripts/init_sample.py` and copy the printed repository path.

## Reliable five-minute demonstration

1. **Create run:** choose fixture demo and the payments sample. Submit:
   `Add apply_discount with validated 0..100 percent and integer paise`.
   Choose the `test` fault. Explain that plans and incorrect code are controlled
   fixtures, while Git changes and Docker checks are real.
2. **Workflow:** show analyst criteria, architect scope, baseline and the first
   failed unit check. Expand the actual transition and tool events.
3. **Quality & security:** show failed iteration 0 and repaired iteration 1,
   exit codes, stdout, durations and the 12 immutable acceptance cases. Baseline
   acceptance fails because the original repository lacks the function.
4. **Agents:** show Developer input containing failure feedback, then its new
   proposal. Explain repair, malformed-output and disagreement budgets.
5. **Code review:** inspect `payments.py` and new tests. Existing tests and the
   original supplied repository remain unchanged.
6. **Human review:** inspect risks, rubric, source and evidence SHA-256 values.
   Enter your own reviewer name and rationale, then approve or reject yourself.
   Approval permits patch export only; it never deploys. A rejection stays final.
7. Submit another fixture run with `security`. Show the real Bandit B307 finding
   and FAILED state. Explain the explicitly separate local “critical” policy.

## Live demonstrations

Use `python evaluation/live.py --pace-seconds 62` for the discount case.
The CLI prints the run ID and a unique JSON evidence path. Open that run in the
UI. Historical successful runs are evidence, not a pretend live performance.

For the larger scenario, run:

```powershell
python scripts/init_sample.py --sample refund-service
python evaluation/live.py --scenario refunds --pace-seconds 62
```

The requirement is in `sample-repos/refund-service/README.md`. It requires an
idempotent refund endpoint across API, service and ledger layers. The trusted
20-case HTTP oracle checks replay, conflicts, strict validation, business limits
and concurrent duplicates. Live runs can require clarification, fail, or hit
provider limits. Show the actual state; do not describe a blocked run as passing.
Use `--resume RUN_ID` only for a resumable BLOCKED run; budgets remain enforced.

## Architecture questions to prepare

- **Why LangGraph plus SQLAlchemy?** The graph checkpoints orchestration; the
  application database owns durable run documents and pending side-effect
  markers. Neither makes filesystem writes transactional.
- **Exactly once?** No. Patches with uncertain completion stop for inspection.
  Completed checks are reused only with matching source hashes and iteration.
  Provider billing cannot be deduplicated after an uncertain network failure.
- **How do you constrain model authority?** Typed proposals, canonical paths,
  immutable existing tests, explicit scope, fixed Docker commands, release
  evidence hashes, and a separate human token gate.
- **Prompt injection?** Repository text is untrusted input. Prompt instructions
  are not a security guarantee; deterministic controls bound the consequences.
- **Are all agents LLMs?** No. Running tests and enforcing policies benefit from
  deterministic execution. Optional AI summaries were not added because they
  would increase cost without strengthening the authoritative evidence.
- **What does the baseline prove?** Before/after functional improvement under
  identical independent checks, not superiority over a single-agent benchmark.
- **Production limitations?** Local single-user trust, curated dependencies,
  SQLite, in-memory sample ledger, incomplete scanners, no automatic deployment.
- **Cancellation?** Durable cooperative request. An in-flight call/check finishes
  or reaches its timeout; the next boundary stops work and preserves artifacts.

Keep `FINAL_AUDIT.md`, `traceability.md` and `SUBMISSION_READINESS.md` available
for evidence and honest limitations.
