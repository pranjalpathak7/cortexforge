"""Integer paise avoids floating-point money errors."""


def total(amounts: list[int]) -> int:
    if any(amount < 0 for amount in amounts):
        raise ValueError("Amounts must be nonnegative")
    return sum(amounts)

