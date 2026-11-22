# Excel formulas

Build Excel formulas with Python operators, then hand them straight to openpyxl.

```python
from pycountant.excel import Sheet, F

s = Sheet(ws)
rev  = s.put("B2", 1000)                 # writes the value, hands back the ref
cost = s.put("B3", 600)

s.put("B4", rev - cost)                  # =B2-B3
s.put("B5", (rev - cost) / rev)          # =(B2-B3)/B2
s.put("B6", F.IF(rev.gt(cost), "profit", "loss"))
```

No tracking which cell a value went to, no `f"={a}-{b}"` string assembly, and no
guessing about parentheses.

## Why

Four problems, in the order they actually bite.

**1. Coordinates drift.** Hand-written formulas name cells twice — once where the
value is written, once where it is referenced — and nothing connects the two:

```python
ws["B2"] = 1000
ws["B3"] = 600
ws["B4"] = "=B2-B3"
ws["B5"] = "=(B2-B3)/B2"
```

Insert one header row at the top of the generating code and every string below is
quietly pointing at the wrong cell. `s.put()` returns a reference to where the value
actually landed, so the coordinate is written once and never typed again. This is the
one that costs you time on an ordinary Tuesday.

**2. Functions added in Excel 2010 or later need a prefix you have never heard of.** The
file format stores them as `_xlfn.XLOOKUP`, `_xlfn.TEXTJOIN`, `_xlfn._xlws.FILTER`.
Write `=XLOOKUP(...)` bare through openpyxl and the workbook opens showing `#NAME?`,
with no error at write time and no hint as to why. `F.XLOOKUP(...)` emits the
prefixed form automatically — you write the plain name.

**3. Precedence goes wrong silently.** The obvious version of "just concatenate the
coordinates" turns `(revenue - cost) / revenue` into `=B3-B4/B3` — a wrong number,
not an error. `pycountant.excel` builds a small expression tree and renders it with Excel's
precedence rules, so the parentheses are right and there are no redundant ones.

It handles two places where Python and Excel genuinely disagree:

| You write | Python means | Excel would read | pycountant emits |
|---|---|---|---|
| `a ** b ** c` | `a ** (b ** c)` | `^` is left-associative | `a^(b^c)` |
| `-a ** 2` | `-(a ** 2)` | unary `-` binds tighter than `^` | `-(a^2)` |

**4. You have to open Excel to remember the arguments.** Does `SUMIFS` take the sum
range first or last? First — unlike `SUMIF`, which takes it last. A formula written
as a string gives your editor nothing to work with, so answering that usually means
a scratch workbook open on the other monitor.

`F.` is an ordinary attribute lookup, so your editor completes it. 263 Excel
function names are known to it, and the 85 you reach for most carry full signatures,
so the argument names and order show up as you type:

```python
F.SUMIF(rng("A:A"), ">5", rng("B:B"))     # range, criteria, sum_range
F.SUMIFS(rng("B:B"), rng("A:A"), ">5")    # sum_range, criteria_range, criteria
```

Pass the wrong number and it is flagged in the editor, before you run anything and
long before Excel would have shown you a `#VALUE!`. The formula gets written where
you are already working, with the reference material inline. See
[Validation](validation.md) for what is checked and when, and
[Usage](usage.md#discovering-functions) for browsing what is available.

## Is this for you?

If you are writing computed **values** into a spreadsheet — `df.to_excel(...)` and
friends — you need none of this. No formula ever appears, so none of the above can
go wrong.

This is for workbooks that must contain **live formulas**, because a human will open
the file and change the inputs: financial models, budget templates, audit
deliverables, anything where "the numbers recalculate" is the point.

## Where next

- **[Usage](usage.md)** — writing values, references, operators, functions
- **[Validation](validation.md)** — what is checked, when, and what nothing can check
- **[API Reference](../reference/pycountant/excel/index.md)** — every public name, generated from the source
