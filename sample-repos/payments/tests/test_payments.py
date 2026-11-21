import pytest

from payments import total


def test_total():
    assert total([100, 250]) == 350
    assert total([]) == 0


def test_negative():
    with pytest.raises(ValueError):
        total([-1])

