"""
Tax services.
"""

from decimal import Decimal
from functools import cache


@cache
def add_tax(*, to_value: Decimal, at_rate: Decimal) -> Decimal:
    """
    Add tax to a value.

    Args:
        to (Decimal): Amount to add tax to.
        at_rate (Decimal): Rate (percentage) to add tax at.
                           20% should be written as Decimal("20")

    Returns:
        Decimal: The amount with tax added.
    """
    base_rate = Decimal("1.0")
    return to_value * (base_rate + (at_rate / Decimal("100")))


@cache
def remove_tax(*, from_value: Decimal, at_rate: Decimal) -> Decimal:
    """
    Remove tax from a value.

    Args:
        to (Decimal): Amount to remove tax from.
        at_rate (Decimal): Rate (percentage) to remove tax at.
                           20% should be written as Decimal("20")

    Returns:
        Decimal: The amount with tax removed.
    """
    base_rate = Decimal("1.0")
    return from_value / (base_rate + (at_rate / Decimal(100)))
