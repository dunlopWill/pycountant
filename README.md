# pycountant

[![CI](https://github.com/dunlopWill/pycountant/actions/workflows/ci.yml/badge.svg)](https://github.com/dunlopWill/pycountant/actions/workflows/ci.yml)
[![pypi](https://img.shields.io/pypi/v/pycountant.svg)](https://pypi.python.org/pypi/pycountant)
[![Python versions](https://img.shields.io/pypi/pyversions/pycountant.svg)](https://pypi.org/project/pycountant/)
[![downloads](https://static.pepy.tech/badge/pycountant)](https://pepy.tech/project/pycountant)

Python package for accountants.

## Help

See [documentation](https://pycountant.com) for more details.

## Installation

Install with uv:

```bash
uv add pycountant
```

or with pip:

```bash
pip install pycountant
```

## Example

### Currency amounts

Parse amounts the way accountants write them, and convert them at historical
European Central Bank or HMRC rates:

```python
from datetime import date

from pycountant.models import Currency

Currency(value="(£1,250)")      # -1,250.00 GBP
Currency(value="$12.34k")       # 12,340.00 USD

pound = Currency(value="£1")
pound.convert(to="USD", on=date(2025, 9, 5))   # converts in place, returns None
print(pound)
# 1.35 USD
```

### Tax

```python
from decimal import Decimal

from pycountant.services import add_tax, remove_tax

add_tax(to_value=Decimal("100"), at_rate=Decimal("20"))       # Decimal('120')
remove_tax(from_value=Decimal("120"), at_rate=Decimal("20"))  # Decimal('100')
```

### Excel formulas

Build live Excel formulas with Python operators and write them through openpyxl:

```python
from pycountant.excel import Sheet, F

s = Sheet(ws)
rev  = s.put("B2", 1000)                 # writes the value, hands back the ref
cost = s.put("B3", 600)

s.put("B4", (rev - cost) / rev)          # =(B2-B3)/B2
s.put("B5", F.IF(rev.gt(cost), "profit", "loss"))
```

See the [Excel formulas guide](https://pycountant.com/excel/) for more.

## Development

```bash
uv sync
just check                # ruff, pyright, ty, pytest
just fast                 # skip the LibreOffice recalculation tests
just recalc               # only those (needs `soffice` on PATH)
just docs-serve           # preview the docs at http://localhost:8000
```

`just check` is the gate CI runs. See [CONTRIBUTING.md](CONTRIBUTING.md) and
[CLAUDE.md](CLAUDE.md).

## License

MIT — see [LICENSE](LICENSE).
