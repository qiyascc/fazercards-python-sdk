from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Optional, Union

from .errors import InvalidRequestError
from .messages import text

Amount = Union[Decimal, int, float, str]

CENT = Decimal("0.01")


def parse(value: Any) -> Optional[Decimal]:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def amount(value: Amount, field: str = "amount") -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
        raise InvalidRequestError(text("value.amount_type", field=field, value=value))
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise InvalidRequestError(text("value.amount_type", field=field, value=value)) from None
    if not result.is_finite():
        raise InvalidRequestError(text("value.amount_finite", field=field, value=value))
    if result <= 0:
        raise InvalidRequestError(text("value.amount_positive", field=field, value=value))
    if result != result.quantize(CENT):
        raise InvalidRequestError(text("value.amount_scale", field=field, value=value))
    return result


def wire(value: Decimal) -> str:
    return format(value.quantize(CENT), "f")
