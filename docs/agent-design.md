# Specialist contracts

| Agent | Inputs | Outputs | Authority |
|---|---|---|---|
| Analyst | requirement, source metadata, constraints | criteria, tasks, questions | request clarification |
| Architect | specification, actual files, dependencies | scoped files, rationale, risks, checks | propose scope |
| Developer | design, source, failed tool evidence | full file contents, summary, disagreement | propose changes only |
| QA | isolated worktree | unit/lint exit codes and captured output | fixed Docker operations |
| Security | isolated source | Bandit JSON and policy violations | block readiness |
| Release | diff, checks, risks | rubric, evidence hash, review checkpoint | request human review |

Live analyst, architect and developer use Groq structured output through
the official Groq-compatible HTTP API. Model IDs must be explicitly configured; use
`MODEL_ANALYST`, `MODEL_ARCHITECT`, `MODEL_DEVELOPER`, `MODEL_RESOLVER` to override
`LLM_MODEL`. The provider interface accepts agent, context and JSON schema and
returns text plus usage. An injectable test adapter and labelled demo adapter
exercise failures without API keys. No optional cloud provider is implemented.

Malformed output receives one schema correction attempt. Disagreement receives
at most two architect resolution rounds; an expanded scope or unresolved third
objection escalates to a human-visible failure without applying the proposal.

Usage events preserve provider-reported input/output/thinking tokens, measured
latency and configured-price cost estimates. Missing usage/prices remain null
and explicitly unknown. Failed calls may still be billed; unknown is never
reported as free. Fixture calls are labelled not applicable. QA/security/release
have tool durations, no invented token consumption.

Reference: [Groq structured output documentation](https://console.groq.com/docs/structured-outputs).
