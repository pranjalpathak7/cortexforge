# Local submission readiness

This document is a release checklist, not publication authorization.

## Coverage and evidence

All seven core requirements, six stretch requirements and six failure scenarios
have implementation/test mappings in `traceability.md`. The original statement
is unchanged and read-only. Historical live discount evidence and actual human
decisions remain preserved. Fresh audit results are recorded in FINAL_AUDIT.md.

The additional refund scenario is separately evaluated; failures and provider
limits are preserved in `evaluation/live-refunds-*.json`. Check the latest audit
entry for its verified outcome. Do not infer success from its implementation.

## Reproducibility

- Windows PowerShell setup is in README; activate `.venv` before using Python.
- Python dependencies have a lockfile; frontend uses `npm ci` and package-lock.
- Docker-only execution uses the curated sandbox image; no host fallback.
- Both sample templates are committed separately into ignored runtime folders
  by `scripts/init_sample.py`; agents never edit the versioned templates.
- Fixture evaluation creates a separate database per batch and unique JSON
  reports, preserving human-review records and historical evidence.
- Live evaluation requires a working Groq key and sufficient quota. Pacing is
  explicit, optional and does not add hidden retries or increase budgets.

## Security and hygiene

`evaluation/submission-scan.json` records a scan of publishable files against
configured credential values and oversized files. Runtime databases, .env,
virtual environments, node_modules and worktrees are ignored. Dependency audits
and Bandit reports are under evaluation. These checks are not a guarantee that
all possible secrets or vulnerabilities have been detected.

No GitHub repository was created. No push, publication or deployment occurred.
The current checkout has untracked source files; the reversible audit snapshot
is local and ignored. A Git commit has not been fabricated as an existing release.

## Limitations and outstanding release decisions

- A human must review any new live result. Automated evaluation never approves.
- No production identity, distributed workers, PostgreSQL verification,
  arbitrary dependency installation or hostile multi-tenant sandbox guarantee.
- Cost is unknown unless valid nonnegative finite pricing is configured.
- Generated tests remain untrusted; independent oracles cover only named cases.
- The refund sample uses process-local memory and does not move real money.
- Dependency locks reflect the tested environment; another machine's fresh
  clone is not claimed verified until its setup/checks execute.

## Exact steps before publication

1. Read FINAL_AUDIT.md and confirm the latest checks and live evidence.
2. Review `git status --short` and `git diff --no-index`/editor changes as needed;
   inspect all files intended for the initial commit.
3. Run the README verification commands and inspect skip/failure counts.
4. Confirm `.env`, `.cortexforge`, build outputs and credentials remain ignored.
5. Review the README screenshot and retained reports for personal information.
6. Choose repository visibility and a license if desired; neither was assumed.
7. Make the local initial commit after content review. Obtain explicit user
   authorization before creating a remote repository or pushing anything.
8. After publication, verify the GitHub rendering and clone instructions, then
   submit the repository URL to the company yourself.


Report portability: absolute developer-machine paths in selected JSON/XML
metadata were normalized to `<workspace>` or `<temporary-directory>`. Test
outcomes, tool stdout evidence, timing and hashes were not changed. Raw report
copies remain in the ignored local audit checkpoint directory.

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
