from datetime import (
    date,
)
from decimal import (
    Decimal,
)
from typing import (
    Literal,
)

import pytest
from pydantic_extra_types.currency_code import (
    ISO4217,
)

from pycountant.services import (
    convert,
)

@pytest.mark.parametrize(
    "value, of, to, on, using, expected",
    [
        (Decimal("10000"), "EUR", "USD", date(2025, 9, 2), "European Central Bank", Decimal("11646.00")),
        (Decimal("11646"), "USD", "EUR", date(2025, 9, 2), "European Central Bank", Decimal("10000.00")),
        (Decimal("10000"), "GBP", "USD", date(2025, 9, 2), "European Central Bank", Decimal("13383.13")),
        (Decimal("87309.67"), "CZK", "THB", date(2025, 9, 2), "European Central Bank", Decimal("134446.55")),
    ],
)
def test_convert(value: Decimal, of: ISO4217, to: ISO4217, on: date, using: Literal["European Central Bank"], expected: Decimal) -> None:
    # arrange
    # act
    actual = convert(value=value, of=of, to=to, on=on, using=using)
    # assert
    assert actual.quantize(Decimal("1.00")) == expected
