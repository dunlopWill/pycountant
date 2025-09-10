from datetime import (
    date,
)
from decimal import (
    Decimal,
)

import pytest

from pycountant.models import (
    Currency,
)


@pytest.mark.parametrize(
    "context, expected_value, expected_code",
    [
        (
            {"value": "$100.12"},
            Decimal("100.12").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "-$100.12"},
            Decimal("-100.12").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "$-100.12"},
            Decimal("-100.12").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "100.12$"},
            Decimal("100.12").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "   £   100.12   "},
            Decimal("100.12").quantize(Decimal("1.00")),
            "GBP",
        ),
        (
            {"value": "100.12", "code": "USD"},
            Decimal("100.12").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "100.12", "code": "$"},
            Decimal("100.12").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "100.12", "code": "£"},
            Decimal("100.12").quantize(Decimal("1.00")),
            "GBP",
        ),
        (
            {"value": 100.1200001, "code": "EUR"},
            Decimal("100.12").quantize(Decimal("1.00")),
            "EUR",
        ),
        (
            {"value": "$100.12", "code": "CAD"},
            Decimal("100.12").quantize(Decimal("1.00")),
            "CAD",
        ),
        (
            {"value": -100, "code": "EUR"},
            Decimal("-100.00").quantize(Decimal("1.00")),
            "EUR",
        ),
        (
            {"value": "(100.12)", "code": "USD"},
            Decimal("-100.12").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "1,123,456.12", "code": "USD"},
            Decimal("1123456.12").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "£10k", "code": "USD"},
            Decimal("10000").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "10.2m", "code": "USD"},
            Decimal("10200000").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "10.2m", "code": "$"},
            Decimal("10200000").quantize(Decimal("1.00")),
            "USD",
        ),
        (
            {"value": "$10.2m", "code": "$"},
            Decimal("10200000").quantize(Decimal("1.00")),
            "USD",
        ),
    ],
)
def test_currency(context, expected_value, expected_code) -> None:
    # arrange
    # act
    item = Currency(**context)
    # assert
    assert item.value == expected_value
    assert item.code == expected_code


@pytest.mark.parametrize(
    "value, code, to, expected",
    [
        (
            "87309.67",
            "CZK",
            "THB",
            Decimal("134446.55"),
        ),
    ],
)
def test_currency_convert(value, code, to, expected) -> None:
    # arrange
    item = Currency(value=value, code=code)  # type: ignore[arg-type]
    # act
    item.convert(
        to=to,  # type: ignore[arg-type]
        on=date(2025, 9, 2),
        using="European Central Bank",  # type: ignore[arg-type]
    )
    # assert
    assert item.code == to
    assert item.value == expected
