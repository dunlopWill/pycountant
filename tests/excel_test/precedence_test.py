"""Parenthesisation is the load-bearing part: wrong parens give silently wrong numbers."""

import pytest

from pycountant.excel import F, Raw, cell, rng

A, B, C = cell("A1"), cell("A2"), cell("A3")


@pytest.mark.parametrize(
    "expr, expected",
    [
        # The bug this library exists to prevent.
        ((A - B) / A, "=(A1-A2)/A1"),
        (A - B / A, "=A1-A2/A1"),
        # No gratuitous parens: output should read like something a person wrote.
        (A + B + C, "=A1+A2+A3"),
        (A * B * C, "=A1*A2*A3"),
        (A + B * C, "=A1+A2*A3"),
        ((A + B) * C, "=(A1+A2)*A3"),
        # Non-associative operators need parens on an equal-precedence right operand.
        (A - (B - C), "=A1-(A2-A3)"),
        (A - B - C, "=A1-A2-A3"),
        (A / (B / C), "=A1/(A2/A3)"),
        (A / B / C, "=A1/A2/A3"),
        (A / (B * C), "=A1/(A2*A3)"),
        # Concatenation sits between "+ -" and comparisons.
        (A & B, "=A1&A2"),
        ((A + B) & C, "=A1+A2&A3"),
        (A & (B + C), "=A1&A2+A3"),
        ((A & B).eq("x"), '=A1&A2="x"'),
        (A.gt(B + C), "=A1>A2+A3"),
        # Percent is postfix and binds tighter than "^".
        (A.pct(), "=A1%"),
        ((A + B).pct(), "=(A1+A2)%"),
    ],
)
def test_rendering(expr, expected):
    assert str(expr) == expected


@pytest.mark.parametrize(
    "expr, expected",
    [
        # Python's "**" is right-associative; Excel's "^" is left-associative, so the
        # grouping Python parsed has to be made explicit or the value changes.
        (A**B**C, "=A1^(A2^A3)"),
        ((A**B) ** C, "=A1^A2^A3"),
        # Python: -x**2 == -(x**2).  Excel: unary minus binds tighter than "^", so a
        # bare "-A1^2" would mean (-A1)^2.  The parens preserve Python's meaning.
        (-(A**2), "=-(A1^2)"),
        ((-A) ** 2, "=-A1^2"),
        (-A + B, "=-A1+A2"),
        (-(A + B), "=-(A1+A2)"),
    ],
)
def test_python_excel_associativity_mismatches(expr, expected):
    assert str(expr) == expected


def test_reflected_operators():
    assert str(1000 - A) == "=1000-A1"
    assert str(2 * A) == "=2*A1"
    assert str(1 / A) == "=1/A1"
    assert str("x" & A) == '="x"&A1'


def test_deeply_nested_keeps_meaning():
    growth = (B - A) / A
    assert str(F.ROUND(growth * 100, 1)) == "=ROUND((A2-A1)/A1*100,1)"
    assert str(F.IF(growth.gt(0), growth, 0)) == "=IF((A2-A1)/A1>0,(A2-A1)/A1,0)"


def test_range_in_arithmetic():
    total = rng("B3:B10").sum()
    assert str(total / rng("C3:C10").sum()) == "=SUM(B3:B10)/SUM(C3:C10)"


def test_raw_is_parenthesised_when_nested():
    # Structure is unknown, so assume the worst rather than emit "A1+B1*2".
    assert str(Raw("A1+B1") * 2) == "=(A1+B1)*2"
    assert str(Raw("A1+B1")) == "=A1+B1"
    assert str(Raw("SUM(A:A)", atomic=True) * 2) == "=SUM(A:A)*2"


def test_modulo_is_rejected():
    # Inherited str.__mod__ would silently do printf formatting here.
    with pytest.raises(TypeError, match="F.MOD"):
        A % 2
