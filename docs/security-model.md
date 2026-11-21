# Local security model

Treat generated code, repository contents and model outputs as untrusted.
Only authorized local, clean, committed Git repositories are supported. A bare
clone with `--no-local` and a new branch/worktree prevents changes to the original
repository, including its branch refs. Symlink/submodule trees, traversal,
Windows drive paths and junction escapes are rejected. Only explicitly scoped
Python files and new test modules may be written. All changes are validated
before any file write. Git hooks and global/system Git config are disabled.

The Docker adapter exports source without `.git` or hidden files into a temporary
snapshot. It uses an unprivileged user, read-only root and source mount, no
network, no capabilities, no-new-privileges, 1 CPU, 256 MB memory, 64 processes,
64 MB tmpfs and a 60-second command deadline. No host credentials or Docker
socket enter the container. The image is built separately with pinned pytest,
Ruff and Bandit; generated commands and dependency installs are forbidden.
Only unit, lint, security and the fixed sample acceptance oracle operations exist. The host launches Git/Docker
with argument lists, never LLM shell strings. Missing Docker is a blocker.

Local Docker is a development boundary, not perfect isolation from hostile
workloads. Use only controlled local samples on a trusted single-user machine.
Container image provenance, sophisticated malicious Git objects, resource
exhaustion in import and scanner evasion need stronger production defenses.
Container stdout is continuously drained into a bounded 50 KB tail buffer.
Unparseable successful scanner output fails closed instead of claiming clean
security evidence. This still is not a production multi-tenant service.

Human review requires a private configured token and matching evidence hash.
The hash binds checks, diff and full worktree content; mutation prevents approval
and patch export. Agents never see the token and cannot invoke review tools.
This is local possession-based authorization, not independently verified human
identity or enterprise authentication. A privileged host user can edit SQLite;
event history is append-only through the app, not tamper-proof storage.

Bandit tool severity is retained verbatim. Local policy classifies B307 (eval)
and B602 (shell injection) as critical execution risks; this is an explicit
policy classification, not a claim that Bandit emitted a critical rating.
Generated `# nosec` comments cannot suppress findings: sandbox scans use
`--ignore-nosec`. The trusted adapter source has one documented B108 suppression
for the literal container `/tmp` tmpfs target; host temporary directories are
created by `TemporaryDirectory`, not by that path.

No merge, push or deployment endpoint exists. Approval is an auditable decision,
not permission for the agent to deploy. Do not expose this local API publicly.


Audit hardening rejects test infrastructure writes (including conftest and tool
shadowing filenames), noncanonical paths and no-op source changes. Sandbox
versions are pinned in scripts/Dockerfile.sandbox and audited independently of
the host. New tool records include the resolved image identity and acceptance
oracle hash; historical records retain their original evidence fields.
