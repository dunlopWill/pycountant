"""Write a value and get a reference back, so you never retype a coordinate.

``Sheet`` is a thin wrapper over an openpyxl worksheet -- it holds no state of its
own beyond the worksheet, and ``.ws`` is always there when you want plain openpyxl::

    s = Sheet(ws)
    rev  = s.put("B2", 1000)
    cost = s.put("B3", 600)
    s.put("B4", (rev - cost) / rev)      # =(B2-B3)/B2

References come back *unqualified*, because most formulas stay on one sheet.  When
one crosses sheets, ``.qualified()`` supplies the sheet name for you.
"""

from __future__ import annotations

from .refs import CellRef, RangeRef, cell, col_letter, rng, sheet_name

__all__ = ["Sheet"]


class Sheet:
    """A write-and-remember wrapper around an openpyxl worksheet.

    openpyxl is never imported: the worksheet is duck-typed on ``.title`` and
    ``.cell(row=, column=, value=)``.
    """

    __slots__ = ("ws", "title")

    def __init__(self, ws):
        self.ws = ws
        self.title = sheet_name(ws)

    def __repr__(self) -> str:
        return f"Sheet({self.title!r})"

    def put(self, *args, number_format: str | None = None, **style) -> CellRef:
        """Write a value and return a reference to the cell it landed in.

        Called either as ``put("B2", value)`` or as ``put(row, col, value)``.
        ``value`` may be an expression, in which case the formula is written.

        ``number_format`` and any further keywords are applied to the openpyxl
        cell as attributes, so ``font=``, ``fill=``, ``alignment=`` and ``border=``
        all pass straight through.
        """
        row, col, value = self._parse_target(args)
        target = self.ws.cell(row=row, column=col, value=value)
        if number_format is not None:
            target.number_format = number_format
        for attr, setting in style.items():
            setattr(target, attr, setting)
        return CellRef(row, col, home=self.title)

    @staticmethod
    def _parse_target(args):
        if len(args) == 2 and isinstance(args[0], str):
            coord, value = args
            ref = cell(coord)
            return ref.row, ref.col, value
        if len(args) == 3 and all(isinstance(a, int) for a in args[:2]):
            return args[0], args[1], args[2]
        raise TypeError('put() takes ("B2", value) or (row, col, value)')

    def ref(self, key: str):
        """A reference into this sheet without writing anything."""
        return rng(key, home=self.title) if ":" in key else cell(key, home=self.title)

    __getitem__ = ref

    def cell(self, row: int, col: int, **kw) -> CellRef:
        """A reference by position, without writing anything."""
        return cell(row, col, home=self.title, **kw)

    def span(self, start: CellRef, end: CellRef) -> RangeRef:
        """The range between two references written on this sheet."""
        return rng(start, end, home=self.title)

    def column(self, ref_or_letter) -> RangeRef:
        """The whole column a reference sits in: ``s.column(rev)`` -> ``B:B``."""
        letter = col_letter(ref_or_letter.col) if isinstance(ref_or_letter, CellRef) else ref_or_letter
        return rng(f"{letter}:{letter}", home=self.title)
