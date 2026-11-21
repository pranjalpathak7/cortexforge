"""Independent HTTP oracle, authored before any live model modification."""

REFUND_ORACLE = """import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from api import create_app

@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c

def refund(client, amount=300, key="request-1", payment="p1"):
    return client.post(f"/payments/{payment}/refunds", json={"amount": amount},
                       headers={"Idempotency-Key": key})

def test_partial_and_complete(client):
    first = refund(client)
    assert first.status_code == 201
    assert first.json() == {"payment_id": "p1", "amount": 300,
                            "refunded_total": 300, "status": "partially_refunded"}
    assert client.get("/payments/p1").json()["status"] == "partially_refunded"
    final = refund(client, 700, "request-2")
    assert final.status_code == 201
    assert final.json()["status"] == "refunded"
    assert final.json()["refunded_total"] == 1000
    payment = client.get("/payments/p1").json()
    assert payment["refunded"] == 1000 and payment["amount"] == 1000

def test_replay_preserves_original_response_even_after_final_refund(client):
    first = refund(client)
    assert first.status_code == 201
    assert refund(client, 700, "final").status_code == 201
    replay = refund(client)
    assert replay.status_code == 200 and replay.json() == first.json()
    assert client.get("/payments/p1").json()["refunded"] == 1000

@pytest.mark.parametrize("amount,payment", [(301, "p1"), (300, "p2")])
def test_conflicting_replay(client, amount, payment):
    assert refund(client).status_code == 201
    assert refund(client, amount, payment=payment).status_code == 409
    assert client.get("/payments/p1").json()["refunded"] == 300
    assert client.get("/payments/p2").json()["refunded"] == 0

@pytest.mark.parametrize("amount", [0, -1, 1.5, "10", True, None],
                         ids=["zero", "negative", "fraction", "numeric-string", "boolean", "null"])
def test_invalid_amount(client, amount):
    assert refund(client, amount).status_code == 422
    assert client.get("/payments/p1").json()["refunded"] == 0

@pytest.mark.parametrize("headers", [{}, {"Idempotency-Key": ""},
    {"Idempotency-Key": "x" * 65}, {"Idempotency-Key": "bad key"}])
def test_invalid_key(client, headers):
    assert client.post("/payments/p1/refunds", json={"amount": 1}, headers=headers).status_code == 422

def test_unknown_payment(client):
    assert refund(client, payment="missing").status_code == 404
    assert refund(client).status_code == 201

def test_invalid_business_state_and_failure_does_not_consume_key(client):
    assert refund(client, payment="p3").status_code == 409
    assert refund(client, 1001).status_code == 409
    assert refund(client).status_code == 201
    assert refund(client, 701, "second").status_code == 409
    assert refund(client, 700, "second").status_code == 201

def test_extra_fields_rejected(client):
    result = client.post("/payments/p1/refunds", json={"amount": 1, "admin": True},
                         headers={"Idempotency-Key": "extra"})
    assert result.status_code == 422

@pytest.mark.parametrize("amount", [1, 10])
def test_small_positive_integer_is_valid(client, amount):
    assert refund(client, amount).status_code == 201

def test_concurrent_duplicate_is_applied_once(client):
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: refund(client), range(4)))
    assert sorted(r.status_code for r in responses) == [200, 200, 200, 201]
    assert all(r.json() == responses[0].json() for r in responses)
    assert client.get("/payments/p1").json()["refunded"] == 300
"""
