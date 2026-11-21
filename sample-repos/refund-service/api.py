"""Small payment API with isolated application state per factory call."""

from fastapi import FastAPI, HTTPException

from ledger import Ledger
from service import PaymentService


def create_app():
    app = FastAPI()
    service = PaymentService(Ledger())

    @app.get("/payments/{payment_id}")
    def get_payment(payment_id: str):
        try:
            return service.get_payment(payment_id)
        except KeyError:
            raise HTTPException(404, "Payment not found") from None

    return app
