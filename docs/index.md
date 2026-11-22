# PyCountant

PyCountant brings the domain knowledge of accounting to Python, enabling
professionals to focus on solving problems fast.

## Installation

=== "uv"

    ```bash
    uv add pycountant
    ```

=== "pip"

    ```bash
    pip install pycountant
    ```

Requires Python 3.13 or later.

## What it does

### Currency amounts

Parse amounts the way accountants write them — symbols, thousands separators,
`k`/`m` abbreviations and bracketed negatives — into an exact two-decimal value
with an ISO 4217 code.

```python
from pycountant.models import Currency

Currency(value="£1,250")       # 1,250.00 GBP
Currency(value="$12.34k")      # 12,340.00 USD
Currency(value="(€1,000)")     # -1,000.00 EUR
```

[Currency amounts →](currency/index.md)

### Exchange rates

Convert between currencies at the historical rate published by the European
Central Bank (daily) or HMRC (monthly).

```python
from datetime import date

amount = Currency(value="£100")
amount.convert(to="EUR", on=date(2025, 9, 5))
print(amount)                  # 115.23 EUR
```

[Exchange rates →](currency/fx.md)

### Tax

Gross up a net amount, or strip the tax back out of a gross one.

```python
from decimal import Decimal
from pycountant.services import add_tax, remove_tax

add_tax(to_value=Decimal("100"), at_rate=Decimal("20"))       # 120
remove_tax(from_value=Decimal("120"), at_rate=Decimal("20"))  # 100
```

[Tax →](tax.md)

### Excel formulas

Build live Excel formulas with Python operators and write them straight to
openpyxl cells, with Excel's precedence rules and file-format quirks handled for
you.

```python
from pycountant.excel import Sheet, F

s = Sheet(ws)
rev  = s.put("B2", 1000)                 # writes the value, hands back the ref
cost = s.put("B3", 600)

s.put("B4", (rev - cost) / rev)          # =(B2-B3)/B2
s.put("B5", F.IF(rev.gt(cost), "profit", "loss"))
```

[Excel formulas →](excel/index.md)

## Money is `Decimal`

Every amount and rate in PyCountant is a
[`Decimal`](https://docs.python.org/3/library/decimal.html), never a `float`, so
`0.1 + 0.2` is `0.3` and totals reconcile to the penny. Pass `Decimal` or `str`
values in; you get `Decimal` values out.
