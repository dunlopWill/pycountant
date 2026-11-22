"""Recalculate generated workbooks in a real engine.

The static checks in ``functions.py`` catch a misspelled or mis-counted call, and
the type stubs catch it earlier still.  Neither can catch a formula that is
perfectly well-formed and simply wrong -- arguments in the wrong order, a range off
by a row, a reference into an empty cell.  Only an engine that actually evaluates
the sheet finds those, so these tests hand the file to LibreOffice and read back
what it computed.

Marked ``slow``: each case starts a headless soffice, which takes a second or two.
Deselect with ``-m "not slow"``.
"""

import csv
import re
import shutil
import subprocess

import pytest

openpyxl = pytest.importorskip("openpyxl")

from pycountant.excel import F, Raw, Sheet

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice (soffice) is not installed"),
]

# LibreOffice reports Excel's "#NAME?" style for some failures and its own
# "Err:511" style for others, so both have to count as an error.
_ERROR = re.compile(r"^(#[A-Z0-9_/]+[!?]|Err:\d+)$")


@pytest.fixture
def recalc(tmp_path):
    """Write a sheet, evaluate it in LibreOffice, hand back ``{coordinate: value}``.

    The CSV export carries computed *values*, which is the whole point -- the
    formulas openpyxl wrote have no cached result, so anything that comes back had
    to be calculated.
    """

    def run(fill) -> dict[str, str]:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Model"
        fill(Sheet(ws))
        book = tmp_path / "book.xlsx"
        wb.save(book)

        # A private profile keeps this from colliding with a LibreOffice the
        # developer already has open.
        subprocess.run(
            [
                "soffice",
                "--headless",
                f"-env:UserInstallation=file://{tmp_path / 'profile'}",
                "--convert-to",
                "csv",
                "--outdir",
                str(tmp_path),
                str(book),
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )

        values = {}
        with open(tmp_path / "book.csv", newline="") as fh:
            for r, row in enumerate(csv.reader(fh), start=1):
                for c, value in enumerate(row, start=1):
                    if value != "":
                        values[f"{chr(64 + c)}{r}"] = value
        return values

    return run


def test_a_model_recalculates_to_the_expected_numbers(recalc):
    """Values, not just the absence of errors -- this is what catches a wrong formula."""

    def fill(s):
        rev = s.put("B1", 1000)
        cost = s.put("B2", 600)
        s.put("B3", rev - cost)  # 400
        s.put("B4", (rev - cost) / rev)  # 0.4
        s.put("B5", F.IF(rev.gt(cost), "profit", "loss"))
        s.put("B6", F.ROUND(F.SUM(rev, cost) / 3, 2))  # 533.33
        s.put("B7", -(rev**2))  # -1000000, not +1000000
        s.put("B8", rev & " units")  # concatenation, not AND

    out = recalc(fill)
    assert out["B3"] == "400"
    assert out["B4"] == "0.4"
    assert out["B5"] == "profit"
    assert out["B6"] == "533.33"
    assert out["B7"] == "-1000000"
    assert out["B8"] == "1000 units"


def test_precedence_survives_a_real_engine(recalc):
    """The parenthesiser's output has to compute what the Python expression said.

    ``a ** b ** c`` is right-associative in Python, and Excel's bare ``^`` is
    left-associative, so the emitted ``a^(b^c)`` is what makes the engine agree with
    Python.  Asserting 2^81 rather than (2^3)^4 is the whole point: without the
    parentheses this cell would come back as 4096.
    """

    def fill(s):
        a = s.put("A1", 2)
        b = s.put("A2", 3)
        c = s.put("A3", 4)
        s.put("B1", a**b**c)  # 2^(3^4) == 2**81, not (2^3)^4 == 4096
        s.put("B2", a - (b - c))  # 3, not -5
        s.put("B3", a / (b / c))  # 2.666..., not 0.1666...
        s.put("B4", (a + b) * c)  # 20, not 14
        s.put("B5", -(a**2))  # -(2^2) == -4, not (-2)^2 == 4

    out = recalc(fill)
    assert float(out["B1"]) == pytest.approx(float(2**81))
    assert out["B2"] == "3"
    assert out["B3"].startswith("2.66")
    assert out["B4"] == "20"
    assert out["B5"] == "-4"


def test_future_functions_are_not_name_errors(recalc):
    """The _xlfn prefixing is exactly what stops these being #NAME?."""

    def fill(s):
        s.put("A1", 3)
        s.put("A2", 1)
        s.put("A3", 2)
        s.put("C1", F.TEXTJOIN("-", True, s["A1"], s["A2"], s["A3"]))
        s.put("C2", F.MAXIFS(s["A1:A3"], s["A1:A3"], ">1"))

    out = recalc(fill)
    assert not any(_ERROR.match(v) for v in out.values()), out
    assert out["C1"] == "3-1-2"
    assert out["C2"] == "3"


def test_no_cell_in_a_wide_sample_reports_an_error(recalc):
    """A broad sweep -- anything that renders to something Excel cannot parse shows here."""

    def fill(s):
        rev = s.put("A1", 1200)
        s.put("A2", 0.15)
        s.put("B1", F.ROUND(rev * s["A2"], 2))
        s.put("B2", F.IFERROR(rev / 0, "n/a"))
        s.put("B3", F.TEXT(rev, "#,##0"))
        s.put("B4", F.VLOOKUP(1200, s["A1:B1"], 2, False))
        s.put("B5", F.COUNTIF(s["A1:A2"], ">1"))
        s.put("B6", F.EOMONTH(F.DATE(2026, 9, 1), 0))
        s.put("B7", rev.pct())

    out = recalc(fill)
    bad = {k: v for k, v in out.items() if _ERROR.match(v)}
    assert not bad, f"cells evaluated to an error: {bad}"


def test_the_harness_can_actually_detect_a_bad_formula(recalc):
    """Negative control.

    Without this, every test above would still pass if the export silently stopped
    carrying computed values.
    """

    def fill(s):
        s.put("A1", Raw("NOSUCHFUNCTION(1)"))
        s.put("A2", Raw("SUMIF(B:B)"))

    out = recalc(fill)
    assert _ERROR.match(out["A1"]), f"expected an error in A1, got {out.get('A1')!r}"
    assert _ERROR.match(out["A2"]), f"expected an error in A2, got {out.get('A2')!r}"
