import datetime as dt
from decimal import Decimal

import pytest

from pycountant.excel import F, Func, Lit, cell, rng
from pycountant.excel.functions import _XLFN, _XLWS, stored_name


def test_call_and_nesting():
    assert str(F.SUM(rng("A1:A9"))) == "=SUM(A1:A9)"
    assert str(F.SUM(cell("A1"), cell("A2"))) == "=SUM(A1,A2)"
    assert str(F.IF(cell("A1").gt(0), F.SUM(rng("B:B")), 0)) == "=IF(A1>0,SUM(B:B),0)"


def test_any_function_name_works():
    assert str(F.SOME_ADDIN(cell("A1"))) == "=SOME_ADDIN(A1)"
    # Double underscore stands in for the dot in names like STDEV.S.
    assert str(F.STDEV__S(rng("A1:A9"))) == "=_xlfn.STDEV.S(A1:A9)"


def test_omitted_argument():
    assert str(F.VLOOKUP(cell("A1"), rng("B:D"), 3, None)) == "=VLOOKUP(A1,B:D,3,)"


def test_range_aggregate_helpers():
    r = rng("B3:B10")
    assert str(r.sum()) == "=SUM(B3:B10)"
    assert str(r.average()) == "=AVERAGE(B3:B10)"
    assert str(r.counta()) == "=COUNTA(B3:B10)"
    assert str(r.min()) == "=MIN(B3:B10)"


@pytest.mark.parametrize(
    "value, expected",
    [
        (1, "1"),
        (-5, "-5"),
        (1.5, "1.5"),
        (Decimal("2.50"), "2.50"),
        (True, "TRUE"),
        (False, "FALSE"),
        ("text", '"text"'),
        ('say "hi"', '"say ""hi"""'),
        ("", '""'),
        (dt.date(2026, 9, 1), "DATE(2026,9,1)"),
        (dt.datetime(2026, 9, 1), "DATE(2026,9,1)"),
    ],
)
def test_literals(value, expected):
    assert Lit(value).text == expected


def test_bool_is_checked_before_int():
    # bool is an int subclass; rendering it as 1/0 would be wrong.
    assert Lit(True).text == "TRUE"
    assert str(F.IF(cell("A1"), True, False)) == "=IF(A1,TRUE,FALSE)"


def test_datetime_with_a_time_can_still_be_nested():
    stamp = dt.datetime(2026, 9, 1, 13, 30)
    assert Lit(stamp).text == "DATE(2026,9,1)+TIME(13,30,0)"
    # It renders as an addition, so it must parenthesise inside a multiplication.
    assert str(Lit(stamp) * 2) == "=(DATE(2026,9,1)+TIME(13,30,0))*2"


def test_unrenderable_literal_is_rejected():
    with pytest.raises(TypeError, match="Raw"):
        Lit(object())


def test_future_functions_get_their_prefix():
    assert (
        str(F.XLOOKUP(cell("A1"), rng("B:B"), rng("C:C")))
        == "=_xlfn.XLOOKUP(A1,B:B,C:C)"
    )
    assert (
        str(F.TEXTJOIN(", ", True, rng("A1:A9"))) == '=_xlfn.TEXTJOIN(", ",TRUE,A1:A9)'
    )
    assert (
        str(F.IFS(cell("A1").gt(0), "up", True, "down"))
        == '=_xlfn.IFS(A1>0,"up",TRUE,"down")'
    )


def test_dynamic_array_functions_get_the_worksheet_prefix():
    assert (
        str(F.FILTER(rng("A:A"), rng("B:B").gt(0))) == "=_xlfn._xlws.FILTER(A:A,B:B>0)"
    )
    assert str(F.SORT(rng("A1:C9"))) == "=_xlfn._xlws.SORT(A1:C9)"
    assert _XLWS == {"FILTER", "SORT"}


def test_every_table_entry_renders_with_its_prefix():
    # check=False: this is about the prefix, not the argument count, and many of
    # these names legitimately require arguments.
    for name in _XLFN:
        assert Func(name, check=False).text == f"_xlfn.{name}()"
    for name in _XLWS:
        assert Func(name, check=False).text == f"_xlfn._xlws.{name}()"
    assert _XLFN.isdisjoint(_XLWS)


def test_pre_2010_functions_are_left_alone():
    for name in ("SUM", "IF", "VLOOKUP", "IFERROR", "SUMIFS", "INDEX", "MATCH"):
        assert stored_name(name) == name


def test_prefix_lookup_is_case_insensitive():
    assert stored_name("xlookup") == "_xlfn.XLOOKUP"
    assert str(F.xlookup(cell("A1"), rng("B:B"), rng("C:C"))).startswith(
        "=_xlfn.XLOOKUP"
    )
