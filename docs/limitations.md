# Assumptions and limitations

- Initial support: small, clean, committed Python repositories with dependencies
  already in the curated sandbox image. No arbitrary dependency installation.
- Live Groq was verified on the controlled payments task with GPT-OSS 120B.
  This does not establish reliability on arbitrary repositories or requirements.
- Demo agent outputs are seeded fixtures for the bundled payments task only;
  no fresh model reasoning is claimed. Actual checks require Docker.
- QA, security and release are deterministic specialist agents. They do not
  perform speculative LLM reviews or full dependency vulnerability analysis.
- Bandit and simple secret/scope rules are incomplete security analysis.
- No automatic merging/deploying; export an approved patch for manual use.
- SQLite schema initialization is included, but Alembic migrations, PostgreSQL,
  distributed workers and multi-user identity are not implemented.
- Partial interrupted patches stop for inspection, rather than attempting
  automatic rollback across an uncertain external side-effect boundary.
- UI uses custom accessible CSS and a two-pane diff; Tailwind/shadcn/Monaco are
  optional stack preferences and are not dependencies of this implementation.
- Current verification and open blockers are recorded in IMPLEMENTATION_STATUS.md
  and the requirement matrix. These documents do not imply full completion.


The refund sample is an additional bounded FastAPI exercise, not a financial
service. Its ledger is process-local memory. The platform may expose genuine
live failures and provider quota/context blocks; fixture success is not evidence
of universal live success. Cancellation is cooperative. Inspector/scanner and
oracle coverage remain incomplete even when all checks pass; manual review
found and corrected a gap during this audit.
