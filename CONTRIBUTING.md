# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/dunlopWill/pycountant/issues.

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

pycountant could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

To preview the docs locally:

```sh
just docs-serve
```

This starts a local server at http://localhost:8000 with live reload. Edit
files in `docs/` or add docstrings to your code (the reference pages are
generated from them by `scripts/gen_ref_pages.py`, which both recipes run
first). Run `just docs-build` to verify a production build.

Docs deploy to https://pycountant.com through Azure Static Web Apps on every
push to `main`; pull requests against `main` get a staging site linked from a
PR comment.

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/dunlopWill/pycountant/issues.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions are welcome :)

## Get Started!

Ready to contribute? Here's how to set up pycountant for local development.

1. Fork the pycountant repo on GitHub.
2. Clone your fork locally:

   ```sh
   git clone git@github.com:your_name_here/pycountant.git
   ```

3. Install your local copy with uv:

   ```sh
   cd pycountant/
   uv sync
   ```

4. Create a branch for local development:

   ```sh
   git checkout -b name-of-your-bugfix-or-feature
   ```

   Now you can make your changes locally.

5. When you're done making changes, verify formatting, linting, types, and tests without modifying files:

   ```sh
   just check
   ```

   Use `just fix` to apply Ruff's formatting and automatic lint fixes, or `just fix-and-check` to apply them before verification.

   Formatting covers Python only. Ruff also formats Python inside Markdown
   fences, and that is switched off in `[tool.ruff.format]`: the Excel docs use
   aligned trailing comments to show a call next to the formula Excel receives,
   and collapsing them to a single space loses the column. Format prose by hand.

   Or run the tests alone:

   ```sh
   just test        # everything
   just fast        # skip the LibreOffice recalculation tests
   just recalc      # only those -- needs `soffice` on PATH
   ```

   `tests/excel_test/recalc_test.py` writes a workbook, recalculates it in headless
   LibreOffice, and asserts on the computed values. It is the only test that
   catches a formula which is well-formed and simply *means* the wrong thing, so
   it runs in CI against a real LibreOffice install. Locally it skips itself when
   `soffice` is missing — install LibreOffice if you are touching
   `pycountant/excel/functions.py`, `expr.py`, or anything about precedence.

6. Commit your changes and push your branch to GitHub:

   ```sh
   git add .
   git commit -m "Your detailed description of your changes."
   git push origin name-of-your-bugfix-or-feature
   ```

7. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with a docstring, and add the feature to the list in README.md.
3. The pull request should work for Python 3.13 and 3.14. Tests run in GitHub Actions on every pull request to the main branch, make sure that the tests pass for all supported Python versions.

## Tips

To run a subset of tests:

```sh
uv run pytest tests/excel_test/precedence_test.py   # one file
uv run pytest -k "parens"                          # one pattern
```

Test files are named `*_test.py` and grouped in a directory per subpackage
(`models_test/`, `services_test/`, `excel_test/`). In the Excel tests,
`precedence_test.py` is the load-bearing one: wrong parentheses give silently
wrong numbers rather than errors.

Both type checkers must stay clean. pyright is authoritative — the package ships
`py.typed`, so its own type errors surface in consumers' editors:

```sh
uv run pyright        # must be 0 errors
uv run ty check .     # must be "All checks passed!"
```

## Releasing a New Version

1. **Bump the version:**
   ```bash
   uv version <version>        # or: uv version --bump minor
   ```
2. **Commit:**
   ```bash
   git add pyproject.toml uv.lock
   git commit -m "Bump version to <version>"
   ```
3. **Release:**
   ```bash
   just release
   ```
   This finalizes `CHANGELOG/unreleased.md` as
   `CHANGELOG/<version>.md`, creates a fresh unreleased file, commits and
   pushes that notes commit, then creates an annotated `v*` tag and GitHub
   Release. The tag push triggers `.github/workflows/publish.yml`, which
   builds the package, generates SLSA provenance attestations, and publishes
   to PyPI via trusted publishing.

Record release-worthy changes in `CHANGELOG/unreleased.md` as they merge.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.
