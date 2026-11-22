# Currency amounts

`Currency` is a [pydantic](https://docs.pydantic.dev/) model holding an amount
and its ISO 4217 currency code. It reads amounts the way they appear in ledgers,
invoices and spreadsheets, so you rarely need to clean them first.

```python
from pycountant.models import Currency

amount = Currency(value="$12.34k")
print(amount)        # 12,340.00 USD
amount.value         # Decimal('12340.00')
amount.code          # 'USD'
```

## Parsing amounts

`value` accepts a `str`, `int` or `Decimal`. Strings are cleaned before
validation:

| You pass | `value` | `code` | What happened |
|---|---|---|---|
| `"£1"` | `1.00` | `GBP` | symbol becomes the code |
| `"1,234.50"` | `1234.50` | `None` | thousands separators removed |
| `"(1,000)"` | `-1000.00` | `None` | brackets mean negative |
| `"(£1,000)"` | `-1000.00` | `GBP` | all of the above together |
| `"$12.34k"` | `12340.00` | `USD` | `k` = thousand |
| `"€2.5m"` | `2500000.00` | `EUR` | `m` = million |

The abbreviations are `k` (thousand), `m` (million), `b` (billion) and `t`
(trillion), lower case, as the last character.

The recognised symbols are `$` (USD), `£` (GBP), `€` (EUR), `¥` (JPY), `₹` (INR)
and `₽` (RUB). For anything else, pass the code.

### Setting the code

`code` takes any ISO 4217 code, or one of the symbols above:

```python
Currency(value="10", code="CHF")    # 10.00 CHF
Currency(value="10", code="£")      # 10.00 GBP
```

An explicit `code` wins over a symbol in the value. That matters for currencies
that share a symbol:

```python
Currency(value="$5", code="CAD")    # 5.00 CAD, not USD
```

`code` is optional, but an amount without one cannot be converted or compared.

### Rounding

Values are held to exactly two decimal places. Anything finer is rounded using
`Decimal`'s default, round-half-to-even (banker's rounding), so a run of halves
does not drift upwards:

```python
Currency(value="1,234.567")         # 1,234.57
Currency(value="0.125")             # 0.12
Currency(value="0.135")             # 0.14
```

!!! tip

    Pass amounts as `str` or `Decimal`, not `float`. `Currency(value=0.1)` is
    rounded correctly here, but the float has already lost precision before
    PyCountant sees it, and a calculation done in floats beforehand will not be.

### Validation

An unknown currency code, or a value that is not a number once cleaned
(`"abc"`, `"£"`), raises `pydantic.ValidationError`.

`Currency` is a pydantic model, so it can be used as a field in your own models:

```python
from pydantic import BaseModel

class Invoice(BaseModel):
    number: str
    total: Currency

Invoice(number="INV-001", total={"value": "£1,200"})
```

## Converting

`.convert()` changes the amount **in place** into another currency, at the rate
on a given past date, and returns `None`:

```python
from datetime import date

amount = Currency(value="£1")
amount.convert(to="USD", on=date(2025, 9, 5))
print(amount)                       # 1.35 USD
```

The result is rounded back to two decimal places. Copy the model first if you
need to keep the original:

```python
usd = amount.model_copy()
usd.convert(to="USD", on=date(2025, 9, 5))
```

Rates come from the European Central Bank by default. Pass `using="HMRC"` for
HMRC's monthly rates:

```python
amount.convert(to="EUR", on=date(2025, 3, 14), using="HMRC")
```

See [Exchange rates](fx.md) for how the providers differ, what happens on
weekends, and what needs a network connection.

## Comparing

Two amounts in different currencies are equal if they are worth the same on a
given date. `.is_equal()` converts this amount into the other's currency and
compares the two:

```python
from decimal import Decimal

gbp = Currency(value="£100")
eur = Currency(value="€118")

gbp.is_equal(to=eur, on=date(2025, 9, 5))                                # False
gbp.is_equal(to=eur, on=date(2025, 9, 5), accept_variance=Decimal("5"))  # True
```

`accept_variance` is an inclusive tolerance in the **other** amount's currency
(EUR above) — useful when reconciling figures converted with slightly different
rates or roundings.

`==` does the same with no variance, at **yesterday's** rate:

```python
gbp == eur                          # gbp.is_equal(to=eur, on=<yesterday>)
```

!!! warning

    `==` makes a network request for the rate, and its answer can change from
    one day to the next. Yesterday may also have no published rate yet, in
    which case it raises `ValueError` (see
    [Exchange rates](fx.md#weekends-and-holidays)). Both sides must be
    `Currency` instances with a code. Prefer `.is_equal()` with an explicit
    date in anything that must be reproducible.
