from decimal import (
    Decimal,
)
import pytest

from pycountant.models import (
    GeneralLedgerLineItem,
)


@pytest.fixture
def defaults() -> dict:
    return {
        "account_code": "4000",
        "journal_number": "JN123",
        "net": "456.45",
        "effective": "2023-01-01",
        "created": "2023-01-01T12:00:00",
        "user": "test_user",
        "reference": "REF123",
        "line_description": "Test line item",
        "journal_description": "Test journal",
    }


@pytest.mark.parametrize(
    "input_value, expected",
    [
        (123, Decimal("123.00").quantize(Decimal("1.00"))),
        (123.123456, Decimal("123.12").quantize(Decimal("1.00"))),
        (123.7654, Decimal("123.77").quantize(Decimal("1.00"))),
    ],
)
def test_parsing_of_net(input_value, expected, defaults) -> None:
    # arrange
    defaults["net"] = input_value
    # act
    item = GeneralLedgerLineItem(**defaults)
    # assert
    assert item.net.value == expected
