# Tax

Two helpers for percentage-based taxes such as VAT or GST: one grosses up a net
amount, the other extracts the net amount from a gross one.

```python
from decimal import Decimal
from pycountant.services import add_tax, remove_tax

add_tax(to_value=Decimal("100"), at_rate=Decimal("20"))        # Decimal('120')
remove_tax(from_value=Decimal("120"), at_rate=Decimal("20"))   # Decimal('100')
```

The rate is a **percentage**: 20% is `Decimal("20")`, not `Decimal("0.2")`.

## Removing tax is not subtracting the rate

`remove_tax` divides by `1 + rate`, which is what you need to reverse `add_tax`.
Taking 20% off £120 gives £96, not the £100 you started with:

```python
remove_tax(from_value=Decimal("120"), at_rate=Decimal("20"))   # 100
Decimal("120") * (1 - Decimal("0.20"))                         # 96.00 — wrong
```

The tax element is the difference:

```python
gross = Decimal("120")
net = remove_tax(from_value=gross, at_rate=Decimal("20"))
tax = gross - net                                              # 20
```

## Rounding

When the answer is exact, it keeps the precision you passed in:

```python
add_tax(to_value=Decimal("12.50"), at_rate=Decimal("20"))      # Decimal('15.00')
```

When it is not, the result is left unrounded. Quantise to the precision you
report in:

```python
net = remove_tax(from_value=Decimal("100"), at_rate=Decimal("20"))
net                            # Decimal('83.33333333333333333333333333')
net.quantize(Decimal("0.01"))  # Decimal('83.33')
```

Tax authorities differ on whether tax is rounded per line or per invoice, so
PyCountant leaves that decision to you.
