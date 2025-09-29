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
