"""
Custom number types.
"""

from decimal import (
    Decimal,
    InvalidOperation,
)
from typing import (
    Annotated,
    Any,
)

from pydantic import (
    BeforeValidator,
)


def _to_two_places(value: Any) -> Decimal:
    # decimal.InvalidOperation is not a ValueError, so pydantic would let it
    # escape instead of reporting a ValidationError.
    try:
        return Decimal(value).quantize(Decimal("1.00"))
    except (InvalidOperation, TypeError) as error:
        raise ValueError(f"{value!r} is not a number") from error


# A Decimal with two decimal places.
Number = Annotated[
    Decimal,
    BeforeValidator(_to_two_places),
]
