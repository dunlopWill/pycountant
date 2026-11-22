"""Excel formula expressions built from Python operators.

Every node is a ``str`` subclass whose string value is the finished, ``=``-prefixed
formula, so an expression can be assigned straight to an openpyxl cell::

    ws["B5"] = cell("B3") - cell("B4")  # cell gets "=B3-B4"

Nesting uses :attr:`Expr.text` (the body, without the ``=``) rather than the string
value.  That distinction is the one invariant holding the whole module together.
"""

from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from typing import Self

__all__ = [
    "Expr",
    "BinOp",
    "UnaryOp",
    "Lit",
    "Raw",
    "P_CMP",
    "P_CONCAT",
    "P_ADD",
    "P_MUL",
    "P_POW",
    "P_PCT",
    "P_NEG",
    "P_REF",
    "P_ATOM",
]

# Excel operator precedence, loosest first.  Reference operators bind tightest and
# comparisons loosest; note that unary minus binds *tighter* than "^", which is where
# Excel and Python disagree.
P_CMP = 1  # = <> < <= > >=
P_CONCAT = 2  # &
P_ADD = 3  # + -
P_MUL = 4  # * /
P_POW = 5  # ^
P_PCT = 6  # postfix %
P_NEG = 7  # unary -
P_REF = 8  # : range
P_ATOM = 9  # literals, cell refs, function calls

# Operators where "a op (b op c)" differs from "(a op b) op c", so an equal-precedence
# right operand has to be parenthesised.  "+", "*" and "&" are left out: they regroup
# freely, and omitting the parens keeps the output readable.
_RIGHT_NEEDS_PARENS = frozenset({"-", "/", "^"})


class Expr(str):
    """Base class for every formula fragment.

    The ``str`` value is the complete formula (``"=B3-B4"``); :attr:`text` is the
    body (``"B3-B4"``).  Composition always reads :attr:`text`.
    """

    _text: str
    _prec: int

    def __new__(cls, text: str, prec: int = P_ATOM) -> Self:
        return cls._make(text, prec)

    @classmethod
    def _make(cls, text: str, prec: int) -> Self:
        # Returning Self, not Expr, is what lets each subclass assign its own
        # attributes to the result and return it as its own type.
        obj = str.__new__(cls, "=" + text)
        obj._text = text
        obj._prec = prec
        return obj

    @property
    def text(self) -> str:
        """The formula body, without the leading ``=``."""
        return self._text

    @property
    def formula(self) -> str:
        """The complete formula as a plain ``str``, including the leading ``=``."""
        return "=" + self._text

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._text!r})"

    # -- composition ------------------------------------------------------------
    def _operand(self, parent_prec: int, *, right: bool = False, op: str = "") -> str:
        """This expression's text, parenthesised only if the parent would misread it."""
        if self._prec < parent_prec:
            return f"({self._text})"
        if right and self._prec == parent_prec and op in _RIGHT_NEEDS_PARENS:
            return f"({self._text})"
        return self._text

    def shift(self, rows: int = 0, cols: int = 0) -> Expr:
        """Return a copy with every *relative* reference moved by ``rows``/``cols``.

        Absolute (``$``-locked) components are left alone.  Nodes without references
        return themselves.
        """
        return self

    # -- arithmetic -------------------------------------------------------------
    def __add__(self, other):
        return BinOp("+", self, other, P_ADD)

    def __radd__(self, other):
        return BinOp("+", other, self, P_ADD)

    def __sub__(self, other):
        return BinOp("-", self, other, P_ADD)

    def __rsub__(self, other):
        return BinOp("-", other, self, P_ADD)

    def __mul__(self, other):
        return BinOp("*", self, other, P_MUL)

    def __rmul__(self, other):
        return BinOp("*", other, self, P_MUL)

    def __truediv__(self, other):
        return BinOp("/", self, other, P_MUL)

    def __rtruediv__(self, other):
        return BinOp("/", other, self, P_MUL)

    def __pow__(self, other):
        return BinOp("^", self, other, P_POW)

    def __rpow__(self, other):
        return BinOp("^", other, self, P_POW)

    # Excel's "&" is string concatenation, not boolean AND.  Use F.AND(...) for that.
    def __and__(self, other):
        return BinOp("&", self, other, P_CONCAT)

    def __rand__(self, other):
        return BinOp("&", other, self, P_CONCAT)

    def __neg__(self):
        return UnaryOp("-", self)

    def __pos__(self):
        return self

    def __mod__(self, other):
        raise TypeError(
            "'%' is not an Excel binary operator (and would otherwise be Python "
            "string formatting here). Use F.MOD(a, b), or .pct() for a postfix %."
        )

    __rmod__ = __mod__

    def pct(self) -> Expr:
        """Postfix percent: ``x.pct()`` renders ``x%``."""
        return UnaryOp("%", self, postfix=True)

    # -- comparisons ------------------------------------------------------------
    # Deliberately methods rather than operator overloads, so "==" and hash() keep
    # their native str behaviour and expressions stay usable as dict keys.
    def eq(self, other):
        return BinOp("=", self, other, P_CMP)

    def ne(self, other):
        return BinOp("<>", self, other, P_CMP)

    def lt(self, other):
        return BinOp("<", self, other, P_CMP)

    def le(self, other):
        return BinOp("<=", self, other, P_CMP)

    def gt(self, other):
        return BinOp(">", self, other, P_CMP)

    def ge(self, other):
        return BinOp(">=", self, other, P_CMP)


def lit(value) -> Expr:
    """Coerce a Python value into an :class:`Expr`, passing existing ones through."""
    return value if isinstance(value, Expr) else Lit(value)


class Lit(Expr):
    """A Python value rendered as an Excel literal."""

    _value: object

    def __new__(cls, value) -> Lit:
        text, prec = _render_literal(value)
        obj = cls._make(text, prec)
        obj._value = value
        return obj


def _render_literal(value) -> tuple[str, int]:
    """Render a Python value, with the precedence of the text produced."""
    if value is None:
        return "", P_ATOM
    # bool before int: bool is an int subclass and would otherwise render as 1/0.
    if isinstance(value, bool):
        return ("TRUE" if value else "FALSE"), P_ATOM
    if isinstance(value, (int, float, Decimal)):
        text = repr(value) if isinstance(value, float) else str(value)
        # A negative number carries a leading "-", so it needs unary-minus precedence.
        return text, (P_NEG if text.startswith("-") else P_ATOM)
    if isinstance(value, str):
        return '"' + value.replace('"', '""') + '"', P_ATOM
    if isinstance(value, _dt.datetime):
        date = f"DATE({value.year},{value.month},{value.day})"
        if (value.hour, value.minute, value.second) == (0, 0, 0):
            return date, P_ATOM
        # DATE(...)+TIME(...) really is an addition, so it must be able to parenthesise.
        return f"{date}+TIME({value.hour},{value.minute},{value.second})", P_ADD
    if isinstance(value, _dt.date):
        return f"DATE({value.year},{value.month},{value.day})", P_ATOM
    if isinstance(value, _dt.time):
        return f"TIME({value.hour},{value.minute},{value.second})", P_ATOM
    raise TypeError(
        f"cannot render {type(value).__name__} as an Excel literal; "
        "wrap it with Raw(...) if you know the formula text you want"
    )


class Raw(Expr):
    """Verbatim formula text.

    Parenthesised whenever it is nested, because its internal structure is unknown
    and ``Raw("A1+B1") * 2`` must not silently become ``A1+B1*2``.  Pass
    ``atomic=True`` when the text is a single self-contained term.
    """

    def __new__(cls, text: str, *, atomic: bool = False) -> Raw:
        return cls._make(text, P_ATOM if atomic else P_CMP)


class BinOp(Expr):
    """A binary operation between two expressions."""

    op: str
    left: Expr
    right: Expr

    def __new__(cls, op: str, left, right, prec: int) -> BinOp:
        left, right = lit(left), lit(right)
        text = left._operand(prec) + op + right._operand(prec, right=True, op=op)
        obj = cls._make(text, prec)
        obj.op, obj.left, obj.right = op, left, right
        return obj

    def shift(self, rows: int = 0, cols: int = 0) -> BinOp:
        return BinOp(
            self.op,
            self.left.shift(rows, cols),
            self.right.shift(rows, cols),
            self._prec,
        )


class UnaryOp(Expr):
    """A prefix (``-``) or postfix (``%``) operation."""

    op: str
    operand: Expr
    postfix: bool

    def __new__(cls, op: str, operand, *, postfix: bool = False) -> UnaryOp:
        operand = lit(operand)
        prec = P_PCT if postfix else P_NEG
        body = operand._operand(prec)
        obj = cls._make(body + op if postfix else op + body, prec)
        obj.op, obj.operand, obj.postfix = op, operand, postfix
        return obj

    def shift(self, rows: int = 0, cols: int = 0) -> UnaryOp:
        return UnaryOp(self.op, self.operand.shift(rows, cols), postfix=self.postfix)
