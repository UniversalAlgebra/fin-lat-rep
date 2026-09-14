"""
File: scripts/python/finlatrep/test_check.py

Description: Tests for the catalog check, including the regression that shows
  it has teeth.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Sequence

from _utils.pipeline_types import ErrorType
from finlatrep.catalog import read_catalog
from finlatrep.check import (  # noqa: I001
    Comparison,
    check_diagram_count,
    cross_check,
    lattice_index_of,
    parse_uacalc_table,
    run,
)
from finlatrep.ua import Algebra, Operation

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ARTICLE = REPO / "article" / "SmallLatticeReps.tex"
PRE_FIX_B28 = HERE.parent / "fixtures" / "B28-pre-fix.ua"


class NamingTests(unittest.TestCase):
    def test_reads_the_lattice_index_out_of_an_algebra_name(self) -> None:
        self.assertEqual(lattice_index_of("B28"), 28)

    def test_a_suffixed_name_still_names_its_lattice(self) -> None:
        """B4-prime is a second representation of L4, not a different lattice."""
        self.assertEqual(lattice_index_of("B4-prime"), 4)

    def test_a_name_that_is_not_an_algebra_of_the_catalog_is_rejected(self) -> None:
        self.assertIsNone(lattice_index_of("S3group"))


class DiagramCountTests(unittest.TestCase):
    def test_an_algebra_with_no_drawn_lattice_stops_the_run(self) -> None:
        """A diagram moved into an \\input would otherwise be skipped silently."""
        algebra = Algebra("B99", 2, (Operation("f", 1, (0, 1)),))
        outcome = check_diagram_count({}, [algebra])
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.VALIDATION_ERROR)
        self.assertIn("L99", outcome.unwrap_err().message)

    def test_the_real_article_covers_every_algebra_it_should(self) -> None:
        catalog = read_catalog(ARTICLE).unwrap()
        algebra = Algebra("B28", 2, (Operation("f", 1, (0, 1)),))
        self.assertTrue(check_diagram_count(catalog, [algebra]).is_ok)


class RegressionTests(unittest.TestCase):
    r"""The check must fail on the algebra file that was published before #22.

    Without this the suite would only show that the check passes on data that
    is already correct, which pins nothing.  The fixture is the B28 that stood
    in UACalc/AlgebraFiles from 2017-08-02 until 2026-09-13, taken from commit
    9e1ef390ef7a1288cdabdfb449d23c9095c02173.
    """

    def test_the_fixture_is_present(self) -> None:
        self.assertTrue(PRE_FIX_B28.is_file(), f"not found: {PRE_FIX_B28}")

    def test_the_pre_fix_b28_is_reported_as_a_mismatch(self) -> None:
        comparisons = run(PRE_FIX_B28, ARTICLE).unwrap()
        self.assertEqual(len(comparisons), 1)
        self.assertEqual(comparisons[0].algebra, "B28")
        self.assertFalse(comparisons[0].agrees)

    def test_the_pre_fix_b28_has_an_eight_element_congruence_lattice(self) -> None:
        """Eight, where L28 has seven: that is exactly the defect #20 reported."""
        comparison = run(PRE_FIX_B28, ARTICLE).unwrap()[0]
        self.assertEqual(comparison.computed.size, 8)
        self.assertEqual(comparison.drawn.size, 7)

    def test_the_failure_message_names_the_algebra_and_both_relations(self) -> None:
        message = run(PRE_FIX_B28, ARTICLE).unwrap()[0].describe_failure()
        self.assertIn("B28", message)
        self.assertIn("L28", message)
        self.assertIn("8 elements", message)
        self.assertIn("7 elements", message)


class CrossCheckTests(unittest.TestCase):
    """The UACalc table is the second engine's half of the comparison."""

    def _b28(self) -> Sequence[Comparison]:
        return run(PRE_FIX_B28, ARTICLE).unwrap()

    def test_reads_a_well_formed_table(self) -> None:
        sizes = parse_uacalc_table("B1 4 5\nB28 16 7\n").unwrap()
        self.assertEqual(sizes, {"B1": 5, "B28": 7})

    def test_blank_lines_are_ignored(self) -> None:
        self.assertEqual(parse_uacalc_table("\nB1 4 5\n\n").unwrap(), {"B1": 5})

    def test_a_malformed_line_is_an_error(self) -> None:
        outcome = parse_uacalc_table("B1 4\n")
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.PARSING_ERROR)

    def test_agreement_passes(self) -> None:
        """Our own computation says 8 for the pre-fix B28, so 8 is agreement."""
        self.assertTrue(cross_check(self._b28(), {"B28": 8}).is_ok)

    def test_disagreement_is_reported_with_both_numbers(self) -> None:
        outcome = cross_check(self._b28(), {"B28": 7})
        self.assertTrue(outcome.is_err)
        self.assertIn("we compute 8", outcome.unwrap_err().message)
        self.assertIn("UACalc computes 7", outcome.unwrap_err().message)

    def test_an_algebra_absent_from_the_table_is_reported(self) -> None:
        outcome = cross_check(self._b28(), {})
        self.assertTrue(outcome.is_err)
        self.assertIn("absent from the UACalc table", outcome.unwrap_err().message)


class ErrorPathTests(unittest.TestCase):
    def test_a_missing_algebra_file_is_an_error_not_an_exception(self) -> None:
        outcome = run(HERE / "no-such-file.ua", ARTICLE)
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.FILE_NOT_FOUND)

    def test_a_missing_article_is_an_error_not_an_exception(self) -> None:
        outcome = run(PRE_FIX_B28, HERE / "no-such-article.tex")
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.FILE_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
