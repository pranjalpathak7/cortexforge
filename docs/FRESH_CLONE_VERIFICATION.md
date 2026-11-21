# Fresh-clone verification

Initial commit: `af6b3e1550c1e31bdc9dbc01abc41ad688e7bea8`.
Message: `Initial CortexForge Pine Labs submission`.
Committed files: exactly 103, matching INITIAL_COMMIT_FILES.txt.
Manifest SHA-256: `7ffa374a7ce29a699094a8a539dae8c3f34e554278516272c8bc9b5b09750b00`.
Commit author/committer: CortexForge <local@example.invalid> (neutral local identity).

## Pre-commit privacy verification

No configured API key/review token or token-pattern matches were found. Metadata
in 13 approved files was redacted: reviewer initials to reviewer-1, hostnames to
redacted-host, and temporary user paths to a portable placeholder. No outcomes,
timestamps, code, evidence hashes or approved paths were changed. Original copies
remain in ignored local storage. The screenshot was inspected visually and has
no EXIF/XMP metadata; it shows empty reviewer fields and no credentials. Synthetic
example.invalid emails, code decorators and a public advisory's example email
were retained. A second scan of the committed blobs found no remaining identified
personal metadata. This is a scoped scan, not a guarantee against every possible
secret format. The original company statement remains unchanged in the source.

## Isolation and environment

A genuine `git clone --no-local` was created in a newly allocated OS temporary
directory. Its HEAD equals the initial commit and it contains the same 103 files.
Its local origin reference was removed; the original repository has no remote.
No .env, .venv, database, node_modules or runtime worktree existed in the clone
before setup. Nothing ignored was copied from the original checkout.

Windows 11 build 26300; Python 3.12.4; Node 22.16.0; npm 11.11.0;
Git 2.49.0.windows.1; Docker client/server 28.5.1, Linux containers.
The new virtual environment uses the installed base interpreter, not the
original project's site-packages. Provider keys, model overrides, DATABASE_URL,
PYTHONPATH and runtime configuration were removed from child process environments.

README's documented reproducibility alternatives were selected: requirements.lock
plus editable `--no-deps` installation, and `npm ci` with package-lock. Direct
.venv interpreter invocation is equivalent to activation and avoids machine
execution-policy dependence. Installation used an empty npm cache and pip's
`--no-cache-dir`; Docker uses `--no-cache` and a separate freshclone tag. Network
package access and the already installed Docker engine/base-image store are host
prerequisites, not copied project runtime artifacts. The build still resolves
the README Dockerfile's mutable base tag/transitive packages; bit-identical future
images are not claimed.

## Final execution results — 2026-11-21

**PASS: genuine clean local clone of the initial commit.** No source edits,
lockfile changes, dependency substitutions or weakened tests were needed.
All commands below exited 0. `python` denotes the clone's new .venv interpreter;
frontend commands ran under apps/web; remaining commands ran at the clone root.
`<evidence>` and `<new-empty-cache>` denote newly allocated paths outside the clone.
SANDBOX_IMAGE was set to cortexforge-sandbox:freshclone for execution.

| Step / actual command (portable paths) | Exit | Wall seconds |
|---|---:|---:|
| `python -m pip install --no-cache-dir -r requirements.lock` | 0 | 353.42 |
| `python -m pip install -e . --no-deps` | 0 | 13.67 |
| `python -m pip check` | 0 | 1.77 |
| `npm.cmd ci --cache <new-empty-cache>` | 0 | 15.58 |
| `npm.cmd test -- --reporter=json --outputFile=<evidence>/frontend-tests.json` | 0 | 5.61 |
| `npm.cmd run build` | 0 | 9.44 |
| `docker build --no-cache -f scripts/Dockerfile.sandbox -t cortexforge-sandbox:freshclone .` | 0 | 188.14 |
| `python scripts/init_sample.py` | 0 | 0.55 |
| `python scripts/init_sample.py --sample refund-service` | 0 | 0.51 |
| `python -m pytest -q --junitxml=<evidence>/backend-junit.xml` | 0 | 161.3 |
| `python -m ruff check backend scripts evaluation` | 0 | 1.0 |
| `python evaluation/run.py` | 0 | 74.05 |

- Backend JUnit: **70 tests, 0 failures, 0 errors, 0 skipped**, 155.015 seconds
  suite time (161.30 seconds process wall time).
- Frontend JSON: **5 passed, 0 failed, 0 pending**. TypeScript/Vite production
  build succeeded. Fresh npm installation reported 0 vulnerabilities.
- pip check: `No broken requirements found.` Ruff: `All checks passed!`
- Both sample initialization commands created new, committed sample repositories.
- Fixture evaluation: **8/8 expected outcomes passed**, using actual Docker:

| Scenario | Actual terminal state | Evaluation |
|---|---|---|
| none | AWAITING_HUMAN_APPROVAL | PASS |
| test / bounded repair | AWAITING_HUMAN_APPROVAL | PASS |
| security | FAILED | PASS |
| scope | FAILED | PASS |
| repeat | FAILED | PASS |
| malformed | FAILED | PASS |
| provider | BLOCKED | PASS |
| disagree | FAILED | PASS |

FAILED/BLOCKED here are deliberate safety outcomes, not failed verification.
The new fixture report is `fixtures-268bbf6ca82a45bf9d13e21c29d0857f.json`.
No human approval was fabricated. No live model calls were made or API tokens spent.

## Startup and provenance checks

The clone received a new .env copied from its committed example, with a newly
generated local review token and no Groq key. The token was not printed or saved
in this report. Uvicorn was started with `python -m uvicorn cortexforge.api:app
--host 127.0.0.1 --port 8001`; port 8001 avoided disrupting the existing application.
Health returned Docker ready, live_configured=false. Authenticated GET runs returned
an empty list. The smoke-test process was stopped after verification (3.66s).

Imports resolved to the cloned backend and clone-local .venv. Tracked clone files
remained unchanged; only the expected new fixture evaluation JSON was untracked.
Original runtime databases, worktrees, credentials and pending refund approval
were not copied into the clone. Browser interaction and a new live Groq run were
not repeated; frontend tests/build and backend startup/API checks are the checks
claimed here. The documented locked-install path was tested, not a separate
unlocked `pip install -e '.[dev]'` / `npm install` dependency resolution.

## Evidence preservation

Raw command logs, per-command exit/timing JSON, environment metadata, backend JUnit,
frontend JSON and the new fixture report are preserved locally under the ignored
`.cortexforge/fresh-clone-evidence/` directory. They remain local because raw logs
contain temporary machine paths. The portable results above are suitable for the
repository. Raw evidence is not included in the original 103-file commit.

SHA-256 of selected raw evidence (before any metadata redaction):

| Artifact | SHA-256 |
|---|---|
| `backend-junit.xml` | `ad86a08122318cdac9c2eaed6c00d2c02ba25f291bccbba9871f812ef8c47078` |
| `frontend-tests.json` | `225a594b1534124c5d08410ef114e21f3056e8b84a2b6a582a3a70bd1a15a082` |
| `fixtures-268bbf6ca82a45bf9d13e21c29d0857f.json` | `ba521e4a40c5318ed109527b35794e5d5782c5c1946523764aac5e8e2c2e7f1c` |
| `docker-build.log` | `4257f2f37184b2847bbe26015f6fb00ec54727c5fe5a6b10001266062df494e8` |
| `python-install-lock.log` | `ea59be9ef16aa9280d1e37e1fc1b2887f69f791096b615ce6bef50f19c2073c2` |
| `api-smoke.json` | `ed4ca7d4f218e89aa40d24ec34b96ca9609c81134094bd4f9ecbe5ef3c03d985` |

## Failures, warnings and limits

No installation, build, test, initialization or fixture-evaluation command failed;
no tests were skipped. Downloads were slow, not bypassed using original runtime
artifacts. npm reported a deprecated transitive whatwg-encoding package; pip/npm
update notices and container build root-install warnings were nonfatal. Runtime
container commands still execute as the configured unprivileged user.

This is a fresh local clone on the same Windows/Docker host, not proof of every
OS or a completely new machine. Existing host Python/Node/Git/Docker and network
registries are prerequisites. Docker --no-cache rebuilt application/tool layers;
it does not erase the host's base-image/content store. Dependency locks and the
Dockerfile do not guarantee byte-identical images forever. Live Groq mode still
requires the user's credentials and sufficient quota; fixture mode does not.

## Commit and remaining human actions

The original local repository retains initial commit
`af6b3e1550c1e31bdc9dbc01abc41ad688e7bea8` with 103 approved paths.
The report was subsequently committed, without amendments or code changes, as
`952f807386a4fcb3fa91ec3f3f5217bae4ebc6e7` with message
`docs: add verified clean-clone reproducibility report`.

The separate publication candidate has new history and documentation/privacy
changes. The execution results above describe the original initial commit;
they do not claim a new full test run of the publication candidate. Application,
test, dependency, Docker and evaluation files are preserved unchanged. The
company brief remains only in local excluded storage. Historical results and
hashes above have not been altered. Refund approval is a separate human action.
No remote, push, publication or deployment has been performed.
