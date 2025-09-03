from decimal import (
    Decimal,
)
from typing import (
    Annotated,
)

from pydantic import (
    BeforeValidator,
)

Number = Annotated[
    Decimal,
    BeforeValidator(lambda v: Decimal(v).quantize(Decimal("1.00"))),
]
