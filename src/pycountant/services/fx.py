"""
Foreign exchange services.
"""

from datetime import (
    date,
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
    eur_to_eur_rate = Decimal("1.0")
    return (eur_to_eur_rate / of_rate) / (eur_to_eur_rate / to_rate)


@cache
def convert(
    value: Decimal,
    of: ISO4217,
    to: ISO4217,
    on: PastDate,
    using: FxProviderStr,
) -> Decimal:
    """
    Convert a value from one currency to another.

    Args:
        value (Decimal): The value to convert.
        of (ISO4217): Currency code to convert from.
        to (ISO4217): Currency code to convert to.
        on (PastDate): Date to get the rate for.
        using (FxProviderStr): The FX provider to use.

    Raises:
        NotImplementedError: When the given FX provider is not supported.

    Returns:
        Decimal: The converted value.
    """
    strategies: dict[
        FxProviderStr,
        Callable[[ISO4217, ISO4217, date], Decimal],
    ] = {
        "European Central Bank": get_rate_via_ecb,
    }
    strategy = strategies.get(using)
    if strategy is None:
        raise NotImplementedError(
            f"Currently only '{','.join(strategies)}' is supported, not '{using}'",
        )
    rate = strategy(of, to, on)
    return value * rate
