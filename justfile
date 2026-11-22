# Justfile for pycountant

# Show available commands
list:
    @just --list

alias b := build
alias c := clean
alias d := docs-serve
alias t := test
alias tc := type-check

# Type check with both checkers (pyright is authoritative -- see CLAUDE.md)
type-check:
    uv run pyright
    uv run ty check .

# Type check with concise output (one diagnostic per line)
type-check-concise:
    uv run ty check --output-format=concise .

# Type check in watch mode (rechecks on file changes)
type-check-watch:
    uv run ty check --watch .

# Apply formatting and automatic lint fixes
fix:
    uv run ruff format .
    uv run ruff check . --fix

# Verify formatting, linting, types, and tests without modifying source files
check:
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright
    uv run ty check .
    uv run pytest

# Apply automatic fixes, then run the local quality gate
fix-and-check: fix check

# Compatibility alias for fix-and-check
qa: fix-and-check

# The LibreOffice recalculation is version-independent, so `just recalc` covers it.

# Run the fast tests on every supported Python version
testall:
    uv run --python=3.13 pytest -m "not slow"
    uv run --python=3.14 pytest -m "not slow"

# Run all the tests, but allow for arguments to be passed
test *ARGS:
    uv run pytest {{ARGS}}

# Run only the fast tests (skips the LibreOffice recalculation)
fast:
    uv run pytest -m "not slow"

# Recalculate generated workbooks in headless LibreOffice (needs `soffice`)
recalc:
    uv run pytest -m slow -v

# Run all the tests, but on failure, drop into the debugger
pdb *ARGS:
    uv run pytest --pdb --maxfail=10 {{ARGS}}

# Run tests with coverage across all supported Python versions
coverage:
    uv run --python=3.13 coverage run -m pytest -m "not slow"
    uv run --python=3.14 coverage run -m pytest -m "not slow"
    uv run coverage combine
    uv run coverage report
    uv run coverage html

# Regenerate docs/reference/ after adding, removing or renaming a module
docs-ref:
    uv run scripts/gen_ref_pages.py

# Serve docs locally with live reload
docs-serve: docs-ref
    -lsof -ti :8000 | xargs kill
    uv run --group docs zensical serve

# Build docs
docs-build: docs-ref
    uv run --group docs zensical build --clean

# Build the project, useful for checking that packaging is correct
build:
    rm -rf build
    rm -rf dist
    uv build

# Finalize release notes, tag, push, and create a GitHub release
release:
    uv run scripts/release.py

# Remove all build, test, coverage and Python artifacts
clean: clean-build clean-pyc clean-test

# Remove build artifacts
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

# Remove Python file artifacts
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

# Remove test and coverage artifacts
clean-test:
	rm -f .coverage
	rm -f .coverage.*
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -fr .ruff_cache

# Publish to PyPI (manual alternative to GitHub Actions)
publish:
    uv build
    uv publish
