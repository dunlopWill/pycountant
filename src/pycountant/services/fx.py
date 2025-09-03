from datetime import (
    date,
    timedelta,
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
    ProviderStr,
)


def get_rate_via_ecb(value: Decimal, of: ISO4217, to: ISO4217, on: PastDate) -> Decimal:
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
    content = str(httpx.get(url).content)
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
    using: ProviderStr = "European Central Bank"
    if of_rate is None:
        raise ValueError(
            f"No rate found for '{of}' on {on.isoformat()} using '{using}'",
        )
    if to_rate is None:
        raise ValueError(
            f"No rate found for '{to}' on {on.isoformat()} using '{using}'",
        )
    EUR_TO_EUR_RATE = Decimal("1.0")
    return (EUR_TO_EUR_RATE / of_rate) / (EUR_TO_EUR_RATE / to_rate)


@cache
def convert(
    value: Decimal,
    of: ISO4217,
    to: ISO4217,
    on: PastDate,
    using: ProviderStr,
) -> Decimal:
    strategies: dict[
        ProviderStr,
        Callable[[Decimal, ISO4217, ISO4217, date], Decimal],
    ] = {
        "European Central Bank": get_rate_via_ecb,
        # TODO HMRC https://developer.service.hmrc.gov.uk/api-documentation/docs/api/xml/Exchange%20rates%20from%20HMRC
    }
    strategy = strategies.get(using)
    if strategy is None:
        raise NotImplementedError(
            f"Currently only '{','.join(strategies)}' is supported, not '{using}'",
        )
    rate = strategy(value, of, to, on)
    return value * rate


if __name__ == "__main__":
    print(
        convert(
            value=Decimal("100"),
            of="USD",
            to="GBP",
            on=date.today() - timedelta(days=1),
            using="European Central Bank",
        ),
    )
