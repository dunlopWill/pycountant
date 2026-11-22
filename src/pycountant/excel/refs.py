"""Cell and range references.

References are relative by default, so Excel's own fix-up behaviour works normally
when someone later edits the workbook by hand.  Sheet qualification is always
explicit -- it is never inferred from context.
"""

from __future__ import annotations

import re

from .expr import P_ATOM, P_REF, Expr

__all__ = ["CellRef", "RangeRef", "Ref", "cell", "rng", "col_letter", "col_index"]

_A1_RE = re.compile(r"^(\$?)([A-Za-z]{1,3})(\$?)([1-9][0-9]*)$")
_COL_RE = re.compile(r"^(\$?)([A-Za-z]{1,3})$")
_ROW_RE = re.compile(r"^(\$?)([1-9][0-9]*)$")
# A sheet name is safe unquoted only if it is all word characters and does not
# start with a digit -- otherwise Excel needs it in single quotes.
_SAFE_SHEET_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

MAX_COL = 16384  # XFD
MAX_ROW = 1048576


class _Keep:
    """Sentinel for :meth:`CellRef._replace`: leave this field as it is.

    ``None`` cannot serve here -- ``sheet=None`` is a real value meaning "no sheet
    prefix", which is what ``.bare()`` asks for.
    """

    def __repr__(self) -> str:
        return "<keep>"


_KEEP = _Keep()


def col_letter(index: int) -> str:
    """1-based column index to letters: ``1 -> A``, ``27 -> AA``."""
    if not 1 <= index <= MAX_COL:
        raise ValueError(f"column index {index} out of range 1..{MAX_COL}")
    letters = ""
    while index:
        index, rem = divmod(index - 1, 26)  # bijective base-26
        letters = chr(65 + rem) + letters
    return letters


def col_index(letters: str) -> int:
    """Column letters to a 1-based index: ``A -> 1``, ``AA -> 27``."""
    index = 0
    for ch in letters.upper():
        if not "A" <= ch <= "Z":
            raise ValueError(f"invalid column letters: {letters!r}")
        index = index * 26 + (ord(ch) - 64)
    if not 1 <= index <= MAX_COL:
        raise ValueError(f"column {letters!r} out of range A..XFD")
    return index


def sheet_name(sheet) -> str | None:
    """Accept an openpyxl worksheet (duck-typed on ``.title``) or a plain name."""
    if sheet is None:
        return None
    return sheet if isinstance(sheet, str) else sheet.title


def sheet_prefix(sheet) -> str:
    name = sheet_name(sheet)
    if name is None:
        return ""
    if _SAFE_SHEET_RE.match(name):
        return f"{name}!"
    return "'" + name.replace("'", "''") + "'!"


def _parse_a1(a1: str):
    m = _A1_RE.match(a1.strip())
    if not m:
        raise ValueError(f"not an A1 cell reference: {a1!r}")
    abs_col, letters, abs_row, row = m.groups()
    return int(row), col_index(letters), bool(abs_row), bool(abs_col)


class CellRef(Expr):
    """A single cell, e.g. ``B3``, ``$B$3`` or ``'Source Data'!B3``."""

    row: int
    col: int
    abs_row: bool
    abs_col: bool
    sheet: str | None
    home: str | None

    def __new__(
        cls,
        row: int,
        col: int,
        *,
        abs_row: bool = False,
        abs_col: bool = False,
        sheet=None,
        home=None,
    ) -> CellRef:
        if not 1 <= row <= MAX_ROW:
            raise ValueError(f"row {row} out of range 1..{MAX_ROW}")
        name = sheet_name(sheet)
        text = (
            sheet_prefix(name)
            + ("$" if abs_col else "")
            + col_letter(col)
            + ("$" if abs_row else "")
            + str(row)
        )
        obj = cls._make(text, P_ATOM)
        obj.row, obj.col = row, col
        obj.abs_row, obj.abs_col, obj.sheet = abs_row, abs_col, name
        # The sheet this ref was written to.  Never rendered -- it only makes
        # .qualified() possible without retyping the sheet name.
        obj.home = sheet_name(home) or name
        return obj

    @property
    def coordinate(self) -> str:
        """The bare ``B3`` coordinate, without sheet or ``$`` markers."""
        return f"{col_letter(self.col)}{self.row}"

    def rel_text(self) -> str:
        """This cell's text without the sheet prefix, keeping any ``$`` markers."""
        return (
            ("$" if self.abs_col else "")
            + col_letter(self.col)
            + ("$" if self.abs_row else "")
            + str(self.row)
        )

    def _replace(
        self,
        *,
        row: int | _Keep = _KEEP,
        col: int | _Keep = _KEEP,
        abs_row: bool | _Keep = _KEEP,
        abs_col: bool | _Keep = _KEEP,
        sheet: str | None | _Keep = _KEEP,
        home: str | None | _Keep = _KEEP,
    ) -> CellRef:
        """A copy of this reference with the named fields changed."""
        return CellRef(
            self.row if isinstance(row, _Keep) else row,
            self.col if isinstance(col, _Keep) else col,
            abs_row=self.abs_row if isinstance(abs_row, _Keep) else abs_row,
            abs_col=self.abs_col if isinstance(abs_col, _Keep) else abs_col,
            sheet=self.sheet if isinstance(sheet, _Keep) else sheet,
            home=self.home if isinstance(home, _Keep) else home,
        )

    def offset(self, rows: int = 0, cols: int = 0) -> CellRef:
        """A new reference moved by ``rows`` down and ``cols`` right."""
        return self._replace(row=self.row + rows, col=self.col + cols)

    def shift(self, rows: int = 0, cols: int = 0) -> CellRef:
        return self._replace(
            row=self.row if self.abs_row else self.row + rows,
            col=self.col if self.abs_col else self.col + cols,
        )

    def abs(self) -> CellRef:
        """Lock both row and column: ``$B$3``."""
        return self._replace(abs_row=True, abs_col=True)

    def abs_r(self) -> CellRef:
        """Lock the row only: ``B$3``."""
        return self._replace(abs_row=True)

    def abs_c(self) -> CellRef:
        """Lock the column only: ``$B3``."""
        return self._replace(abs_col=True)

    def rel(self) -> CellRef:
        """Drop all ``$`` locking."""
        return self._replace(abs_row=False, abs_col=False)

    def on(self, sheet) -> CellRef:
        """The same cell, qualified with another sheet."""
        return self._replace(sheet=sheet)

    def qualified(self) -> CellRef:
        """Qualify with the sheet this ref came from, for use in another sheet."""
        if self.sheet is not None:
            return self
        if self.home is None:
            raise ValueError(
                f"{self!r} has no home sheet to qualify with; use .on(sheet) to name one explicitly"
            )
        return self._replace(sheet=self.home)

    def bare(self) -> CellRef:
        """Drop the sheet prefix, keeping the home sheet for later qualification."""
        return self._replace(sheet=None)

    def to(self, other: CellRef) -> RangeRef:
        """The rectangular range spanning this cell and ``other``."""
        return RangeRef(self, other)


class RangeRef(Expr):
    """A range: ``B3:B10``, a whole column ``B:B``, or a whole row ``3:3``."""

    start: str
    end: str
    sheet: str | None
    home: str | None

    def __new__(cls, start, end=None, *, sheet=None, home=None) -> RangeRef:
        if end is None:
            raise TypeError("RangeRef needs both a start and an end")
        name = sheet_name(sheet)
        if isinstance(start, CellRef) and isinstance(end, CellRef):
            # A cell's own sheet wins if none was passed explicitly.
            name = name if name is not None else start.sheet
            home = home if home is not None else start.home
            start_txt = start.rel_text()
            end_txt = end.rel_text()
        else:
            start_txt, end_txt = str(start), str(end)
        obj = cls._make(f"{sheet_prefix(name)}{start_txt}:{end_txt}", P_REF)
        obj.start, obj.end, obj.sheet = start_txt, end_txt, name
        obj.home = sheet_name(home) or name
        return obj

    @property
    def coordinate(self) -> str:
        """The bare ``B3:B10``, without the sheet prefix."""
        return f"{self.start}:{self.end}"

    def on(self, sheet) -> RangeRef:
        return RangeRef(self.start, self.end, sheet=sheet, home=self.home)

    def qualified(self) -> RangeRef:
        """Qualify with the sheet this range came from."""
        if self.sheet is not None:
            return self
        if self.home is None:
            raise ValueError(f"{self!r} has no home sheet to qualify with")
        return RangeRef(self.start, self.end, sheet=self.home)

    def bare(self) -> RangeRef:
        """Drop the sheet prefix, keeping the home sheet."""
        return RangeRef(self.start, self.end, home=self.home)

    def shift(self, rows: int = 0, cols: int = 0) -> RangeRef:
        return RangeRef(
            _shift_part(self.start, rows, cols),
            _shift_part(self.end, rows, cols),
            sheet=self.sheet,
            home=self.home,
        )

    # Convenience aggregates.  Imported lazily to keep functions.py free to import
    # this module for its own type checks.
    def sum(self):
        return self._fn("SUM")

    def average(self):
        return self._fn("AVERAGE")

    # NOTE: this shadows str.count, so RangeRef is the one Expr subclass where
    # "expr.count(substring)" raises instead of counting characters.  Kept because
    # .count() is documented API and renaming it would break callers; the
    # alternative, dispatching on the argument, would be worse.  Reach for
    # F.COUNT(rng) if the shadowing ever bites.
    def count(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return self._fn("COUNT")

    def counta(self):
        return self._fn("COUNTA")

    def min(self):
        return self._fn("MIN")

    def max(self):
        return self._fn("MAX")

    def _fn(self, name: str):
        from .functions import Func

        return Func(name, self)


def _shift_part(part: str, rows: int, cols: int) -> str:
    """Move one endpoint of a range, respecting ``$`` locks and open endpoints."""
    m = _A1_RE.match(part)
    if m:
        abs_col, letters, abs_row, row = m.groups()
        new_col = letters if abs_col else col_letter(col_index(letters) + cols)
        new_row = row if abs_row else str(int(row) + rows)
        return f"{abs_col}{new_col}{abs_row}{new_row}"
    m = _COL_RE.match(part)
    if m:
        abs_col, letters = m.groups()
        return abs_col + (letters if abs_col else col_letter(col_index(letters) + cols))
    m = _ROW_RE.match(part)
    if m:
        abs_row, row = m.groups()
        return abs_row + (row if abs_row else str(int(row) + rows))
    raise ValueError(f"cannot shift range endpoint {part!r}")


class Ref:
    """A sheet-bound factory for references.

    Takes an openpyxl worksheet (duck-typed on ``.title``, so openpyxl is never
    imported) or a plain sheet name::

        data = Ref(ws)
        data["B3"]  # 'Data'!B3
        data["A:A"]  # 'Data'!A:A
        data.cell(3, 2)  # 'Data'!B3
    """

    __slots__ = ("sheet",)

    def __init__(self, sheet):
        self.sheet = sheet_name(sheet)

    def __repr__(self) -> str:
        return f"Ref({self.sheet!r})"

    def __getitem__(self, key: str):
        return (
            cell(key, sheet=self.sheet)
            if ":" not in key
            else rng(key, sheet=self.sheet)
        )

    def cell(self, row: int, col: int, **kw) -> CellRef:
        return cell(row, col, sheet=self.sheet, **kw)

    def rng(self, *args, **kw) -> RangeRef:
        return rng(*args, sheet=self.sheet, **kw)


def cell(
    *positional,
    sheet=None,
    home=None,
    abs_row: bool | None = None,
    abs_col: bool | None = None,
) -> CellRef:
    """Build a :class:`CellRef` from ``"B3"`` or from ``(row, col)``.

    ``cell("$B$3")`` picks up the ``$`` markers; the ``abs_row``/``abs_col``
    keywords override whatever the string said.
    """
    args = list(positional)
    if args and not isinstance(args[0], (str, int)):
        sheet = args.pop(0)  # a worksheet passed positionally
    if len(args) == 1 and isinstance(args[0], str):
        row, col, parsed_row, parsed_col = _parse_a1(args[0])
    elif len(args) == 2 and all(isinstance(a, int) for a in args):
        row, col = args
        parsed_row = parsed_col = False
    else:
        raise TypeError("cell() takes either an A1 string or (row, col) integers")
    return CellRef(
        row,
        col,
        abs_row=parsed_row if abs_row is None else abs_row,
        abs_col=parsed_col if abs_col is None else abs_col,
        sheet=sheet,
        home=home,
    )


def rng(*positional, sheet=None, home=None) -> RangeRef:
    """Build a :class:`RangeRef` from ``"B3:B10"`` or from two cell references."""
    args = list(positional)
    if args and not isinstance(args[0], str) and not isinstance(args[0], CellRef):
        sheet = args.pop(0)
    if len(args) == 1 and isinstance(args[0], str):
        start, _, end = args[0].strip().partition(":")
        if not end:
            raise ValueError(f"not a range: {args[0]!r}")
        for part in (start, end):
            if not (_A1_RE.match(part) or _COL_RE.match(part) or _ROW_RE.match(part)):
                raise ValueError(f"invalid range endpoint {part!r} in {args[0]!r}")
        return RangeRef(start, end, sheet=sheet, home=home)
    if len(args) == 2 and all(isinstance(a, CellRef) for a in args):
        return RangeRef(args[0], args[1], sheet=sheet, home=home)
    raise TypeError('rng() takes an "A1:B2" string or two CellRefs')
