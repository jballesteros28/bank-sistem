from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def normalize_decimal(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalize_email(value: str) -> str:
    return value.strip().lower()

