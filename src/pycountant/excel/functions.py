"""Excel worksheet functions.

``F`` builds a call for any function name, so nothing here limits which functions
you can use::

    F.SUM(rng("B3:B10"))
    F.XLOOKUP(key, lookup_range, return_range)
    F.SOME_ADDIN_FUNCTION(a, b)

Functions added in Excel 2010 or later are stored in the file with an ``_xlfn.``
prefix; written bare they show as ``#NAME?`` when the workbook is opened.  That
rewriting happens automatically, so you always write the plain name.

Two checks run at construction, both aimed at mistakes that would otherwise survive
as far as opening the workbook:

* **Arity.**  Names in :data:`_ARITY` are checked against their argument count and
  raise :class:`TypeError` on the line that built them.  Names outside the table are
  not checked at all, so add-in and future functions keep working.
* **Spelling.**  An unrecognised name close to a known one warns
  (:class:`UnknownFunctionWarning`) rather than raising, since an arbitrary name is
  legitimate.  ``check=False`` silences both.
"""

from __future__ import annotations

import difflib
import warnings

from .expr import P_ATOM, Expr, lit

__all__ = ["Func", "F", "UnknownFunctionWarning"]


class UnknownFunctionWarning(UserWarning):
    """An unrecognised function name that looks like a misspelling of a known one."""


# Functions added in Excel 2010 and later, which the file format stores prefixed.
# Taken from XlsxWriter's table, which tracks the Microsoft list.
_XLFN = {
    "ACOT",
    "ACOTH",
    "AGGREGATE",
    "ANCHORARRAY",
    "ARABIC",
    "ARRAYTOTEXT",
    "BASE",
    "BETA.DIST",
    "BETA.INV",
    "BINOM.DIST",
    "BINOM.DIST.RANGE",
    "BINOM.INV",
    "BITAND",
    "BITLSHIFT",
    "BITOR",
    "BITRSHIFT",
    "BITXOR",
    "BYCOL",
    "BYROW",
    "CEILING.MATH",
    "CEILING.PRECISE",
    "CHISQ.DIST",
    "CHISQ.DIST.RT",
    "CHISQ.INV",
    "CHISQ.INV.RT",
    "CHISQ.TEST",
    "CHOOSECOLS",
    "CHOOSEROWS",
    "COMBINA",
    "CONCAT",
    "CONFIDENCE.NORM",
    "CONFIDENCE.T",
    "COT",
    "COTH",
    "COVARIANCE.P",
    "COVARIANCE.S",
    "CSC",
    "CSCH",
    "DAYS",
    "DECIMAL",
    "DROP",
    "ERF.PRECISE",
    "ERFC.PRECISE",
    "EXPAND",
    "EXPON.DIST",
    "F.DIST",
    "F.DIST.RT",
    "F.INV",
    "F.INV.RT",
    "F.TEST",
    "FILTERXML",
    "FLOOR.MATH",
    "FLOOR.PRECISE",
    "FORECAST.ETS",
    "FORECAST.ETS.CONFINT",
    "FORECAST.ETS.SEASONALITY",
    "FORECAST.ETS.STAT",
    "FORECAST.LINEAR",
    "FORMULATEXT",
    "GAMMA",
    "GAMMA.DIST",
    "GAMMA.INV",
    "GAMMALN.PRECISE",
    "GAUSS",
    "HSTACK",
    "HYPGEOM.DIST",
    "IFNA",
    "IFS",
    "IMAGE",
    "IMCOSH",
    "IMCOT",
    "IMCSC",
    "IMCSCH",
    "IMSEC",
    "IMSECH",
    "IMSINH",
    "IMTAN",
    "ISFORMULA",
    "ISOMITTED",
    "ISOWEEKNUM",
    "LAMBDA",
    "LET",
    "LOGNORM.DIST",
    "LOGNORM.INV",
    "MAKEARRAY",
    "MAP",
    "MAXIFS",
    "MINIFS",
    "MODE.MULT",
    "MODE.SNGL",
    "MUNIT",
    "NEGBINOM.DIST",
    "NORM.DIST",
    "NORM.INV",
    "NORM.S.DIST",
    "NORM.S.INV",
    "NUMBERVALUE",
    "PDURATION",
    "PERCENTILE.EXC",
    "PERCENTILE.INC",
    "PERCENTRANK.EXC",
    "PERCENTRANK.INC",
    "PERMUTATIONA",
    "PHI",
    "POISSON.DIST",
    "QUARTILE.EXC",
    "QUARTILE.INC",
    "QUERYSTRING",
    "RANDARRAY",
    "RANK.AVG",
    "RANK.EQ",
    "REDUCE",
    "RRI",
    "SCAN",
    "SEC",
    "SECH",
    "SEQUENCE",
    "SHEET",
    "SHEETS",
    "SINGLE",
    "SKEW.P",
    "SORTBY",
    "STDEV.P",
    "STDEV.S",
    "SWITCH",
    "T.DIST",
    "T.DIST.2T",
    "T.DIST.RT",
    "T.INV",
    "T.INV.2T",
    "T.TEST",
    "TAKE",
    "TEXTAFTER",
    "TEXTBEFORE",
    "TEXTJOIN",
    "TEXTSPLIT",
    "TOCOL",
    "TOROW",
    "UNICHAR",
    "UNICODE",
    "UNIQUE",
    "VALUETOTEXT",
    "VAR.P",
    "VAR.S",
    "VSTACK",
    "WEBSERVICE",
    "WEIBULL.DIST",
    "WRAPCOLS",
    "WRAPROWS",
    "XLOOKUP",
    "XMATCH",
    "XOR",
    "Z.TEST",
}

# Two dynamic-array functions take a further worksheet-class prefix.
_XLWS = {
    "FILTER",
    "SORT",
}


def stored_name(name: str) -> str:
    """The name as it must appear inside the xlsx file."""
    upper = name.upper()
    if upper in _XLWS:
        return "_xlfn._xlws." + upper
    if upper in _XLFN:
        return "_xlfn." + upper
    return name


class Func(Expr):
    """A worksheet function call.

    ``None`` renders as an omitted argument, so ``Func("VLOOKUP", a, b, c, None)``
    gives ``VLOOKUP(a,b,c,)``.
    """

    name: str
    args: tuple

    def __new__(cls, name: str, *args, check: bool = True) -> Func:
        if check:
            _check_name(name, len(args))
        parts = tuple(lit(a) for a in args)
        text = f"{stored_name(name)}({','.join(p.text for p in parts)})"
        obj = cls._make(text, P_ATOM)
        obj.name, obj.args = name, parts
        return obj

    def shift(self, rows: int = 0, cols: int = 0) -> Func:
        # Already validated when first built -- and shifting cannot change arity.
        return Func(self.name, *(a.shift(rows, cols) for a in self.args), check=False)


def _check_name(name: str, n_args: int) -> None:
    """Raise on a known function called with the wrong number of arguments.

    Names outside :data:`_ARITY` are not checked -- add-in and future functions must
    keep working -- but one close to a known name warns, since that is far more
    likely a typo than a real function.
    """
    upper = name.upper()
    bounds = _ARITY.get(upper)
    if bounds is None:
        if upper not in _XLFN and upper not in _XLWS:
            near = difflib.get_close_matches(upper, _KNOWN, n=1, cutoff=0.8)
            if near:
                warnings.warn(
                    f"{name!r} is not a known Excel function -- did you mean "
                    f"{near[0]!r}? It is written as-is, and shows as #NAME? if Excel "
                    f"does not know it either. Pass check=False to silence this.",
                    UnknownFunctionWarning,
                    stacklevel=3,
                )
        return

    low, high = bounds
    if low <= n_args and (high is None or n_args <= high):
        return
    if high is None:
        wanted = f"at least {low}"
    elif low == high:
        wanted = f"exactly {low}"
    else:
        wanted = f"{low} to {high}"
    plural = "" if wanted.endswith(" 1") else "s"
    raise TypeError(
        f"{upper} takes {wanted} argument{plural}, got {n_args}. Pass check=False to override."
    )


class _Functions:
    """Attribute access builds a call: ``F.SUM(a, b)`` -> ``SUM(a,b)``."""

    __slots__ = ()

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        def call(*args, check: bool = True) -> Func:
            return Func(name.replace("__", "."), *args, check=check)

        call.__name__ = name
        call.__qualname__ = f"F.{name}"
        call.__doc__ = f"Build an Excel {name.replace('__', '.')}(...) call."
        return call

    def __dir__(self):
        return sorted(_XLFN | _XLWS | _ARITY.keys())

    def __repr__(self) -> str:
        return "<pycountant.excel.F: Excel worksheet functions>"


# Argument counts for the functions people actually reach for, as
# ``name -> (min, max)`` with ``None`` for "no upper bound".  A name here is
# checked; a name absent from it is not, which is what keeps add-in and
# newly-shipped functions working.  When a signature is uncertain, widen the
# bounds: a false rejection blocks correct code, while a miss only leaves you
# where you would have been anyway.  Optional trailing arguments are counted, so
# these ranges track Excel's own "[...]" notation.
_ARITY: dict[str, tuple[int, int | None]] = {
    # Aggregation
    "SUM": (1, None),
    "SUMIF": (2, 3),
    "SUMIFS": (3, None),
    "SUMPRODUCT": (1, None),
    "AVERAGE": (1, None),
    "AVERAGEIF": (2, 3),
    "AVERAGEIFS": (3, None),
    "COUNT": (1, None),
    "COUNTA": (1, None),
    "COUNTBLANK": (1, 1),
    "COUNTIF": (2, 2),
    "COUNTIFS": (2, None),
    "MIN": (1, None),
    "MAX": (1, None),
    "MAXIFS": (3, None),
    "MINIFS": (3, None),
    "SUBTOTAL": (2, None),
    "AGGREGATE": (3, None),
    "STDEV.S": (1, None),
    "STDEV.P": (1, None),
    "VAR.S": (1, None),
    "VAR.P": (1, None),
    "MEDIAN": (1, None),
    "MODE.SNGL": (1, None),
    # Arithmetic
    "ROUND": (2, 2),
    "ROUNDUP": (2, 2),
    "ROUNDDOWN": (2, 2),
    "MROUND": (2, 2),
    "ABS": (1, 1),
    "MOD": (2, 2),
    "INT": (1, 1),
    "TRUNC": (1, 2),
    "SIGN": (1, 1),
    "POWER": (2, 2),
    "SQRT": (1, 1),
    "EXP": (1, 1),
    "LN": (1, 1),
    "LOG": (1, 2),
    "LOG10": (1, 1),
    "CEILING.MATH": (1, 3),
    "FLOOR.MATH": (1, 3),
    "RAND": (0, 0),
    "RANDBETWEEN": (2, 2),
    # Logic
    "IF": (2, 3),
    "IFERROR": (2, 2),
    "IFNA": (2, 2),
    "IFS": (2, None),
    "AND": (1, None),
    "OR": (1, None),
    "NOT": (1, 1),
    "XOR": (1, None),
    "SWITCH": (3, None),
    "LET": (3, None),
    # Lookup
    "VLOOKUP": (3, 4),
    "HLOOKUP": (3, 4),
    "LOOKUP": (2, 3),
    "INDEX": (2, 4),
    "MATCH": (2, 3),
    "OFFSET": (3, 5),
    "INDIRECT": (1, 2),
    "CHOOSE": (2, None),
    "XLOOKUP": (3, 6),
    "XMATCH": (2, 4),
    "ROW": (0, 1),
    "COLUMN": (0, 1),
    "ROWS": (1, 1),
    "COLUMNS": (1, 1),
    # Dynamic arrays
    "FILTER": (2, 3),
    "SORT": (1, 4),
    "SORTBY": (2, None),
    "UNIQUE": (1, 3),
    "SEQUENCE": (1, 4),
    "TAKE": (2, 3),
    "DROP": (2, 3),
    "HSTACK": (1, None),
    "VSTACK": (1, None),
    # Text
    "TEXT": (2, 2),
    "LEN": (1, 1),
    "LEFT": (1, 2),
    "RIGHT": (1, 2),
    "MID": (3, 3),
    "TRIM": (1, 1),
    "UPPER": (1, 1),
    "LOWER": (1, 1),
    "PROPER": (1, 1),
    "SUBSTITUTE": (3, 4),
    "REPLACE": (4, 4),
    "FIND": (2, 3),
    "SEARCH": (2, 3),
    "CONCAT": (1, None),
    "CONCATENATE": (1, None),
    "TEXTJOIN": (3, None),
    "REPT": (2, 2),
    "VALUE": (1, 1),
    "NUMBERVALUE": (1, 3),
    "TEXTBEFORE": (2, 6),
    "TEXTAFTER": (2, 6),
    "TEXTSPLIT": (2, 6),
    # Dates
    "TODAY": (0, 0),
    "NOW": (0, 0),
    "DATE": (3, 3),
    "TIME": (3, 3),
    "YEAR": (1, 1),
    "MONTH": (1, 1),
    "DAY": (1, 1),
    "HOUR": (1, 1),
    "MINUTE": (1, 1),
    "SECOND": (1, 1),
    "WEEKDAY": (1, 2),
    "WEEKNUM": (1, 2),
    "EOMONTH": (2, 2),
    "EDATE": (2, 2),
    "DATEDIF": (3, 3),
    "DAYS": (2, 2),
    "YEARFRAC": (2, 3),
    "WORKDAY": (2, 3),
    "NETWORKDAYS": (2, 3),
    "DATEVALUE": (1, 1),
    # Finance
    "NPV": (2, None),
    "IRR": (1, 2),
    "XNPV": (3, 3),
    "XIRR": (2, 3),
    "PMT": (3, 5),
    "IPMT": (4, 6),
    "PPMT": (4, 6),
    "PV": (3, 5),
    "FV": (3, 5),
    "RATE": (3, 6),
    "NPER": (3, 5),
    "SLN": (3, 3),
    "PDURATION": (3, 3),
    "RRI": (3, 3),
    # Information
    "ISBLANK": (1, 1),
    "ISNUMBER": (1, 1),
    "ISTEXT": (1, 1),
    "ISERROR": (1, 1),
    "ISERR": (1, 1),
    "ISNA": (1, 1),
    "ISFORMULA": (1, 1),
    "ISLOGICAL": (1, 1),
    "NA": (0, 0),
    "ERROR.TYPE": (1, 1),
    "FORMULATEXT": (1, 1),
    "SHEET": (0, 1),
    "SHEETS": (0, 1),
    "CELL": (1, 2),
    "INFO": (1, 1),
}

# Every name we can vouch for, used only to spot near-miss misspellings.
_KNOWN = frozenset(_ARITY) | _XLFN | _XLWS

F = _Functions()
