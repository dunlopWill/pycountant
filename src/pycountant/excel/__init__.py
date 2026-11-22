"""Build Excel formulas with Python operators.

Cell references are objects, so Python's own operators assemble the formula and a
precedence-aware renderer parenthesises it correctly::

    from pycountant.excel import cell, rng, Ref, F

    rev, cost = cell("B3"), cell("B4")
    ws["B5"] = rev - cost  # =B3-B4
    ws["B6"] = (rev - cost) / rev  # =(B3-B4)/B3
    ws["B7"] = rng("B3:B10").sum() * 1.2  # =SUM(B3:B10)*1.2

Or let ``Sheet`` hand you the reference as you write, so no coordinate is typed
twice::

    s = Sheet(ws)
    rev, cost = s.put("B2", 1000), s.put("B3", 600)
    s.put("B4", (rev - cost) / rev)  # =(B2-B3)/B2

Expressions are ``str`` subclasses whose value is the finished formula, so they can
be assigned straight to an openpyxl cell.  Nothing here imports openpyxl.
"""

from .expr import BinOp, Expr, Lit, Raw, UnaryOp, lit
from .functions import F, Func
from .refs import CellRef, RangeRef, Ref, cell, col_index, col_letter, rng
from .sheet import Sheet

__all__ = [
    "cell",
    "rng",
    "Ref",
    "F",
    "Sheet",
    "Expr",
    "CellRef",
    "RangeRef",
    "Func",
    "Lit",
    "Raw",
    "BinOp",
    "UnaryOp",
    "lit",
    "col_letter",
    "col_index",
]
