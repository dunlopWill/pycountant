"""
Custom number types.
"""

from decimal import (
    Decimal,
)
from typing import (
    Annotated,
)

from pydantic import (
    BeforeValidator,
)

# A Decimal with two decimal places.
Number = Annotated[
    Decimal,
    BeforeValidator(lambda v: Decimal(v).quantize(Decimal("1.00"))),
]
