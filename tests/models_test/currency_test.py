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


@pytest.mark.parametrize(
    "currency, to, on, expected, accept_variance",
    [
        (
            Currency(value=Decimal("12340.00"), code="USD"),
            Currency(value=Decimal("11640.41"), code="EUR"),
            date(2023, 1, 5),
            True,
            Decimal("0.00"),
        ),
        (
            Currency(value=Decimal("12340.05"), code="USD"),
            Currency(value=Decimal("11640.41"), code="EUR"),
            date(2023, 1, 5),
            True,
            Decimal("0.05"),
        ),
        (
            Currency(value=Decimal("12340.01"), code="USD"),
            Currency(value=Decimal("11640.41"), code="EUR"),
            date(2023, 1, 5),
            False,
            Decimal("0.00"),
        ),
        (
            Currency(value=Decimal("52340.00"), code="USD"),
            Currency(value=Decimal("11640.41"), code="EUR"),
            date(2023, 1, 5),
            False,
            Decimal("0.00"),
        ),
    ],
)
def test_currency_is_equal_to(
    currency: Currency,
    to: Currency,
    on: date,
    expected: bool,
    accept_variance: Decimal,
) -> None:
    # arrange
    # act
    actual = currency.is_equal(
        to=to,
        on=on,
        accept_variance=accept_variance,
    )
    # assert
    assert actual is expected


@pytest.mark.parametrize(
    "currency, other, expected",
    [
        (
            Currency(value=Decimal("100.00"), code="EUR"),
            Currency(value=Decimal("86.95"), code="GBP"),
            True,
        ),
        (
            Currency(value=Decimal("500.00"), code="EUR"),
            Currency(value=Decimal("86.95"), code="GBP"),
            False,
        ),
    ],
)
def test_currency__eq__(
    currency: Currency,
    other: Currency,
    expected: bool,
) -> None:
    # arrange
    # act
    # assert
    assert (currency == other) is expected
