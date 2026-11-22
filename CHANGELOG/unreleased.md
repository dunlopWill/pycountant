# Unreleased

## Added

- `pycountant.excel` module for building Excel formulas with Python operators and
  writing them straight to openpyxl cells. It was previously the separate
  `pycelerate` package. The API is the same; only the import path has changed
  (`from pycelerate import ...` → `from pycountant.excel import ...`).
  - Formulas follow Excel's precedence rules, including the two places where
    Python and Excel disagree: `^` is left-associative in Excel, and unary `-`
    binds tighter than `^`.
  - `Sheet.put()` writes a value and returns a `CellRef`, so you never type a
    coordinate twice.
  - `F.ANYNAME(...)` builds a call to any function name. The `_xlfn.` and
    `_xlfn._xlws.` prefixes the xlsx format needs are added automatically.
  - Known functions have their argument count checked when the call is built,
    and near-miss names trigger a did-you-mean warning. Type stubs surface both
    in your editor.
  - Adds no runtime dependencies, and nothing in the module imports openpyxl.
- Excel formulas guide and a full API reference in the documentation.
- Documentation guides for currency amounts, exchange rates and tax, and a
  home page summarising everything the package does.
- `pycountant.__version__`, read from the installed package metadata.
- `py.typed` marker, so type checkers use the package's annotations and stubs.
- Support for Python 3.14.
- Full PyPI metadata: licence, classifiers, keywords and project URLs.
- Build provenance attestations for released distributions.
- A security policy (`SECURITY.md`) explaining how to report vulnerabilities.

## Changed

- FX lookups (`get_rate`, `convert` and `Currency.convert`) no longer fail when
  no rate is published on the requested date, such as a weekend. They log a
  warning and try up to two earlier days (`MAX_FALLBACK_DAYS`). A `ValueError`
  is raised only if none of those days has a rate.
- Raised the minimum pydantic version to 2.12, the first release whose core
  builds on Python 3.14.
- The package is now built with `uv_build`.
- The documentation site is now built with Zensical instead of MkDocs.
- Development tooling and CI have been overhauled. See `CONTRIBUTING.md` for
  the current workflow.

## Fixed

- Converting or comparing two amounts in the same currency (other than EUR)
  with the European Central Bank provider no longer raises `ValueError: No rate
  found`. Same-currency lookups now return a rate of 1 without a network request.

- `Currency` now raises `pydantic.ValidationError` for a value that is not a
  number, such as `"abc"` or a bare `"£"`. It previously leaked
  `decimal.InvalidOperation` or `IndexError`.
- `add_tax` and `remove_tax` keep the precision of the amount passed in and no
  longer return exponent forms: removing 20% from `120` gives `Decimal('100')`,
  not `Decimal('1.0E+2')`.
- The `Currency.is_equal()` docstring now says `accept_variance` is measured in
  the other amount's currency, which is what the code has always done.

- The README example now runs: it was missing a comma in the
  `convert(to="USD", on=...)` call and the `date` import. It also no longer
  claims `convert()` returns a `Currency`: it converts in place and returns
  `None`.
