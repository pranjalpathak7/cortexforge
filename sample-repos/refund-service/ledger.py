"""In-memory ledger for a controlled local exercise, not a payment gateway."""

from threading import RLock


class Ledger:
    def __init__(self):
        self.lock = RLock()
        self.payments = {
            "p1": {"id": "p1", "amount": 1000, "refunded": 0, "status": "captured"},
            "p2": {"id": "p2", "amount": 500, "refunded": 0, "status": "captured"},
            "p3": {"id": "p3", "amount": 700, "refunded": 0, "status": "cancelled"},
        }
        self.refunds = {}
