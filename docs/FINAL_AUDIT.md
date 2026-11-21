# Independent engineering audit

Audit started 2026-11-21. This report distinguishes newly executed verification
from historical evidence. The original statement SHA-256 is
`200825c244429106800c63f3fbd31bea3ae50301558bbd56deac4dc3f96b75d7`.
Source checkpoint: ignored `.cortexforge/audit-checkpoints/before-audit.zip`.

## CRITICAL

No confirmed critical finding at initial inspection. This is not a security certification.

## HIGH

### H1 — Writable test infrastructure and noncanonical scope paths

- Location: `backend/cortexforge/repository.py:validate_scope`, `safe_path`.
- Description: existing root `conftest.py` and paths such as
  `tests/test_helpers/conftest.py` pass the former write rules. Canonical path validation was also tightened as defense in depth; the initial
  alias probes already failed closed under the broader existing policy.
- Impact: model proposals could alter regression-test behavior despite the
  advertised immutable-test policy.
- Reproduction: focused regression probes in `backend/tests/test_audit.py`.
- Proposed fix: require canonical portable paths; protect test configuration,
  tool-shadowing modules and test files; permit new direct test modules only.
- Verification: audit regression suite and full 70-test backend suite passed (see dated artifacts).

## MEDIUM

### M1 — Provider envelope and usage validation gaps

- Location: `backend/cortexforge/providers.py:GroqProvider.generate`.
- Description: non-object usage metadata and non-string content can raise
  unexpected exceptions; negative/non-numeric counters and invalid pricing
  are not validated. Failed calls omit provider/model identity.
- Impact: unreliable observability and unnecessary generic workflow failures.
- Reproduction: HTTP contract probes in `backend/tests/test_audit.py`.
- Proposed fix: validate envelopes, keep unknown metrics null, preserve identity
  and partial-response information, and test sanitized failure handling.
- Verification: audit regression suite and full 70-test backend suite passed (see dated artifacts).

### M2 — No-op implementation can reach human approval

- Location: `backend/cortexforge/workflow.py:RELEASE_REVIEW`.
- Description: `scoped_change` is reported but not enforced as a release gate.
- Impact: a generic run without an acceptance profile can pass checks without
  satisfying the company's code-modification requirement.
- Reproduction: unchanged full-file proposal, generic live run with injected
  provider, `test_noop_cannot_reach_review`.
- Proposed fix: require a nonempty change to an existing source code path.
- Verification: audit regression suite and full 70-test backend suite passed (see dated artifacts).

## LOW

### L1 — README verification claims are stale

- Location: `README.md`, Verified local result.
- Description: says three frontend tests and live approval pending, while the
  test suite has four tests and persisted audit records contain approval.
- Impact: reviewer confusion and reduced evidence credibility.
- Reproduction: compare README with tests and `evaluation/final-run-audit.json`.
- Proposed fix: replace with dated, linked verification and clear history.
- Verification: README reconciled with the preserved human-decision and evaluation records.

## VERIFIED WORKING

- Initial frontend suite executed successfully; JSON report:
  `evaluation/audit-initial-frontend.json`.
- Initial TypeScript/Vite production build passed.
- Source isolation, actual command execution, schema validation, approval and
  restart implementations have been inspected; fresh backend tests are running.
- No publication, push or deployment performed. Original statement unchanged.

## Audit boundary

This local system is not a hostile multi-tenant execution service. LLMs can be
influenced by repository text; deterministic scope and tool gates remain the
authority. Static scans and tests do not prove semantic correctness. Further
findings and executed results will be recorded as the audit proceeds.

## Executed audit verification

- Initial baseline: 40 backend tests passed in 116.91s; initial frontend suite
  and production build passed. Reproduction probes then exposed three genuine
  failures (test-hook writes and a no-op release); `audit-reproduction.xml`
  intentionally retains those pre-fix failures.
- Full post-fix suite: **70 passed, zero failed/skipped**, 162.474s JUnit time,
  `evaluation/audit-final-backend.xml`. Includes actual Docker, subprocess
  restart/kill, concurrency, cancellation and approval/tamper checks.
- Frontend: **5 passed, zero failed**, `evaluation/audit-final-frontend.json`;
  TypeScript/Vite production build passed. The new profile-submission test
  exposed an accessible-label issue, which was fixed and rerun successfully.
- Eight fixture scenarios passed with real Docker:
  `evaluation/fixtures-8f1f434fb7b7462d80cdc7e1ea3f1e0d.json`.
- Ruff and pip check passed. Bandit medium/high scan returned no findings:
  `evaluation/audit-final-security.json`. Python lockfile and npm dependency
  audits reported no known vulnerabilities in their dated reports.
- Publishable-file scan found no configured credential values and no file over
  5 MB. Original problem-statement hash remains unchanged.
- Connected UI profile selector inspected against the running application.
  Backend restarted to load the audit changes; existing decisions preserved.

## Additional reliability and product changes

- Completed checks can be reused after an actual process restart only when
  operation, source hash and repair iteration match. A regression test starts
  another interpreter to verify this behavior.
- Durable cooperative cancellation stops before another patch/check; artifacts
  remain inspectable. It does not instantly kill an in-flight provider call.
- Provider errors now include sanitized machine codes, provider/model and call
  attempt. Unsupported envelopes are controlled failures; invalid token counters
  and pricing remain unknown. Truncated responses cannot be accepted as complete.
- Provider-side JSON-generation rejection uses the same bounded schema retry.
- Model repair feedback is bounded; raw stdout remains unchanged in evidence.
  Deterministic failure excerpts preserve assertion lines without warning noise.
- Frontend exposes trusted acceptance profiles, cancellation, exact evidence
  and source hashes, call counts and repair counts. No decorative controls added.
- Evaluation writes unique reports and isolates fixture-batch databases, avoiding
  both history overwrites and confusing automated failures with user runs.

## Remaining audit boundary

The new live refund evaluation exposed genuine free-tier quota/context limits
and imperfect generated code. Failed attempts remain in uniquely named reports.
The final outcome is recorded in the progress/status documents. No failed live
attempt is relabelled as a fixture, and no generated test is treated as a trusted
oracle. Additional providers/languages and optional LLM security summaries were
not pursued because deterministic evidence and existing provider reliability
have higher value for this submission.

## Further independent findings

### H2 — Sandbox dependencies needed their own vulnerability audit

The host lockfile audit passed, but a separate `pip-audit` of the actual sandbox
image found 16 advisory entries affecting pytest 8.3.5 and Starlette 0.46.2
(including duplicate advisory IDs). Evidence: audit-sandbox-dependencies.json.
The Dockerfile now pins the versions already used in the audited host lockfile:
pytest 9.2.0, FastAPI 0.165.0 and Starlette 1.10.0. Ruff and Bandit retain
the previously audited scanner versions; the final runnable environment is audited separately.
A replacement image and actual sandbox checks are being verified independently.
Upstream references: [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
and [pytest changelog](https://docs.pytest.org/en/stable/changelog.html).

### M3 — Initial refund oracle missed stored partial-refund status

Live run f41a06d47eb04a018da301a724974112 passed its original 18 cases, but manual
diff inspection found that GET payment still reported captured after a partial
refund. That run was cancelled before any human approval, with an audit event.
Its historic report is retained, not rewritten. The strengthened 20-case oracle
checks stored status and small valid amounts, and gives invalid inputs explicit
type labels. A fresh model run evaluates these stronger checks. This illustrates
why passing tests alone cannot prove all requirements.

## Stronger live refund verification completed

Run `aaf4eb55a7dc400ca16873196177c72d` reached AWAITING_HUMAN_APPROVAL:
15 unit tests, 20 independent acceptance cases, lint and security passed after
2 bounded repairs. Baseline passed unit/lint/security and failed the missing
refund feature oracle. Actual generated changes: api.py, service.py and
new tests/test_refunds.py; no unrelated changes. Five actual Groq calls reported
20,078 tokens; cost remains unknown. Evidence: `evaluation/live-refunds-aaf4eb55a7dc400ca16873196177c72d-resume0.json`.

This final candidate includes the stored partial-refund status fix and strict
input validation. The earlier 18-case candidate is CANCELLED with a persisted
audit explanation and cannot be approved. No human approval was fabricated for
the new run. `evaluation/audit-api-final.json` verifies the running API, preserved
old approval/export, and a 409 response for export of the new unapproved patch.

## Updated sandbox verification

The replacement sandbox built successfully. Its installed dependency audit
reported no known vulnerabilities (`evaluation/audit-sandbox-final-dependencies.json`;
exact installed versions in `evaluation/sandbox-final-requirements.txt`). The
historical vulnerable-image report is retained as before-fix evidence. The final
image upgrades/removes the older installed pytest/FastAPI/Starlette versions.
The Dockerfile retains cached intermediate installation layers; only the final
upgraded environment is runnable under the published tag.

The final live refund candidate independently passed all four checks again in
the updated image, including all 20 acceptance cases. Report:
`evaluation/refunds-updated-sandbox.json`, with image identity, oracle hash and
source hash. This supplementary execution does not rewrite the original run's
review evidence. The verified image is now also tagged cortexforge-sandbox:local.

## Final audit closeout — 2026-11-21

The final complete backend rerun against the upgraded sandbox passed **70 tests,
zero failures/errors/skips, 160.905s** (`evaluation/audit-final-backend.xml`).
All eight fixture outcomes also passed after the final resolver fix:
`evaluation/fixtures-1d4b80a403bd4b5a906c8c5886a8fb54.json`.
The resolver compaction regression is fixed without weakening its tests; its
before-fix report is retained separately. Frontend: five tests and build passed.
The earlier checkpoint and label regressions were likewise fixed and rerun.

No known failing final check remains. Human approval of the final refund patch,
initial Git commit/content review and any eventual authorized publication remain
user-controlled steps. See IMPLEMENTATION_STATUS.md for the concise current
status; earlier progress entries in this audit are historical, not open blockers.
