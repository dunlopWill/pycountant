"""
Foreign exchange services.
"""

from datetime import (
    date,
    datetime,
)
from decimal import (
    Decimal,
)
from functools import (
    cache,
)
from typing import (
    Callable,
)
from xml.etree import (
    ElementTree,
)

import httpx
from pydantic import (
    PastDate,
)
from pydantic_extra_types.currency_code import (
    ISO4217,
)

from ..extra_types import (
    FxProviderStr,
)


@cache
def get_rate_from_base(of_rate: Decimal, to_rate: Decimal) -> Decimal:
    base_rate = Decimal("1.0")
    return (base_rate / of_rate) / (base_rate / to_rate)


@cache
def get_rate_via_ecb(of: ISO4217, to: ISO4217, on: PastDate) -> Decimal:
    """
    Get FX rate via European Central Bank.

    Args:
        of (ISO4217): Currency code to convert from.
        to (ISO4217): Currency code to convert to.
        on (PastDate): Date to get the rate for.

    Raises:
        ValueError: When no rate is found for the given currencies on the given date.

    Returns:
        Decimal: The FX rate.
    """
    content = str(
        httpx.get(
            "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml",
        ).content,
    )
    start = content.find("<Cube>")
    end = content.find("</gesmes:Envelope>")
    tree = ElementTree.fromstring(content[start:end])
    # Filter by date
    of_rate = None if of != "EUR" else Decimal("1.0")
    to_rate = None if to != "EUR" else Decimal("1.0")
    date_cubes = [
        cube
        for cube in tree.findall("Cube")
        if cube.attrib.get("time") == on.isoformat()
    ]  # and cube.attrib.get("currency") == to]
    for date_cube in date_cubes:
        for cube in date_cube.findall("Cube"):
            # Gets rates against EUR
            if cube.attrib.get("currency") == of:
                _of_rate = cube.attrib.get("rate")
                if _of_rate:
                    of_rate = Decimal(_of_rate)
                    continue
            if cube.attrib.get("currency") == to:
                _to_rate = cube.attrib.get("rate")
                if _to_rate:
                    to_rate = Decimal(_to_rate)
                    continue
    if of_rate is None:
        raise ValueError(
            f"No rate found for '{of}' on {on.isoformat()} using European Central Bank",
        )
    if to_rate is None:
        raise ValueError(
            f"No rate found for '{to}' on {on.isoformat()} using European Central Bank",
        )
    return get_rate_from_base(of_rate=of_rate, to_rate=to_rate)


@cache
def get_rate_via_hmrc(of: ISO4217, to: ISO4217, on: PastDate) -> Decimal:
    # https://api.trade-tariff.service.gov.uk/reference.html#get-exchange-rates-year-month
    url = f"https://www.trade-tariff.service.gov.uk/uk/api/exchange_rates/{on.year}-{on.month}?filter[type]=monthly"
    response = httpx.get(url=url)
    content = response.json()
    of_rate = None if of != "GBP" else Decimal("1.0")
    to_rate = None if to != "GBP" else Decimal("1.0")
    if not to_rate:
        to_rate = [
            item.get("attributes").get("rate")
            for item in content.get("included")
            if item.get("attributes").get("currency_code") == to
        ]
        if to_rate:
            to_rate = to_rate[0]
    if not of_rate:
        of_rate = [
            item.get("attributes").get("rate")
            for item in content.get("included")
            if item.get("attributes").get("currency_code") == of
        ]
        if of_rate:
            of_rate = of_rate[0]
    if of_rate is None:
        raise ValueError(
            f"No rate found for '{of}' on {on.isoformat()} using HMRC",
        )
    if to_rate is None:
        raise ValueError(
            f"No rate found for '{to}' on {on.isoformat()} using HMRC",
        )
    return get_rate_from_base(of_rate=Decimal(of_rate), to_rate=Decimal(to_rate))


def get_conversion_strategy(
    *,
    using: FxProviderStr,
) -> Callable[[ISO4217, ISO4217, date], Decimal]:
    """
    Get the conversion strategy for a particular provider.

    Args:
        using (FxProviderStr): The provider.

    Raises:
        NotImplementedError: Error raised if no strategy exists for that provider.

    Returns:
        Callable[[ISO4217, ISO4217, date], Decimal]: A strategy to obtain the rate for conversion with.
    """
    strategies: dict[
        FxProviderStr,
        Callable[[ISO4217, ISO4217, date], Decimal],
    ] = {
        "European Central Bank": get_rate_via_ecb,
        "HMRC": get_rate_via_hmrc,
    }
    strategy = strategies.get(using)
    if strategy is None:
        raise NotImplementedError(
            f"Currently only '{','.join(strategies)}' is supported, not '{using}'",
        )
    return strategy


@cache
def get_rate(
    *,
    of: ISO4217,
    to: ISO4217,
    on: PastDate,
    using: FxProviderStr = "European Central Bank",
):
    """
    Get the rate to convert one currency to another on a past date.

    Args:
        of (ISO4217): Currency code to convert from.
        to (ISO4217): Currency code to convert to.
        on (PastDate): Date to get the rate for.
        using (FxProviderStr): The FX provider to use. Defaults to "European Central Bank"

    Raises:
        NotImplementedError: When the given FX provider is not supported.

    Returns:
        Decimal: The rate

    !!! warning

        If the *on* PastDate does not fall on a weekday (Monday to Friday),
        then it will not be possible to obtain a rate for conversion.

    !!! failure

        If there is no internet connection, it will not be possible to make
        the relevant API call to obtain the rate for conversion.

    """
    strategy = get_conversion_strategy(using=using)
    if isinstance(on, datetime):
        on = on.date()  # Don't need time info
    return strategy(of, to, on)


@cache
def convert(
    *,
    value: Decimal,
    of: ISO4217,
    to: ISO4217,
    on: PastDate,
    using: FxProviderStr = "European Central Bank",
) -> Decimal:
    """
    Convert a value from one currency to another.

    Args:
        value (Decimal): The value to convert.
        of (ISO4217): Currency code to convert from.
        to (ISO4217): Currency code to convert to.
        on (PastDate): Date to get the rate for.
        using (FxProviderStr): The FX provider to use. Defaults to "European Central Bank"

    Raises:
        NotImplementedError: When the given FX provider is not supported.

    Returns:
        Decimal: The converted value.

    Examples:

        >>> from pycountant.services.fx import convert
        >>> print(
        ...     convert(value=Decimal("12340"), of="USD", to="EUR", on=date(2023, 1, 5))
        ... )
        11640.41128195453259126497500

    !!! warning

        If the *on* PastDate does not fall on a weekday (Monday to Friday),
        then it will not be possible to obtain a rate for conversion.

    !!! failure

        If there is no internet connection, it will not be possible to make
        the relevant API call to obtain the rate for conversion.

    """
    rate = get_rate(of=of, to=to, on=on, using=using)
    return value * rate


if __name__ == "__main__":
    import doctest

    doctest.testmod()
