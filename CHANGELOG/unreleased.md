# Unreleased

These are the changes that will go out in the next release.

## Added

- `pycountant.excel` — build Excel formulas with Python operators, then hand them
  straight to openpyxl. This was previously the separate `pycelerate` package;
  the API is unchanged apart from the import path
  (`from pycelerate import ...` → `from pycountant.excel import ...`).
  - Expression tree rendered with Excel's precedence rules, including the two
    places Python and Excel genuinely disagree (`^` is left-associative in Excel;
    unary `-` binds tighter than `^`).
  - `Sheet.put()` writes a value and hands back a `CellRef`, so no coordinate is
    typed twice.
  - `F.ANYNAME(...)` builds a call for any function name, with the `_xlfn.` and
    `_xlfn._xlws.` prefixes the xlsx format needs applied automatically.
  - Arity checked at construction for known names, a did-you-mean warning for
    near-miss spellings, and type stubs that move both to edit time.
  - No new runtime dependencies; nothing imports openpyxl.
- `pycountant.__version__`, read from the installed distribution metadata.
- The package now ships `py.typed`, so type checkers use its annotations and stubs.

## Changed

- Supports Python 3.14. The minimum pydantic is now 2.12, the first release whose
  core builds on 3.14.

### Project infrastructure

- Built with `uv_build`; full PyPI metadata (licence, classifiers, project URLs).
- Ruff formats and lints with a wider rule set (pycodestyle, Pyflakes, isort,
  bugbear, pyupgrade), replacing flake8, pylint and pre-commit.
- pyright and ty replace mypy; pyright is authoritative.
- One `CI` workflow replaces the separate ruff, flake8, pylint, mypy and pytest
  workflows: lint, type check, tests on 3.13 and 3.14 with branch coverage, and a
  LibreOffice recalculation job for the Excel formulas.
- All workflows pinned by SHA with minimal permissions; Zizmor workflow audit,
  CodeQL `security-extended`, and Dependabot with a 7-day cooldown.
- Publishing is triggered by a `v*` tag, with build provenance attestation.
- Docs configured with `zensical.toml` instead of `mkdocs.yml`.
- `justfile`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`,
  `.editorconfig`, issue and pull request templates, and a `just release` flow
  that turns this file into `CHANGELOG/<version>.md`.
