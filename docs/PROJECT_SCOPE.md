# PS3 project scope

CortexForge is an independently implemented case-study prototype for coordinating
software changes with explicit human oversight. This document describes the
project in our own words; it is not a copy of the company-issued brief.

A user supplies a change request and a local sample Git repository. Planning
produces measurable outcomes and a work breakdown. Design inspection narrows the
allowed files, and implementation happens in an isolated worktree. Docker runs
unit, lint and security checks. A review package combines the diff, recorded
results and limitations; a human must authorize patch export. Merge and deployment
remain outside the automated workflow.

The prototype also demonstrates typed specialist interfaces, durable execution
records, capped retries, measured provider usage, restricted execution and
before/after evaluation. Controlled faults exercise conflicting design decisions,
broken implementations, dangerous code, invalid model responses, provider outages,
and duplicate or out-of-scope edits. A repair demonstration shows a failed check
followed by a successful rerun and a human review checkpoint.

See [traceability](traceability.md) for capability-to-source/test mappings and
[limitations](limitations.md) for the boundaries of the verified samples. This
is a local demonstration, not a production enterprise platform. The company
brief is excluded from this publication candidate and its Git history.
