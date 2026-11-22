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
        to_value (Decimal): Amount to add tax to.
        at_rate (Decimal): Rate (percentage) to add tax at.
                           20% should be written as Decimal("20")

    Returns:
        Decimal: The amount with tax added, unrounded.
                 Exact results keep the precision of ``to_value``.
    """
    # Scale by (100 + rate) / 100 rather than (1 + rate / 100): the result then
    # keeps the precision of to_value (12.50 -> 15.00), never "1.2E+2".
    hundred = Decimal("100")
    return to_value * (hundred + at_rate) / hundred


@cache
def remove_tax(*, from_value: Decimal, at_rate: Decimal) -> Decimal:
    """
    Remove tax from a value.

    Args:
        from_value (Decimal): Amount to remove tax from.
        at_rate (Decimal): Rate (percentage) to remove tax at.
                           20% should be written as Decimal("20")

    Returns:
        Decimal: The amount with tax removed, unrounded.
                 Exact results keep the precision of ``from_value``.
    """
    # See add_tax: keeps the precision of from_value, never "1.0E+2".
    hundred = Decimal("100")
    return from_value * hundred / (hundred + at_rate)
