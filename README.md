# pycountant

[![pypi](https://img.shields.io/pypi/v/pycountant.svg)](https://pypi.python.org/pypi/pycountant)
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

```python
from pycountant.models import Currency

pound = Currency(value="£1")

print(pound)
# 1.00 GBP

pound.convert(to="USD" on=date(2025, 9, 5))
# Currency(value=Decimal('1.35'), code='USD')
```
