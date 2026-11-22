# Usage

## Writing values

`Sheet` wraps an openpyxl worksheet so a write hands back a reference:

```python
s = Sheet(ws)
rev = s.put("B2", 1000)          # or s.put(2, 2, 1000)
s.put("B4", rev * 1.2)           # =B2*1.2
```

It holds no state beyond the worksheet, and `s.ws` is the plain openpyxl object
whenever you want it. Formatting passes straight through — `number_format` plus any
keyword you could set on a cell:

```python
s.put("B5", margin, number_format="0.0%", font=Font(bold=True))
```

References come back **unqualified**, because most formulas stay on one sheet. When
one crosses sheets, `.qualified()` fills in the sheet name so you don't retype it:

```python
rev = Sheet(source).put("B2", 1000)
summary["A1"] = rev.qualified() * 2      # ='Source Data'!B2*2
```

`s["B2"]`, `s["A1:A9"]` and `s.cell(2, 2)` give references without writing anything.
`s.span(top, bottom)` and `s.column(rev)` build ranges from references you already
have.

## References

```python
cell("B3")                       # B3
cell(3, 2)                       # B3           -- (row, col), 1-based
cell("B3").abs()                 # $B$3         -- also .abs_r() / .abs_c() / .rel()
cell("B3").offset(rows=2)        # B5
cell("B3").to(cell("D5"))        # B3:D5

rng("B3:B10")                    # B3:B10
rng("A:A")                       # whole column -- "3:3" for a whole row
rng("B3:B10").sum()              # SUM(B3:B10)  -- .average() .count() .counta() .min() .max()
```

References are **relative by default**, so Excel's own reference fix-up behaves
normally when someone later edits the workbook by hand.

Sheet qualification is always explicit — never inferred:

```python
data = Ref(ws_source)            # an openpyxl worksheet, or just a name string
data["B3"]                       # 'Source Data'!B3
data["A:A"]                      # 'Source Data'!A:A
cell("B3", sheet="Data")         # Data!B3
```

## Operators

| Python | Excel | |
|---|---|---|
| `+ - * /` | `+ - * /` | |
| `**` | `^` | |
| `&` | `&` | string concatenation, **not** boolean AND — use `F.AND(...)` |
| `-x` | `-x` | |
| `x.pct()` | `x%` | |

Comparisons are **methods**, not operators: `.eq() .ne() .lt() .le() .gt() .ge()`.
That keeps `==` and `hash()` behaving like normal Python, so references stay usable
as dict keys and in sets. It is a real ergonomic cost in condition-heavy models,
paid deliberately. Reflected operators work too, so `1000 - cost` is fine.

## Functions

`F` builds a call for any name — nothing limits you to a listed set:

```python
F.SUM(rng("B3:B10"))
F.VLOOKUP(key, rng("A:D"), 3, False)
F.SOME_ADDIN_FUNCTION(a, b)
F.STDEV__S(rng("A1:A9"))         # double underscore becomes a dot: STDEV.S
```

The [`_xlfn.` rewriting](index.md#why) happens here:

```python
F.XLOOKUP(key, lookup, result)   # =_xlfn.XLOOKUP(...)
F.FILTER(rng("A:A"), cond)       # =_xlfn._xlws.FILTER(...)
```

`None` renders as an omitted argument: `F.VLOOKUP(a, b, 3, None)` → `VLOOKUP(a,b,3,)`.

`Raw("...")` is the escape hatch for formula text `pycountant.excel` does not model. It is
parenthesised whenever nested, since its structure is unknown — pass `atomic=True`
if it is a single self-contained term.

### Discovering functions

You should not need Excel open to write an Excel formula. Three layers of the
package exist so you don't:

**Completion.** `F.SUM` is an attribute lookup, not a string, so your editor offers
the names. `dir(F)` returns the 263 it knows, which also gives you tab completion in
a REPL:

```python
>>> [n for n in dir(F) if n.startswith("TEXT")]
['TEXT', 'TEXTAFTER', 'TEXTBEFORE', 'TEXTJOIN', 'TEXTSPLIT']
```

**Signatures.** 85 of the most-used functions are declared in `functions.pyi` with
real parameter names, so hovering or typing the opening bracket shows the order —
which is the part nobody remembers:

```python
F.SUMIF(rng("A:A"), ">5", rng("B:B"))     # range, criteria, sum_range
F.SUMIFS(rng("B:B"), rng("A:A"), ">5")    # sum_range, criteria_range, criteria
```

Those parameters are **positional-only**. The names are there to be read in a
tooltip, not passed as keywords — `F.SUMIF(range=..., criteria=...)` is an error.
Excel has no keyword arguments either, so there is nothing sensible to map them to.

**Everything else still works.** The 263 known names are for completion and
spell-checking, not a gate. Anything outside the set — an add-in, a function newer
than this release — builds a call with whatever arguments you give it:

```python
F.BLOOMBERG_BDP(c, "PX_LAST", 1, 2, 3)    # never checked, never blocked
```

See [Validation](validation.md) for which names are checked and what happens when
you misspell one.


## Two things worth knowing

**Expressions are `str` subclasses.** That is what lets you assign one to a cell with
no conversion step. The string value is the finished formula:

```python
str(rev - cost)          # "=B3-B4"
(rev - cost).text        # "B3-B4"   -- the body, for building strings yourself
```

The trade-off: `f"Total: {ref}"` gives `"Total: =B3"`, and `isinstance(expr, str)` is
true. Use `.text` when you want the body.

**openpyxl does not update formulas when you insert or delete rows.** From its
[docs](https://openpyxl.readthedocs.io/en/stable/editing_worksheets.html): *"Openpyxl
does not manage dependencies, such as formulae, tables, charts, etc., when rows or
columns are inserted or deleted."* Excel fixes references only when a **human** edits
the workbook; a file written by `ws.delete_rows(3)` just contains stale strings.

`pycountant.excel` does not change this. Settle your data in Python, then write. If you must
move things afterwards, `.shift()` re-points every relative reference in an
expression and leaves `$`-locked ones alone:

```python
growth = F.ROUND((cell("B3") - cell("B4")) / cell("$A$1"), 2)
growth.shift(rows=-1)            # =ROUND((B2-B3)/$A$1,2)
```

