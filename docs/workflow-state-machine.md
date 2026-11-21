# Durable workflow and recovery

CREATED → REQUIREMENT_ANALYSIS → ARCHITECTURE_PLANNING → BASELINE → IMPLEMENTING
→ TESTING → SECURITY_REVIEW → RELEASE_REVIEW → AWAITING_HUMAN_APPROVAL
→ APPROVED or REJECTED.

Analysis may pause at AWAITING_CLARIFICATION. A human answer returns it to
analysis. Failed unit/lint checks enter REPAIRING, returning to TESTING after
a new patch. Repair attempts are bounded by MAX_REPAIR_ATTEMPTS (0–5).
Repeated content hashes fail before reapplication. Security failure and policy
violation enter FAILED, with no approval override. Start a corrected fresh run.

Provider/Docker unavailability enters BLOCKED with a persisted resume state.
Explicit retry is allowed at most three times. Pending operations are written
before external work. After interruption, a pending check requires explicit
resume. A pending patch requires human inspection and a fresh run: the system
does not guess whether a partial multi-file write completed.

LangGraph checkpoints and run documents are separate durable stores. Resumption
loads the run document and advances the graph from its authoritative state.
Model calls are side-effect-free proposals and can be repeated after a crash;
their remote billing cannot be deduplicated. Tests launch separate Python
processes and inspect preserved state. Additional hard-kill tests cover a pending
write marker. Inspect test names and executed results in traceability.md.


Cancellation is a durable event and a terminal CANCELLED state. A request waits
for the current model/tool deadline or operation to finish, then stops before
another patch/check. It preserves isolated artifacts and prohibits approval.
Completed checks may be reused after restart for the same operation, content
hash and repair iteration. Provider-rejected JSON receives bounded schema retry;
transport/quota errors remain explicit BLOCKED states with capped human resume.
