"""pycountant -- Python package for accountants."""

from importlib.metadata import PackageNotFoundError, version

try:
    # Read from the installed distribution, so pyproject.toml is the only place a
    # version is ever edited -- `uv version --bump` and `just release` depend on it.
    __version__ = version("pycountant")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
