"""Business logic; transport concerns belong in api.py."""

from ledger import Ledger


class PaymentService:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def get_payment(self, payment_id: str) -> dict:
        with self.ledger.lock:
            if payment_id not in self.ledger.payments:
                raise KeyError(payment_id)
            return dict(self.ledger.payments[payment_id])
