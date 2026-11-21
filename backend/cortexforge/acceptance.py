"""Trusted evaluation oracle for the explicitly supported payments demonstration."""

PAYMENTS_ORACLE = """import pytest
from payments import apply_discount, total

@pytest.mark.parametrize("amount,percent,expected", [
    (0, 0, 0), (0, 100, 0), (100, 0, 100), (100, 100, 0),
    (101, 50, 50), (999, 33, 669), (1, 99, 0), (1000000, 10, 900000),
])
def test_trusted_discount(amount, percent, expected):
    assert apply_discount(amount, percent) == expected

@pytest.mark.parametrize("amount,percent", [(-1, 10), (100, -1), (100, 101)])
def test_trusted_invalid(amount, percent):
    with pytest.raises(ValueError):
        apply_discount(amount, percent)

def test_trusted_total_regression():
    assert total([100, 250]) == 350
    assert total([]) == 0
    with pytest.raises(ValueError):
        total([-1])
"""
