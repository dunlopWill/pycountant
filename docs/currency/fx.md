# Exchange rates

PyCountant converts between currencies at historical rates published by an
official source, so a figure can be traced back to where its rate came from.

## Converting a value

[`Currency.convert()`](index.md#converting) is the usual entry point. To work
with bare `Decimal` values instead, use `convert()`:

```python
from datetime import date
from decimal import Decimal
from pycountant.services import convert

convert(value=Decimal("12340"), of="USD", to="EUR", on=date(2023, 1, 5))
# Decimal('11640.41128195453259126497500')
```

Unlike `Currency.convert()`, the result is **not** rounded — quantise it when you
are ready:

```python
result.quantize(Decimal("0.01"))    # Decimal('11640.41')
```

To get the rate itself:

```python
from pycountant.services.fx import get_rate

get_rate(of="GBP", to="EUR", on=date(2025, 9, 5))
# Decimal('1.152339248674809864023968656')
```

All arguments are keyword-only. `of` and `to` are ISO 4217 codes; `on` is a
`date` (a `datetime` is accepted and its time ignored).

## Providers

Choose a provider with `using=`. The default is the European Central Bank.

| `using=` | Rates | Published | Covers |
|---|---|---|---|
| `"European Central Bank"` | daily euro reference rates | each TARGET working day, around 16:00 CET | about 30 major currencies |
| `"HMRC"` | monthly exchange rates | once a month, for the whole month | most world currencies |

```python
convert(value=Decimal("100"), of="USD", to="GBP", on=date(2025, 3, 14), using="HMRC")
```

**European Central Bank** rates are quoted against the euro. A conversion that
involves neither EUR side is made by crossing through the euro: USD → GBP uses
the EUR/USD and EUR/GBP rates for that day.

**HMRC** rates are quoted against sterling and are the ones HMRC expects for UK
customs and VAT purposes. They are fixed for a calendar month, so every date in
March 2025 returns the same rate.

Any other value for `using` raises `NotImplementedError`. The supported names are
also available as the `pycountant.extra_types.FxProviderStr` type, for annotating
your own code.

## Weekends and holidays

The ECB publishes nothing on weekends or TARGET holidays. When no rate exists on
the requested date, PyCountant logs a warning and tries the day before, up to two
days earlier (`MAX_FALLBACK_DAYS`):

```python
amount = Currency(value="£100")
amount.convert(to="EUR", on=date(2025, 9, 6))     # a Saturday
# WARNING No rate found for 'GBP' on 2025-09-06 using European Central Bank;
#         trying 2025-09-05 instead
print(amount)                                     # 115.23 EUR
```

That covers an ordinary weekend. A longer gap — Good Friday to Easter Monday, or
a date before today's rates are published — raises `ValueError`, as does a
currency the provider does not quote:

```text
ValueError: No rate found for 'USD' on 2029-12-30 using European Central Bank
```

The warnings go through the standard `logging` module under the
`pycountant.services.fx` logger, so you can silence or capture them there.

## Network access and caching

Every rate is fetched live — there is no bundled data:

- the ECB provider downloads the ECB's full rate history (several megabytes);
- the HMRC provider calls the UK Trade Tariff API for the requested month.

Both need an internet connection, and a lookup fails if the provider is
unreachable.

Lookups are cached in memory for the life of the process, so asking for the same
pair on the same date again costs nothing. A different date or pair makes a new
request, so converting many rows at many dates in one go is slow with the ECB
provider. The cache is not persisted between runs.
