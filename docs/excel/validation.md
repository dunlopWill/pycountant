# Validation


Three layers, each catching the mistakes the one before it cannot.

**Arity, at construction.** Calling a function you know with the wrong number of
arguments raises on the line that wrote it, rather than opening as `#VALUE!`:

```python
F.SUMIF(rng("A:A"))              # TypeError: SUMIF takes 2 to 3 arguments, got 1
F.ROUND(cell("A1"))              # TypeError: ROUND takes exactly 2 arguments, got 1
F.TODAY(cell("A1"))              # TypeError: TODAY takes exactly 0 arguments, got 1
```

Only names in the table are checked, so the open set stays open — an add-in or a
function newer than this release takes whatever arguments it likes:

```python
F.BLOOMBERG_BDP(c, "PX_LAST", 1, 2, 3)   # never checked, never blocked
```

`check=False` overrides any single call, for the day the table is wrong:

```python
F.SUMIF(rng("A:A"), check=False)
```

**Spelling, as a warning.** An unknown name that looks like a known one is far more
likely a typo than a real function, but it cannot be an error — arbitrary names are
legitimate. So it warns and renders:

```python
F.SUMIFF(rng("A:A"), ">5")
# UnknownFunctionWarning: 'SUMIFF' is not a known Excel function -- did you mean
# 'SUMIF'? It is written as-is, and shows as #NAME? if Excel does not know it either.
```

Silence it per-call with `check=False`, or globally with
`warnings.filterwarnings("ignore", category=UnknownFunctionWarning)`.

**Arity again, before you run it.** The package ships type stubs, so a checker
flags the same mistakes in the editor. Positions that must be a reference are typed
so that passing a plain string is caught too — `"A:A"` would render as a text
literal, not a range:

```python
F.SUMIF(rng("A:A"))              # pyright: Expected 1 more positional argument
F.SUMIF("A:A", ">5")             # pyright: "Literal['A:A']" not assignable to "Expr"
```

One wrinkle: a stub signature cannot depend on a runtime flag, so `check=False`
silences the runtime check while a type checker still sees the arity error. When
you need both off, build the call directly — `Func` takes `*args` and constrains
nothing:

```python
Func("SUMIF", rng("A:A"), check=False)
```

### What none of this catches

A formula can be well-formed, correctly spelled, correctly counted — and still
wrong. Arguments in the wrong order, a range off by one row, a reference into a
cell you never filled:

```python
F.VLOOKUP(rng("A:D"), cell("A1"), 3)     # arguments swapped; valid, and wrong
```

Only an engine that evaluates the sheet finds those. `tests/test_recalc.py` writes
a workbook, recalculates it in headless LibreOffice, and asserts on the computed
values. If you generate models that matter, do the same for yours — it is the only
check that tests the *meaning* rather than the shape:

```bash
uv run pytest -m slow          # requires libreoffice
uv run pytest -m "not slow"    # skip it
```

