"""Explicit missingness and strict numerical validation (DD-03, DD-67)."""

from decimal import Decimal
from enum import Enum


class MissingReason(Enum):
    """Missing evidence is not a numeric zero or an observed absence of trades."""

    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


type NumericValue = Decimal | MissingReason


def require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be nonempty text without surrounding whitespace")


def require_numeric(value: NumericValue, field: str, *, quantity: bool = False) -> None:
    if isinstance(value, MissingReason):
        return
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{field} must be a finite Decimal or explicit MissingReason")
    if quantity and value < 0:
        raise ValueError(f"{field} must not be negative")
