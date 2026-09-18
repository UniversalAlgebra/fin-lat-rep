"""
File: scripts/python/_utils/run_tests.py

Run unittest suites and print one line per test, so that `make test` (and so
`make verify`) says what was tested and which file tested it, rather than a
row of dots.  A line reads

    ✅ finlatrep/test_ua.py  a short table is rejected

or starts with ❌ for a failure or error, whose traceback is printed after the
suite.  The description is the first line of the test's docstring when it has
one (its first sentence, however many lines it wraps over), otherwise the method
name with `test_` dropped and underscores turned into spaces; naming a test well
is what makes this output read well.

Tests' own stdout and stderr are buffered and shown only for a test that fails.
Several tests exercise error paths that print usage messages, and those used to
land in the middle of the dots.

Usage, from scripts/python with PYTHONPATH=. (the Makefile does this):

    python3 -m _utils.run_tests _utils finlatrep

Exit status 0 when every test passed, 1 otherwise, as unittest's own runner.
"""

from __future__ import annotations

import inspect
import re
import sys
import unittest
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Sequence, cast
from unittest.runner import _WritelnDecorator

if TYPE_CHECKING:
    from _typeshed import OptExcInfo

# scripts/python, the directory test files are named relative to.
ROOT = Path(__file__).resolve().parents[1]

PASS = "✅"
FAIL = "❌"
SKIP = "⚪"


def relative_source(test: unittest.TestCase) -> str:
    """The test's file relative to scripts/python, as `finlatrep/test_ua.py`."""
    source = inspect.getsourcefile(type(test))
    if source is None:
        return type(test).__module__
    path = Path(source).resolve()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def first_sentence(doc: str) -> str:
    """The first sentence of a docstring's first paragraph, on one line.

    unittest's own shortDescription() takes the first physical line, which
    cuts a wrapped sentence in the middle; a sentence is the unit that says
    what a test tests.
    """
    paragraph = inspect.cleandoc(doc).split("\n\n")[0]
    flat = " ".join(paragraph.split())
    match = re.match(r"(.*?[.!?])(?:\s|$)", flat)
    return match.group(1) if match else flat


def describe(test: unittest.TestCase) -> str:
    """What the test tests: its docstring's first sentence, else its name in words."""
    method = test.id().rsplit(".", 1)[-1]
    doc = getattr(getattr(type(test), method, None), "__doc__", None)
    if doc:
        return first_sentence(doc)
    words = method[len("test_"):] if method.startswith("test_") else method
    return words.replace("_", " ")


class LineResult(unittest.TextTestResult):
    """A TextTestResult that prints one marked line per test as it finishes."""

    def _line(self, mark: str, test: unittest.TestCase, suffix: str = "") -> None:
        self.stream.write(f"{mark} {relative_source(test)}  {describe(test)}{suffix}\n")
        self.stream.flush()

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        self._line(PASS, test)

    def addFailure(self, test: unittest.TestCase, err: OptExcInfo) -> None:
        super().addFailure(test, err)
        self._line(FAIL, test)

    def addError(self, test: unittest.TestCase, err: OptExcInfo) -> None:
        super().addError(test, err)
        self._line(FAIL, test, "  (error, not a failed assertion)")

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        self._line(SKIP, test, f"  (skipped: {reason})")

    def addExpectedFailure(self, test: unittest.TestCase, err: OptExcInfo) -> None:
        super().addExpectedFailure(test, err)
        self._line(PASS, test, "  (failed, as expected)")

    def addUnexpectedSuccess(self, test: unittest.TestCase) -> None:
        super().addUnexpectedSuccess(test)
        self._line(FAIL, test, "  (passed, but was expected to fail)")


def run_suite(suite_dir: str) -> bool:
    """Run every test_*.py under scripts/python/<suite_dir>; True when all passed."""
    suite = unittest.TestLoader().discover(
        start_dir=str(ROOT / suite_dir), pattern="test_*.py", top_level_dir=str(ROOT)
    )
    # A factory rather than the class itself, because typeshed types
    # `resultclass` as a callable of exactly three positional arguments whose
    # first is a stream protocol, while TextTestResult's stream type defaults
    # to _WritelnDecorator.  That is the class TextTestRunner actually wraps
    # its stream in before calling this, so the cast states a fact.
    runner = unittest.TextTestRunner(
        stream=sys.stdout,
        resultclass=lambda stream, descriptions, verbosity: LineResult(
            cast(_WritelnDecorator, stream), descriptions, verbosity
        ),
        verbosity=0,
        buffer=True,
    )
    result = runner.run(suite)
    failed = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
    if failed:
        print(f"{FAIL} _utils/run_tests.py  {suite_dir}: {failed} of {result.testsRun} tests failed")
    else:
        print(f"{PASS} _utils/run_tests.py  {suite_dir}: all {result.testsRun} tests passed")
    return failed == 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    suites = list(sys.argv[1:] if argv is None else argv) or ["_utils", "finlatrep"]
    outcomes = [run_suite(s) for s in suites]
    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
