from decimal import Decimal

import pytest

from pycountant.services import (
    add_tax,
    remove_tax,
)


@pytest.mark.parametrize(
    "to_value, at_rate, expected",
    [
        (Decimal("100"), Decimal("20"), Decimal("120")),
    ],
)
def test_add_tax(to_value, at_rate, expected) -> None:
    # arrange
    # act
    actual = add_tax(to_value=to_value, at_rate=at_rate)
    # assert
    assert actual == expected


@pytest.mark.parametrize(
    "from_value, at_rate, expected",
    [
        (Decimal("120"), Decimal("20"), Decimal("100")),
    ],
)
def test_remove_tax(from_value, at_rate, expected) -> None:
    # arrange
    # act
    actual = remove_tax(from_value=from_value, at_rate=at_rate)
    # assert
    assert actual == expected


@pytest.mark.parametrize(
    "func, kwargs, expected",
    [
        (add_tax, {"to_value": Decimal("100"), "at_rate": Decimal("20")}, "120"),
        (add_tax, {"to_value": Decimal("12.50"), "at_rate": Decimal("20")}, "15.00"),
        (remove_tax, {"from_value": Decimal("120"), "at_rate": Decimal("20")}, "100"),
        (remove_tax, {"from_value": Decimal("15.00"), "at_rate": Decimal("20")}, "12.50"),
    ],
)
def test_results_keep_the_input_precision_and_never_use_exponent_form(func, kwargs, expected) -> None:
    assert str(func(**kwargs)) == expected
