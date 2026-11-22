"""Arity and spelling checks on function calls.

Both exist to move a failure that would otherwise surface as ``#VALUE!`` or
``#NAME?`` -- on someone else's screen, hours later -- onto the line that wrote it.
The design rule throughout: a name we know is checked, a name we do not know is
left alone, because the set of real Excel functions is open.
"""

import ast
import warnings
from pathlib import Path

import pytest

from pycountant.excel import F, Func, cell, functions, rng
from pycountant.excel.functions import (
    _ARITY,
    _KNOWN,
    _XLFN,
    _XLWS,
    UnknownFunctionWarning,
)

R = rng("A:A")
C = cell("A1")


# The deliberately-wrong calls below are rejected by functions.pyi as well as at
# run time, which is the stubs working -- hence the pyright ignores.

# -- arity ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "build, message",
    [
        (lambda: F.SUMIF(R), "SUMIF takes 2 to 3 arguments, got 1"),  # pyright: ignore[reportCallIssue]
        (lambda: F.SUMIF(R, ">5", R, "extra"), "SUMIF takes 2 to 3 arguments, got 4"),  # pyright: ignore[reportCallIssue]
        (lambda: F.SUM(), "SUM takes at least 1 argument, got 0"),  # pyright: ignore[reportCallIssue]
        (lambda: F.ROUND(C), "ROUND takes exactly 2 arguments, got 1"),  # pyright: ignore[reportCallIssue]
        (lambda: F.TODAY(C), "TODAY takes exactly 0 arguments, got 1"),  # pyright: ignore[reportCallIssue]
        (lambda: F.VLOOKUP(C, R), "VLOOKUP takes 3 to 4 arguments, got 2"),  # pyright: ignore[reportCallIssue]
        (lambda: F.COUNTIF(R), "COUNTIF takes exactly 2 arguments, got 1"),  # pyright: ignore[reportCallIssue]
    ],
)
def test_wrong_argument_count_raises(build, message):
    with pytest.raises(TypeError, match=message.replace("(", r"\(")):
        build()


@pytest.mark.parametrize(
    "build",
    [
        lambda: F.SUMIF(R, ">5"),
        lambda: F.SUMIF(R, ">5", rng("B:B")),
        lambda: F.SUM(C),
        lambda: F.SUM(C, C, C, C, C),
        lambda: F.TODAY(),
        lambda: F.ROW(),
        lambda: F.ROW(C),
        lambda: F.VLOOKUP(C, rng("A:D"), 3),
        lambda: F.VLOOKUP(C, rng("A:D"), 3, False),
        lambda: F.XLOOKUP(C, R, R),
    ],
)
def test_valid_calls_are_untouched(build):
    assert str(build()).startswith("=")


def test_an_omitted_argument_still_counts():
    # None means "argument left blank", not "argument not passed".
    assert str(F.VLOOKUP(C, rng("B:D"), 3, None)) == "=VLOOKUP(A1,B:D,3,)"


def test_check_false_is_the_escape_hatch():
    # check=False turns off the *runtime* check.  A stub signature cannot depend on
    # a runtime flag, so a type checker still sees the arity error -- Func(...)
    # takes *args and is the escape hatch that satisfies both.
    assert str(F.SUMIF(R, check=False)) == "=SUMIF(A:A)"  # pyright: ignore[reportCallIssue]
    assert str(Func("ROUND", C, check=False)) == "=ROUND(A1)"


def test_unknown_names_are_never_arity_checked():
    # The open set is the point: an add-in can have any signature at all.
    assert str(F.SOME_ADDIN_FUNCTION()) == "=SOME_ADDIN_FUNCTION()"
    assert (
        str(F.BLOOMBERG_BDP(C, "PX_LAST", 1, 2, 3))
        == '=BLOOMBERG_BDP(A1,"PX_LAST",1,2,3)'
    )


def test_shifting_a_call_does_not_re_check_it():
    # Built with check=False, so re-validating on shift would raise.
    unchecked = F.SUMIF(rng("B3:B10"), check=False)  # pyright: ignore[reportCallIssue]
    assert str(unchecked.shift(rows=1)) == "=SUMIF(B4:B11)"


def test_arity_is_case_insensitive():
    with pytest.raises(TypeError, match="ROUND takes exactly 2"):
        F.round(C)


# -- spelling ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "build, suggestion",
    [
        (lambda: F.SUMIFF(R, ">5"), "SUMIF"),
        (lambda: F.VLOOOKUP(C, R, 3), "VLOOKUP"),
        (lambda: F.AVERGE(R), "AVERAGE"),
        (lambda: F.IFERRORR(C, 0), "IFERROR"),
        (lambda: F.XLOOKUPP(C, R, R), "XLOOKUP"),
    ],
)
def test_near_miss_names_warn_with_a_suggestion(build, suggestion):
    with pytest.warns(UnknownFunctionWarning, match=suggestion):
        build()


@pytest.mark.parametrize(
    "build",
    [
        lambda: F.SOME_ADDIN_FUNCTION(C),
        lambda: F.BLOOMBERG_BDP(C, "PX_LAST"),
        lambda: F.MY__CUSTOM__THING(C),
        lambda: F.SUM(R),
        lambda: F.XLOOKUP(C, R, R),
        lambda: F.STDEV__S(R),
    ],
)
def test_names_that_must_not_warn(build):
    """A false warning on a legitimate add-in name is worse than a missed typo."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        build()


def test_a_misspelling_still_renders():
    # It warns rather than raising, so an unrecognised name is never a hard stop.
    with pytest.warns(UnknownFunctionWarning):
        assert str(F.SUMIFF(R, ">5")) == '=SUMIFF(A:A,">5")'


def test_check_false_silences_the_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert str(F.SUMIFF(R, ">5", check=False)) == '=SUMIFF(A:A,">5")'


# -- the tables themselves ---------------------------------------------------------


def test_arity_bounds_are_coherent():
    for name, (low, high) in _ARITY.items():
        assert name == name.upper(), name
        assert low >= 0, name
        assert high is None or high >= low, name


def test_known_names_cover_both_tables():
    assert _XLFN <= _KNOWN and _XLWS <= _KNOWN
    assert set(_ARITY) <= _KNOWN


def test_every_arity_entry_is_actually_wired_up():
    """Each entry must really fire -- a key misspelt against _XLFN would sit inert.

    Stronger than comparing spellings: it exercises the lookup the same way a
    caller does, so a name that can never be reached shows up here.
    """
    for name, (low, high) in _ARITY.items():
        if low >= 1:
            with pytest.raises(TypeError, match="argument"):
                Func(name)
        if high is not None:
            with pytest.raises(TypeError, match="argument"):
                Func(name, *([1] * (high + 1)))


def test_dotted_names_reach_their_arity_entry_through_F():
    # F.STDEV__S -> "STDEV.S": the double-underscore spelling has to land on the
    # same key the table uses, prefixed (STDEV.S) or not (ERROR.TYPE).
    with pytest.raises(TypeError, match="STDEV.S takes at least 1"):
        F.STDEV__S()
    with pytest.raises(TypeError, match="ERROR.TYPE takes exactly 1"):
        F.ERROR__TYPE()
    assert str(F.ERROR__TYPE(C)) == "=ERROR.TYPE(A1)"
    assert str(F.STDEV__S(R)) == "=_xlfn.STDEV.S(A:A)"


def _stub_arity():
    """Read ``(min, max)`` per function out of ``functions.pyi``.

    The stub states the same argument counts as ``_ARITY``, in a form only a type
    checker reads, so nothing at run time makes the two agree.  Parsing it here is
    what turns that into a test.
    """
    stub_path = Path(functions.__file__).with_suffix(".pyi")
    assert stub_path.is_file(), f"the type stub is missing: {stub_path}"
    tree = ast.parse(stub_path.read_text(encoding="utf-8"))
    cls = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "_Functions"
    )

    bounds = {}
    for node in cls.body:
        # Excel names are upper case; this skips __getattr__ and __dir__.
        if not isinstance(node, ast.FunctionDef) or not node.name[0].isupper():
            continue
        args = node.args
        # "check" is keyword-only, so it lands in kwonlyargs and is not counted.
        positional = [a for a in args.posonlyargs + args.args if a.arg != "self"]
        low = len(positional) - len(args.defaults)
        high = None if args.vararg else len(positional)
        bounds[node.name] = (low, high)
    return bounds


def test_the_stub_declares_the_same_arity_as_the_table():
    """functions.pyi and _ARITY encode the same counts; neither one checks the other.

    Editing one and forgetting the other leaves the editor and the interpreter
    disagreeing about a call -- and both stay green, because the stub is invisible
    at run time and the table is invisible to a type checker.
    """
    stub = _stub_arity()
    assert stub, "no signatures parsed out of functions.pyi"

    # A stub signature enforcing a count the runtime does not check would mean the
    # two layers disagree about whether the name is checked at all.
    assert set(stub) <= set(_ARITY), sorted(set(stub) - set(_ARITY))

    disagree = {
        name: (got, _ARITY[name]) for name, got in stub.items() if got != _ARITY[name]
    }
    assert not disagree, f"stub vs _ARITY (stub, table): {disagree}"

    # Deliberately not asserted the other way: _ARITY covers far more names than the
    # stub does, and dotted ones like STDEV.S cannot be written as identifiers at all.
