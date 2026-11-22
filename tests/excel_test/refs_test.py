import pytest

from pycountant.excel import CellRef, Ref, cell, col_index, col_letter, rng


@pytest.mark.parametrize(
    "index, letters",
    [
        (1, "A"),
        (26, "Z"),
        (27, "AA"),
        (52, "AZ"),
        (53, "BA"),
        (702, "ZZ"),
        (703, "AAA"),
        (16384, "XFD"),
    ],
)
def test_column_boundaries(index, letters):
    assert col_letter(index) == letters
    assert col_index(letters) == index


def test_column_roundtrip():
    for i in list(range(1, 800)) + [16383, 16384]:
        assert col_index(col_letter(i)) == i


@pytest.mark.parametrize("bad", [0, -1, 16385])
def test_column_out_of_range(bad):
    with pytest.raises(ValueError):
        col_letter(bad)


def test_construction_forms_agree():
    assert cell("B3") == cell(3, 2) == CellRef(3, 2)
    assert cell("B3").row == 3
    assert cell("B3").col == 2


def test_absolute_markers():
    assert str(cell("B3").abs()) == "=$B$3"
    assert str(cell("B3").abs_r()) == "=B$3"
    assert str(cell("B3").abs_c()) == "=$B3"
    assert str(cell("$B$3")) == "=$B$3"  # parsed from the string
    assert str(cell("$B$3").rel()) == "=B3"
    assert str(cell("B3", abs_col=True)) == "=$B3"


def test_offset_crosses_column_z():
    assert str(cell("Z1").offset(cols=1)) == "=AA1"
    assert str(cell("AA1").offset(cols=-1)) == "=Z1"
    assert str(cell("B3").offset(rows=2, cols=1)) == "=C5"
    # offset moves the cell regardless of locking; shift is the one that respects it.
    assert str(cell("$B$3").offset(rows=2)) == "=$B$5"


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Data", "Data!B3"),
        ("Source Data", "'Source Data'!B3"),
        ("2024", "'2024'!B3"),
        ("P&L", "'P&L'!B3"),
        ("Bob's Sheet", "'Bob''s Sheet'!B3"),
    ],
)
def test_sheet_quoting(name, expected):
    assert cell("B3", sheet=name).text == expected


def test_ref_factory_duck_types_a_worksheet():
    class FakeWorksheet:
        title = "Source Data"

    data = Ref(FakeWorksheet())
    assert data["B3"].text == "'Source Data'!B3"
    assert data["A:A"].text == "'Source Data'!A:A"
    assert data.cell(3, 2).text == "'Source Data'!B3"


def test_ranges():
    assert str(rng("B3:B10")) == "=B3:B10"
    assert str(rng("B:B")) == "=B:B"
    assert str(rng("3:3")) == "=3:3"
    assert str(cell("B3").to(cell("D5"))) == "=B3:D5"
    assert str(rng("B3:B10", sheet="Data")) == "=Data!B3:B10"


def test_range_takes_sheet_from_its_cells():
    start, end = cell("B3", sheet="Data"), cell("B10", sheet="Data")
    assert str(start.to(end)) == "=Data!B3:B10"


@pytest.mark.parametrize("bad", ["B3", "B3:", ":B3", "B3:!!", "Q"])
def test_invalid_ranges_rejected(bad):
    with pytest.raises((ValueError, TypeError)):
        rng(bad)


def test_shift_respects_absolute_components():
    assert str(cell("B3").shift(rows=1, cols=1)) == "=C4"
    assert str(cell("$B$3").shift(rows=1, cols=1)) == "=$B$3"
    assert str(cell("$B3").shift(rows=1, cols=1)) == "=$B4"
    assert str(cell("B$3").shift(rows=1, cols=1)) == "=C$3"
    assert str(rng("B3:B10").shift(rows=-1)) == "=B2:B9"
    assert str(rng("$B$3:$B$10").shift(rows=-1)) == "=$B$3:$B$10"
    assert str(rng("B:B").shift(cols=1)) == "=C:C"
    assert str(rng("3:3").shift(rows=1)) == "=4:4"


def test_shift_walks_the_whole_expression():
    from pycountant.excel import F

    expr = F.ROUND((cell("B3") - cell("B4")) / cell("$A$1"), 2)
    assert str(expr) == "=ROUND((B3-B4)/$A$1,2)"
    # Deleting a row above means re-pointing every relative ref by hand; openpyxl
    # will not do it for you.
    assert str(expr.shift(rows=-1)) == "=ROUND((B2-B3)/$A$1,2)"


def test_refs_stay_hashable_and_comparable_as_strings():
    # "==" was deliberately left un-overloaded, so refs still work as dict keys.
    seen = {cell("B3"): "revenue"}
    assert seen[cell("B3")] == "revenue"
    assert cell("B3") == cell("B3")
    assert cell("B3") != cell("B4")
