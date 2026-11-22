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


@pytest.fixture
def fake_strategy(monkeypatch: pytest.MonkeyPatch):
    """Replace the provider with one that only knows the dates in ``rates``."""
    from pycountant.services import fx

    rates: dict[date, Decimal] = {}
    calls: list[date] = []

    def strategy(of: ISO4217, to: ISO4217, on: date) -> Decimal:
        calls.append(on)
        if on not in rates:
            raise ValueError(f"No rate found for '{to}' on {on.isoformat()}")
        return rates[on]

    monkeypatch.setattr(fx, "get_conversion_strategy", lambda *, using: strategy)
    fx.get_rate.cache_clear()
    yield rates, calls
    fx.get_rate.cache_clear()


@pytest.mark.parametrize(
    "on, published, expected_calls",
    [
        (date(2025, 9, 5), date(2025, 9, 5), [date(2025, 9, 5)]),  # Friday
        (date(2025, 9, 6), date(2025, 9, 5), [date(2025, 9, 6), date(2025, 9, 5)]),
        (
            date(2025, 9, 7),  # Sunday
            date(2025, 9, 5),
            [date(2025, 9, 7), date(2025, 9, 6), date(2025, 9, 5)],
        ),
    ],
)
def test_get_rate_falls_back_to_prior_days(
    fake_strategy,
    caplog: pytest.LogCaptureFixture,
    on: date,
    published: date,
    expected_calls: list[date],
) -> None:
    from pycountant.services.fx import get_rate

    rates, calls = fake_strategy
    rates[published] = Decimal("1.5")
    with caplog.at_level("WARNING", logger="pycountant.services.fx"):
        actual = get_rate(of="GBP", to="USD", on=on)
    assert actual == Decimal("1.5")
    assert calls == expected_calls
    assert len(caplog.records) == len(expected_calls) - 1
    for record, missing in zip(caplog.records, expected_calls, strict=False):
        assert missing.isoformat() in record.getMessage()


def test_get_rate_gives_up_after_two_prior_days(fake_strategy) -> None:
    from pycountant.services.fx import get_rate

    _, calls = fake_strategy
    with pytest.raises(ValueError, match="2025-09-04"):
        get_rate(of="GBP", to="USD", on=date(2025, 9, 6))
    assert calls == [date(2025, 9, 6), date(2025, 9, 5), date(2025, 9, 4)]
