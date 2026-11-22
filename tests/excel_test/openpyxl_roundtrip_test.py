"""End-to-end proof that expressions survive as real formulas in a real workbook.

This is what validates the ``str``-subclass design: an expression is assigned to a
cell with no conversion, no wrapper and no import of pycountant by openpyxl.
"""

import pytest

openpyxl = pytest.importorskip("openpyxl")

from pycountant.excel import F, Ref, cell, rng


@pytest.fixture
def roundtrip(tmp_path):
    """Write cells, save, reload, and hand back the reloaded worksheet."""

    def run(fill):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Model"
        fill(ws)
        path = tmp_path / "book.xlsx"
        wb.save(path)
        return openpyxl.load_workbook(path).active

    return run


def test_expression_assigns_directly_and_is_stored_as_a_formula(roundtrip):
    rev, cost = cell("B3"), cell("B4")

    def fill(ws):
        ws["B3"] = 1000
        ws["B4"] = 600
        ws["B5"] = rev - cost  # no str(), no .formula
        ws["B6"] = (rev - cost) / rev

    ws = roundtrip(fill)
    assert ws["B5"].value == "=B3-B4"
    assert ws["B5"].data_type == "f"
    assert ws["B6"].value == "=(B3-B4)/B3"
    assert ws["B3"].value == 1000  # plain values still behave normally


def test_functions_ranges_and_cross_sheet_survive(roundtrip):
    def fill(ws):
        data = Ref("Source Data")
        ws["B7"] = rng("B3:B10").sum() * 1.2
        ws["B8"] = F.XLOOKUP(cell("B3"), data["A:A"], data["C:C"])
        ws["B9"] = F.IF(cell("B3").gt(cell("B4")), "profit", "loss")

    ws = roundtrip(fill)
    assert ws["B7"].value == "=SUM(B3:B10)*1.2"
    # The _xlfn prefix must be in the saved file, or Excel shows #NAME?.
    assert ws["B8"].value == "=_xlfn.XLOOKUP(B3,'Source Data'!A:A,'Source Data'!C:C)"
    assert ws["B9"].value == '=IF(B3>B4,"profit","loss")'
    assert all(ws[c].data_type == "f" for c in ("B7", "B8", "B9"))


def test_written_into_a_second_sheet(tmp_path):
    wb = openpyxl.Workbook()
    src = wb.active
    src.title = "Source Data"
    out = wb.create_sheet("Summary")
    out["A1"] = Ref(src)["B3"] * 2  # Ref takes the worksheet object itself

    path = tmp_path / "book.xlsx"
    wb.save(path)
    reloaded = openpyxl.load_workbook(path)["Summary"]
    assert reloaded["A1"].value == "='Source Data'!B3*2"


def test_a_bare_reference_is_a_formula_not_text(roundtrip):
    ws = roundtrip(lambda ws: ws.__setitem__("A1", cell("B3")))
    assert ws["A1"].value == "=B3"
    assert ws["A1"].data_type == "f"


def test_ws_cell_and_append_accept_expressions(roundtrip):
    def fill(ws):
        ws.cell(row=1, column=1, value=cell("B1") + cell("B2"))
        ws.append([cell("C1") & "x"])

    ws = roundtrip(fill)
    assert ws["A1"].value == "=B1+B2"
    assert ws["A2"].value == '=C1&"x"'
