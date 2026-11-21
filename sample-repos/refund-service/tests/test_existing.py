from fastapi.testclient import TestClient

from api import create_app
from health import health


def test_read_payment():
    client = TestClient(create_app())
    assert client.get("/payments/p1").json() == {
        "id": "p1",
        "amount": 1000,
        "refunded": 0,
        "status": "captured",
    }


def test_unknown_payment():
    assert TestClient(create_app()).get("/payments/missing").status_code == 404


def test_health():
    assert health() == {"status": "ok"}
