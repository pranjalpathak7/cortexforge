# Refund service baseline

A small FastAPI application with transport (`api.py`), business rules
(`service.py`), a locked in-memory ledger (`ledger.py`) and an unrelated health
component. `create_app()` creates fresh state. GET payment and missing-payment
behavior are covered by immutable regression tests. Refunds are not implemented.

Task: add `POST /payments/{payment_id}/refunds`. JSON has exactly `amount`, a
strict positive integer in paise. Require `Idempotency-Key` with 1–64 characters
from ASCII letters, digits, hyphen or underscore. Reject invalid body/header with
422. A new refund returns 201; replay of the same key/payment/amount returns 200
and the identical original JSON. A response has `payment_id`, `amount`,
`refunded_total` and `status`. Keys are global within this app instance; reuse
with a different payment or amount returns 409 without mutation. Unknown payment
returns 404. Cancelled payment or refund exceeding the remaining captured amount
returns 409. Partial refunds set status `partially_refunded`; an exact final
refund sets `refunded`. Prior exact replays must still succeed after full refund.
Failures must not consume a key. Concurrent duplicate requests must mutate once.

Keep business rules in the service and HTTP validation/mapping in the API.
Preserve GET behavior and existing tests; add new regression/negative tests.
Do not change `health.py`. No real money, external gateway, database, authentication
or cross-process durability is claimed for this sample. CortexForge runs it only
inside Docker.
