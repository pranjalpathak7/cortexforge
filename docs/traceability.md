# Pine Labs requirements traceability

Scope: [independent project description](PROJECT_SCOPE.md). This capability-to-evidence map uses independently written summaries, not quotations from the company brief. Historical IDs and verification records are retained.

Verification date: **2026-11-21 (Asia/Calcutta)**. **70 backend tests passed, zero failures/skips**, including actual Docker and process restarts. All eight controlled fixture evaluations passed. Five frontend tests and the production build passed.

Live Groq verification also passed using `openai/gpt-oss-120b`: fresh analyst, architect and developer outputs, actual code modification, 8 unit tests and 12 independent acceptance tests. Evidence: `evaluation/live-results.json`. Three model calls reported 3,628 total tokens; costs remain explicitly unknown without configured pricing. Human decisions verified through the API: reviewer-1 approved the live run and clean fixture run and rejected the repaired fixture run. Approved patch exports returned HTTP 200.

| ID | Capability summary | Proposed implementation | Source files | Automated verification | Demonstration | Status |
|---|---|---|---|---|---|---|
| PS-01 | Request intake | POST typed requirement and local Git path; persist run | `backend/cortexforge/api.py`, `backend/cortexforge/contracts.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_api_create_run; passed (backend JUnit) | Create Run: submit sample path and requirement. | Tested |
| PS-02 | Planning with explicit outcomes and work items | Typed analyst criteria/tasks and explicit clarification pause | `backend/cortexforge/contracts.py`, `backend/cortexforge/workflow.py`, `backend/cortexforge/providers.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_clarification; passed (backend JUnit); fresh live generation verified in evaluation/live-results.json | Inspect Analyst inputs/outputs; run pytest -k clarification. | Tested |
| PS-03 | Design proposals grounded in repository inspection | Inspect tracked source/dependencies and validate proposed design scope | `backend/cortexforge/repository.py`, `backend/cortexforge/providers.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_vertical_slice_repair_review_and_source_preserved; passed (backend JUnit); fresh live generation verified in evaluation/live-results.json | Inspect Architect design.files and rationale in Agents. | Tested |
| PS-04 | Scoped implementation in a sample workspace | Apply validated full-file changes inside private branch/worktree | `backend/cortexforge/repository.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_vertical_slice_repair_review_and_source_preserved; passed (backend JUnit) | Inspect Code review and the isolated branch; compare source Git status. | Tested |
| PS-05 | Executable quality and security feedback | Docker pytest/Ruff/Bandit with captured exit codes/output | `backend/cortexforge/execution.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_real_docker_repair_and_security; passed (backend JUnit) | Open Quality & security and inspect captured command output. | Tested |
| PS-06 | Evidence package leading to a human checkpoint | Deterministic release report and hash-bound human checkpoint | `backend/cortexforge/workflow.py`, `backend/cortexforge/api.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_approval_auth_tamper_and_patch; passed (backend JUnit) | Open Human review; inspect risks and disabled approval until ready. | Tested |
| PS-07 | Import a user-selected repository with its change request | Typed requirement and clean supplied local Git repository import | `backend/cortexforge/api.py`, `backend/cortexforge/repository.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_api_create_run; passed (backend JUnit) | Create a run from the committed sample printed by init_sample.py. | Tested |
| PS-08 | Structured success criteria and implementation sequence | Pydantic Specification from live Groq or explicitly labelled fixtures | `backend/cortexforge/contracts.py`, `backend/cortexforge/providers.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_clarification; live Groq verification passed; passed (backend JUnit); fresh live generation verified in evaluation/live-results.json | Inspect Specification acceptance/tasks; configure Groq for fresh generation. | Tested |
| PS-09 | Locate affected files through source inspection | Tracked file inspection, dependency manifests, design file validation | `backend/cortexforge/repository.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_vertical_slice_repair_review_and_source_preserved; passed (backend JUnit) | Inspect agent_input repository files/dependencies and design.files. | Tested |
| PS-10 | Produce a meaningful source-code diff | Apply actual isolated file changes and expose Git diff including new tests | `backend/cortexforge/repository.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_real_docker_repair_and_security; passed (backend JUnit) | View payments.py and tests/test_discount.py in the actual Git diff. | Tested |
| PS-11 | Exercise behavior and static quality tooling | Real unit tests plus Ruff and Bandit in restricted Docker | `backend/cortexforge/execution.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_real_docker_repair_and_security; passed (backend JUnit) | Inspect unit/lint/security exit codes in Quality & security. | Tested |
| PS-12 | Present check outcomes alongside limitations | Assemble actual checks, baseline rubric, diff and explicit known risks | `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_vertical_slice_repair_review_and_source_preserved; passed (backend JUnit) | Read Human review summary, rubric, risks and exact tool evidence. | Tested |
| PS-13 | Reserve delivery decisions for a human reviewer | Token-authorized persisted decision; manual approved patch export; no merge/deploy API | `backend/cortexforge/api.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_approval_auth_tamper_and_patch; passed (backend JUnit) | Run approval/tamper tests; manually review before patch export. | Tested |
| PS-14 | Separate specialist contracts and ownership | Six logical specialists with typed or deterministic I/O contracts | `backend/cortexforge/contracts.py`, `backend/cortexforge/providers.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_vertical_slice_repair_review_and_source_preserved; passed (backend JUnit) | Open Agents; inspect all six responsibilities and event contracts. | Tested |
| PS-15 | Durable runs and an auditable event trail | SQLAlchemy run/event persistence and SQLite LangGraph checkpoints; real process restart tests | `backend/cortexforge/store.py`, `backend/cortexforge/workflow.py`, `backend/cortexforge/locking.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_process_restart_retains_state_and_checkpoint; test_actual_process_kill_during_patch; passed (backend JUnit) | Run pytest -k "process or restart"; inspect durable checkpoint/history. | Tested |
| PS-16 | Capped retries and explicit workflow transitions | Explicit transitions, schema retry, repair cap, disagreement cap and repeat hashes | `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_failure_scenarios; test_repair_exhaustion; passed (backend JUnit) | Select test/repeat/malformed faults; inspect bounded transitions. | Tested |
| PS-17 | Measured provider consumption and cost uncertainty | Provider-reported tokens, measured latency, configured-price estimates; unknowns remain null | `backend/cortexforge/providers.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_provider_usage_and_cost_are_measured (mock HTTP plus live Groq); live Groq verification passed; passed (backend JUnit) | Configure .env, run python evaluation/live.py, inspect model_usage. | Tested |
| PS-18 | Restricted execution, isolated Git changes and review authorization | Private clone plus real branch/worktree; restricted Docker; content-bound review token gate | `backend/cortexforge/repository.py`, `backend/cortexforge/execution.py`, `backend/cortexforge/api.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_execution_isolation_flags_and_timeout_cleanup; test_approval_auth_tamper_and_patch; Docker integration; passed (backend JUnit) | Inspect isolated worktree/branch; run Docker isolation and approval tests. | Tested |
| PS-19 | Before/after scoring with independent checks | Run identical checks before/after; deterministic check counts, repair counts and policy metrics | `backend/cortexforge/workflow.py`, `evaluation/run.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_vertical_slice_repair_review_and_source_preserved; evaluation/run.py; passed (backend JUnit) | Run python evaluation/run.py; compare baseline and 12-case trusted oracle. | Tested |
| PS-20 | Bounded handling of conflicting design decisions | Explicit agreement flag; two resolver rounds, no scope expansion; third objection escalates | `backend/cortexforge/contracts.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_failure_scenarios[disagree]; passed (backend JUnit) | Create demo fault disagree; observe two resolver rounds then escalation. | Tested |
| PS-21 | Recover from an implementation regression | Wrong-divisor fault causes actual pytest failure; return evidence to developer; bounded repair | `backend/cortexforge/providers.py`, `backend/cortexforge/workflow.py`, `backend/cortexforge/execution.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_real_docker_repair_and_security; test_repair_exhaustion; passed (backend JUnit) | Create demo fault test; inspect failure, repair and successful rerun. | Tested |
| PS-22 | Stop unsafe changes after security detection | Bandit detects eval; retain tool severity and classify executable injection critical under local policy; block review | `backend/cortexforge/providers.py`, `backend/cortexforge/execution.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_real_docker_repair_and_security; passed (backend JUnit) | Create demo fault security; inspect B307 and blocked approval. | Tested |
| PS-23 | Reject invalid agent response structures | Pydantic rejects unsupported fields; one correction attempt then fail safely | `backend/cortexforge/contracts.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_failure_scenarios[malformed]; passed (backend JUnit) | Create demo fault malformed; observe two validation failures and safe stop. | Tested |
| PS-24 | Pause safely when provider access fails | Persist provider error and resume state, unknown billing, controlled retry budget | `backend/cortexforge/providers.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_provider_outage_resume_and_usage; passed (backend JUnit) | Create demo fault provider; inspect BLOCKED, then Retry / resume clears injection. | Tested |
| PS-25 | Prevent duplicate actions and out-of-scope writes | Reject unrelated batch before writes; hash repeated action and stop before reapplication | `backend/cortexforge/repository.py`, `backend/cortexforge/workflow.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_failure_scenarios[scope]; test_failure_scenarios[repeat]; passed (backend JUnit) | Run separate scope and repeat demos; inspect pre-write policy rejection. | Tested |
| PS-27 | End-to-end evidence of planning, repair, review and human control | Fixture-backed plans with real Git/Docker failure and repair; human checkpoint and explicit review API | `backend/cortexforge/workflow.py`, `backend/cortexforge/api.py`, `evaluation/run.py` | `backend/tests/test_workflow.py`, `test_safety.py`: test_real_docker_repair_and_security; test_approval_auth_tamper_and_patch; passed (backend JUnit) | Create demo fault test; follow timeline through repair, security and human checkpoint. | Tested |

## Additional mandatory engineering and scope coverage

| ID | Requirement | Implementation | Source files | Automated tests | Demonstration | Status |
|---|---|---|---|---|---|---|
| E-01 | Workflow persistence across actual process restarts | Separate interpreter processes; kill a writer after durable pending marker; block uncertain replay | `workflow.py`, `store.py`, `locking.py` | `test_actual_process_kill_during_patch`, `test_process_restart_retains_state_and_checkpoint` (passed) | Run pytest; inspect checkpoint and pending marker | Tested |
| E-02 | Live AI mode is primary; no canned live behavior | Groq HTTP adapter, model per agent, Pydantic schemas; fixtures selectable only as demo | `providers.py`, `contracts.py` | Mock HTTP usage test and actual Groq calls passed | Configure key/model and run live task | Tested |
| E-03 | Explicit persisted human approval, never agent self-approval | Token gate, content/evidence hashes, audit action; no automatic merge/deploy | `api.py`, `workflow.py` | Approval/tamper tests passed | Human enters review rationale and approves in UI | Tested |
| E-04 | Reproducible evaluation tasks A, B, C | Eight controlled faults and feature scenario with captured evidence | `evaluation/run.py` | Eight scenarios passed; see evaluation/results.json | Run evaluation command | Tested |
| E-05 | Polished connected frontend with loading/error/empty states | React review console, create run, timeline, agent I/O, diff, checks, approvals, settings | `apps/web/src/main.tsx`, `style.css` | Five Vitest tests passed; production build passed; connected human-review screen and 390px responsive width checked | npm run dev; inspect each tab | Tested |
| E-06 | Secure Docker execution and no host fallback | Fixed operations, no network, non-root, read-only, resource limits, timeout cleanup | `execution.py`, `scripts/Dockerfile.sandbox` | Isolation/timeout and real Docker tests passed | Stop Docker and observe BLOCKED | Tested |
| E-07 | Source preservation, path/scope safety, immutable regression tests | Private clone, reject unsafe paths and entire invalid patch batches | `repository.py` | Path, batch, secret and existing-tests cases passed | Compare source Git status and isolated diff | Tested |
| E-08 | Document all assumptions, mocked dependencies and limitations. | Explicit fixture labels, security boundary, configuration and verification limitations | `README.md`, `docs/limitations.md`, `docs/security-model.md` | Manual documentation review | Follow README and demo guide | Implemented |
| E-09 | Keep current implementation status and traceability | This matrix and progress document | `docs/traceability.md`, `docs/IMPLEMENTATION_STATUS.md` | Review against actual command results | Inspect recorded results and blockers | Tested |
| E-10 | No secrets, remote push or automatic deployment | Environment credentials, excluded runtime artifacts, no deploy/push capability | `.gitignore`, `.env.example`, `api.py`, `providers.py` | Secret rejection and approval tests passed | Inspect API schema and Git status | Tested |
| E-11 | Use LangGraph checkpoints and appropriate durable application persistence. | LangGraph SQLite checkpoints plus SQLAlchemy run/events | `workflow.py`, `store.py` | Checkpoint assertion and actual process restart tests passed | Restart CLI/backend and inspect existing run | Tested |
| E-12 | Deliver a bounded local prototype and document unverified assumptions | Local single-user scope; explicit limitations; no production claims | `README.md`, `docs/limitations.md` | Real Docker failure/recovery and approval gate tests passed | Follow complete demo procedure | Tested |

Paths abbreviated in E rows are under `backend/cortexforge/` unless otherwise qualified. Test functions are in `backend/tests/test_workflow.py` or `backend/tests/test_safety.py`. A fixture-backed success does not verify live model quality. The optional live acceptance profile and usage calculations have passed injected-adapter/HTTP contract tests.

## Executed evidence and remaining boundary

- `evaluation/backend-junit.xml`: full backend verification, including real Docker and process-restart tests.
- `evaluation/safety-junit.xml`: 13 focused safety tests passed, including scanner-suppression rejection.
- `evaluation/live-contract-junit.xml`: 2 live configuration/provider contract tests passed using explicit test adapters.
- `evaluation/results.json`: all 8 controlled evaluation outcomes and actual baseline/candidate stdout, exit codes and durations.
- `evaluation/backend-security.json`: backend Bandit scan with no medium/high findings; one documented container-tmpfs false-positive suppression.
- `evaluation/frontend-tests.json`: frontend test report; production build and npm audit also passed.
- `docs/screenshots/human-review.jpg`: actual connected UI showing 8 unit tests, 12 trusted acceptance tests and one repair; no human approval fabricated.
- `evaluation/live-results.json`: actual Groq-generated plans/changes and provider-reported usage; all quality/acceptance gates passed. Human approval by reviewer-1 verified; see evaluation/final-run-audit.json.
- No GitHub repository has been published, and no push or external deployment has been performed. Those operations were expressly outside authorization.

## Final run-state audit

See `evaluation/final-run-audit.json`: 2 approved, 1 rejected, 5 intentionally failed, 1 intentionally blocked. All failed/blocked rows have injected demo faults; no unexpected failed live run exists. The rejected run had repaired its test failure and passed final checks before the human rejected it. Dashboard rows now name the injected scenario.

## How to read this document

This is a requirement-to-evidence map and project progress record, not the original specification or a percentage-complete score. Each row connects a requirement to its implementation approach, source files, automated checks, demonstration procedure and status.

- **Not Started:** no implementation yet.
- **In Progress:** work exists but is incomplete.
- **Implemented:** code or documentation exists; relevant verification is not yet recorded.
- **Tested:** relevant verification was executed successfully within the stated scope.
- **Blocked:** progress or verification needs a missing prerequisite.

Tested does not mean universally correct, production-ready, or tested on every repository. Current evidence covers the controlled local Python sample, actual Groq generation, real Docker checks, injected failure scenarios and persisted human decisions. Cost calculation is tested with configured prices; actual live cost remains unknown because pricing is unset. QA/security/release are deterministic specialist modules; analyst/architect/developer use the live model. Security severity includes an explicitly documented local-policy classification.

No unimplemented company requirement has been identified within the working-vertical-slice scope. Optional broader-repository support, arbitrary dependency provisioning, enterprise authentication, PostgreSQL, migrations and production sandbox hardening are not implemented. These are limitations, not requirements added to the company's statement. Manual patch application and repository submission remain delivery steps; automatic merge/deployment is intentionally absent.

## Independent audit update — 2026-11-21

Historical results above are preserved. Fresh verification: 70 backend tests
passed with zero failures/skips (`evaluation/audit-final-backend.xml`), five
frontend tests passed and production build passed. All eight real-Docker fixture
scenarios passed in `evaluation/fixtures-8f1f434fb7b7462d80cdc7e1ea3f1e0d.json`.
See FINAL_AUDIT.md for reproduced defects, fixes and evidence boundaries.

| Capability | Implementation | Verification | Demo | Status |
|---|---|---|---|---|
| Immutable test infrastructure and canonical paths | repository.py | test_audit.py path/configuration/junction probes passed | Try a scoped conftest write; observe rejection before write | Tested |
| Meaningful existing code-path change required | repository.py source_changed; workflow.py release gate | test_noop_cannot_reach_review passed | Unchanged/whitespace-only proposals cannot reach approval | Tested |
| Provider validation, partial outputs and unknown metrics | providers.py; workflow.py | HTTP envelope/status/usage and bounded partial-response tests passed | Inspect failed-call identity and safe stop | Tested |
| Concurrent runs and completed-check recovery | workflow.py; store.py | concurrent runs plus actual subprocess reuse tests passed | Inspect check_reused events with content hash | Tested |
| Durable cooperative cancellation | api.py; workflow.py; store.py; main.tsx | during-model and blocked-run cancellation tests passed | Cancel run; in-flight operation finishes before safe boundary | Tested |
| Explicit independent acceptance profile selection | main.tsx | frontend submission integration test passed | Select matching live sample oracle | Tested |
| Multi-file refund scenario | sample-repos/refund-service; refund_acceptance.py; evaluation/live.py | Live 15 unit / 20 independent cases plus lint/security passed after 2 repairs; live-refunds-aaf4eb55a7dc400ca16873196177c72d-resume0.json | Run live.py --scenario refunds --pace-seconds 62 | Tested |

The current automated suite mixes deliberately labelled contract doubles,
real Docker integrations and subprocess tests. It is not 70 live model calls.
The independent refund oracle is author-written and injected only into snapshots.
Manual human approval remains separate from automated evaluation success.

## Final verification pointers

Current full-suite evidence is `evaluation/audit-final-backend.xml` (70 passed,
zero failures/skips, updated sandbox). Current fixture evidence is
`evaluation/fixtures-1d4b80a403bd4b5a906c8c5886a8fb54.json` (all eight passed).
Five frontend tests and production build passed. The strengthened live refund
scenario passed 15 unit and 20 acceptance tests after two repairs, and passed
independent revalidation in the updated sandbox. Original requirement rows and
historical evidence references are preserved. No original requirement is marked
unimplemented within the stated local scope; optional production extensions
remain limitations. Final human review of the refund candidate is still pending.
