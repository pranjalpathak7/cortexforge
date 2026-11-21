# Final local submission verification

Status: ready for authorization of a local initial commit; clean-clone execution
is PENDING. This verification inspected current code, Git state, durable records,
API responses and existing executed reports. It did not rerun the full suites,
make new model calls, modify application code/tests, or approve a patch.

## Refund patch for human review

Run: `aaf4eb55a7dc400ca16873196177c72d`.
Current state verified in read-only SQLite and the running API:
**AWAITING_HUMAN_APPROVAL**. Decision is null; no human-decision events exist.
The export endpoint returns 409. Source and isolated worktree HEADs both remain
at baseline `2909548ea02e297240678b5b6581b900dfd54790`; source Git status is clean.
The patch has not been committed/merged into the supplied sample. The workflow
history shows no approval enabling an automatic export. Independent manual file
copies outside the application's audit trail cannot be ruled out; the JSON
execution report intentionally contains a reviewable diff, not an approved export.

Exact evidence SHA-256:
`c36dbf8c25bf18fe6cf213a47485285b9bc345c0be2de9689db5a93cdb29c809`

Exact source-tree SHA-256 (recomputed and matched):
`abeb15190fb992b92499080d9af179b9e0b849b21aae2af5c9241a5d69db9ac1`

| Changed file in isolated sample | Review focus |
|---|---|
| api.py | POST refund endpoint; StrictInt positive paise; extra fields forbidden; ASCII idempotency key validation; 201 new/200 replay, 404 missing, 409 conflict, 422 invalid input |
| service.py | Locked check-and-mutate; global per-app idempotency; identical original replay response; conflict detection; cumulative refund limits; stored partial/full status transitions; failures do not consume keys |
| tests/test_refunds.py | New regression and negative tests, including duplicate/concurrent requests; existing tests unchanged |

`ledger.py`, `health.py` and baseline tests are unchanged. These generated files
remain in the ignored isolated worktree. The proposed initial platform commit
includes the unmodified sample baseline, generic workflow, trusted oracle and
review evidence; it does NOT apply the unapproved refund patch to the baseline.

## Exact executed evidence

- `evaluation/live-refunds-aaf4eb55a7dc400ca16873196177c72d-resume0.json`:
  genuine Groq output, full diff, baseline and candidate stdout, exit codes,
  timings and usage. Final: 15 unit tests, 20 independent acceptance cases,
  lint and security passed after two repairs. Five calls reported 20,078 tokens;
  cost remains unknown. Baseline acceptance failed because refunds were absent.
- `evaluation/refunds-updated-sandbox.json`: same source-tree hash revalidated
  against the updated image; all four operations exit 0, 15 unit/20 acceptance,
  security findings empty. Image identity:
  `sha256:09227f8edbb57e5da4519368d6d26f4ba8c9fe814967bd0409d3649044ea7b41`.
  Oracle SHA-256:
  `b74afde882c90113ed043d1a18d6c309cdaa5d165389e482cfedb685170dbd06`.
- `evaluation/audit-final-backend.xml`: 70 passed, zero errors/failures/skips,
  160.905 seconds. `evaluation/audit-final-frontend.json`: five passed, zero failed.
- `evaluation/fixtures-1d4b80a403bd4b5a906c8c5886a8fb54.json`: eight expected
  real-Docker outcomes passed, including intentional failures and blocking.
- Final host/sandbox/npm audit reports record no known vulnerabilities at audit
  time. These are historical executed results, not a new advisory database query.

## Security findings and remaining patch risks

Bandit reported no findings in the final candidate. Path/scope and immutable-test
gates passed. This does not prove security. The sample has no authentication or
real payment gateway; the ledger and idempotency map are in-memory, unbounded and
not durable across application restarts. They are suitable for the controlled
exercise, not production financial processing. Locks operate within one process.
The candidate uses deprecated Pydantic class Config syntax, contains minor
comment/encoding/style issues, couples service return values to HTTP status,
and relies on API validation for input safety. These are review considerations;
no new feature/refactor was performed during this verification.

## README and clean-clone prerequisites

README PowerShell commands reference existing files and valid package scripts.
Run commands from the repository root; the second frontend terminal also starts
there before `cd apps/web`. Python 3.12 is the tested lockfile environment.
Use the existing documented locked-install alternative for the clone check:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
Copy-Item .env.example .env
# Set a new local REVIEW_TOKEN; live mode additionally needs a Groq key.
docker build -f scripts/Dockerfile.sandbox -t cortexforge-sandbox:clone-check .
$env:SANDBOX_IMAGE = 'cortexforge-sandbox:clone-check'
.\.venv\Scripts\python.exe scripts/init_sample.py
.\.venv\Scripts\python.exe scripts/init_sample.py --sample refund-service
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe evaluation/run.py
Push-Location apps/web
npm.cmd ci
npm.cmd test
npm.cmd run build
Pop-Location
```

README's `npm install` and editable dev install are valid but can resolve newer
versions; `npm ci` and the lockfile commands above are the reproducibility path.
Direct .venv interpreter commands avoid PowerShell activation-policy dependency.
Docker's base tag/transitive dependencies are not fully digest/hash locked, so a
future rebuild is not guaranteed byte-identical; execute and record actual checks.
Network access to package registries and Docker is required for fresh setup.

Static inspection found no required ignored runtime artifact: sample preparation
creates new committed sample repos from included templates; Engine creates its
SQLite/runtime directories; fixture mode needs no API key. A clone starts with an
empty dashboard, not copied local approval history. Historical evidence remains
available in versioned reports. Exact prior model output is not guaranteed on a
fresh live run. No clean-clone success is claimed yet.

## Exact proposed initial commit

See `INITIAL_COMMIT_FILES.txt`: one explicit repository-relative path per line,
including this report and the manifest itself. It includes both sample templates,
Dockerfile, Python/frontend locks, all source/tests, evaluation scripts, historical
reports (including failures), documentation and the screenshot. No wildcard or
ignored-file inclusion is authorized by this proposal.

Excluded: .env, runtime databases/worktrees/checkpoints, .venv, node_modules,
build outputs and caches. Existing local files are preserved; nothing is deleted.
Configured credential-value scan found no matches in proposed files. The example
key and review-token fields are blank. No remote is configured and no initial
commit exists. No staging or commit was performed. Commit message proposed:
`Initial CortexForge Pine Labs submission`.

The original problem statement hash is unchanged:
`200825c244429106800c63f3fbd31bea3ae50301558bbd56deac4dc3f96b75d7`.

## Outstanding actions / release gates

1. Human review: approve or reject the refund run in the application yourself.
   This is separate from permission to commit the platform and evidence.
2. Authorize the exact initial-commit manifest. If authorized, recheck it for
   drift, stage only those paths and make a local commit; no remote operations.
3. After that commit exists, execute a clean local clone with fresh dependencies,
   newly generated runtime files, sample initialization, backend/frontend checks
   and fixture evaluation. This is the remaining reproducibility verification gate.
4. Review clone results and choose any license/visibility decisions before a
   separately authorized GitHub publication. No publication is authorized now.

No newly reproduced functional release blocker was found in this inspection.
The missing authorized commit and unexecuted clean-clone test prevent a claim
of independently reproduced submission readiness. Prior failures/cancelled runs
and audit evidence remain intact.
