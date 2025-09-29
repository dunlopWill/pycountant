from datetime import (
    date,
    datetime,
)
from decimal import (
    Decimal,
)

import pytest
from pydantic_extra_types.currency_code import (
    ISO4217,
)

from pycountant.extra_types import (
    FxProviderStr,
)
from pycountant.services import (
    convert,
)


@pytest.mark.parametrize(
    "value, of, to, on, using, expected",
    [
        (
            Decimal("10000"),
            "EUR",
            "USD",
            date(2025, 9, 2),
            "European Central Bank",
            Decimal("11646.00"),
        ),
        (
            Decimal("11646"),
            "USD",
            "EUR",
            date(2025, 9, 2),
            "European Central Bank",
            Decimal("10000.00"),
        ),
        (
            Decimal("10000"),
            "GBP",
            "USD",
            date(2025, 9, 2),
            "European Central Bank",
            Decimal("13383.13"),
        ),
        (
            Decimal("87309.67"),
            "CZK",
            "THB",
            date(2025, 9, 2),
            "European Central Bank",
            Decimal("134446.55"),
        ),
        (
            Decimal("87309.67"),
            "CZK",
            "THB",
            datetime(2025, 9, 2),
            "European Central Bank",
            Decimal("134446.55"),
        ),
        (
            Decimal("100.00"),
            "GBP",
            "USD",
            datetime(2024, 10, 31),
            "HMRC",
            Decimal("132.11"),  # 1.3211 * 100
        ),
    ],
)
def test_convert(
    value: Decimal,
    of: ISO4217,
    to: ISO4217,
    on: date,
    using: FxProviderStr,
    expected: Decimal,
) -> None:
    # arrange
    # act
    actual = convert(value=value, of=of, to=to, on=on, using=using)
    # assert
    assert actual.quantize(Decimal("1.00")) == expected
