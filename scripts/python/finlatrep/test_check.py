"""
File: scripts/python/finlatrep/test_check.py

Description: Tests for the catalog check, including the regression that shows
  it has teeth.
"""

from __future__ import annotations

import hashlib
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
    UACalcRow,
    parse_uacalc_table,
    run,
)
from finlatrep.ua import Algebra, Operation

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ARTICLE = REPO / "article" / "SmallLatticeReps.tex"
PRE_FIX_B28 = HERE.parent / "fixtures" / "B28-pre-fix.ua"
CORRECT_B1_B28 = HERE.parent / "fixtures" / "B1-B28-correct.ua"
# Recorded here rather than inside the fixture, which cannot contain its own
# checksum.  Taken from AlgebraFiles commit 9e1ef390.
CORRECT_SHA256 = "294f8ab03c4f66d2bc7b97ca32a498d2f620887b8e283dbf3a5a6f4c5d2c417d"
FIXTURE_SHA256 = "8369d4447d5b3403d9621aadb45c3864b1925cc567843db4e866b87efc53ade6"


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

    def test_the_fixture_is_the_algebra_it_claims_to_be(self) -> None:
        """Pin the fixture by checksum, not just by provenance comment.

        The whole suite's claim to have teeth rests on this file being the
        defective B28 and not something that drifted.  An accidental edit
        would otherwise turn the regression test into a test of whatever the
        file became.
        """
        digest = hashlib.sha256(PRE_FIX_B28.read_bytes()).hexdigest()
        self.assertEqual(digest, FIXTURE_SHA256)

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
        rows = parse_uacalc_table("B1 4 5\nB28 16 7\n").unwrap()
        self.assertEqual(rows["B1"], UACalcRow(cardinality=4, congruences=5))
        self.assertEqual(rows["B28"], UACalcRow(cardinality=16, congruences=7))

    def test_blank_lines_are_ignored(self) -> None:
        rows = parse_uacalc_table("\nB1 4 5\n\n").unwrap()
        self.assertEqual(rows, {"B1": UACalcRow(cardinality=4, congruences=5)})

    def test_a_malformed_line_is_an_error(self) -> None:
        outcome = parse_uacalc_table("B1 4\n")
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.PARSING_ERROR)

    def test_a_non_numeric_cardinality_is_an_error(self) -> None:
        self.assertTrue(parse_uacalc_table("B1 four 5\n").is_err)

    def test_agreement_passes(self) -> None:
        """Our own reading of the pre-fix B28 is |A| = 16 with 8 congruences."""
        row = UACalcRow(cardinality=16, congruences=8)
        self.assertTrue(cross_check(self._b28(), {"B28": row}).is_ok)

    def test_disagreement_on_congruences_is_reported_with_both_numbers(self) -> None:
        outcome = cross_check(self._b28(), {"B28": UACalcRow(16, 7)})
        self.assertTrue(outcome.is_err)
        self.assertIn("we compute 8", outcome.unwrap_err().message)
        self.assertIn("UACalc computes 7", outcome.unwrap_err().message)

    def test_a_table_from_a_different_algebra_file_is_caught(self) -> None:
        """The congruence count alone can coincide; the cardinality gives it away.

        Without comparing |A| a stale table reads as agreement whenever a name
        and a congruence count happen to match, which is exactly when a
        mismatched table is hardest to notice.
        """
        outcome = cross_check(self._b28(), {"B28": UACalcRow(cardinality=99, congruences=8)})
        self.assertTrue(outcome.is_err)
        self.assertIn("we read |A| = 16", outcome.unwrap_err().message)
        self.assertIn("different algebra file", outcome.unwrap_err().message)

    def test_an_algebra_absent_from_the_table_is_reported(self) -> None:
        outcome = cross_check(self._b28(), {})
        self.assertTrue(outcome.is_err)
        self.assertIn("absent from the UACalc table", outcome.unwrap_err().message)


class AgreementTests(unittest.TestCase):
    """The other direction: the checker must also be able to say yes.

    Without this the suite pins only failure.  Measured: with `agrees` forced
    to False in `compare`, every one of these suites still passed and only a
    real `make check-catalog` noticed.  A checker that called every algebra a
    mismatch would therefore have shipped green.
    """

    def test_the_fixture_is_the_algebras_it_claims_to_be(self) -> None:
        digest = hashlib.sha256(CORRECT_B1_B28.read_bytes()).hexdigest()
        self.assertEqual(digest, CORRECT_SHA256)

    def test_the_corrected_algebras_agree_with_the_article(self) -> None:
        comparisons = run(CORRECT_B1_B28, ARTICLE).unwrap()
        self.assertEqual([c.algebra for c in comparisons], ["B1", "B28"])
        for comparison in comparisons:
            self.assertTrue(
                comparison.agrees,
                f"{comparison.algebra} should represent L{comparison.lattice_index}",
            )

    def test_b1_is_the_five_element_pentagon(self) -> None:
        """The answer that looks alarming and is not: the catalog holds
        lattices of size AT MOST seven, and L1 is the pentagon."""
        b1 = run(CORRECT_B1_B28, ARTICLE).unwrap()[0]
        self.assertEqual(b1.cardinality, 4)
        self.assertEqual(b1.computed.size, 5)
        self.assertEqual(b1.drawn.size, 5)

    def test_the_corrected_b28_has_a_seven_element_congruence_lattice(self) -> None:
        """The same algebra the pre-fix fixture gets wrong with eight."""
        b28 = run(CORRECT_B1_B28, ARTICLE).unwrap()[1]
        self.assertEqual(b28.computed.size, 7)
        self.assertTrue(b28.agrees)

    def test_a_passing_run_reports_no_failures(self) -> None:
        comparisons = run(CORRECT_B1_B28, ARTICLE).unwrap()
        self.assertEqual([c for c in comparisons if not c.agrees], [])


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
