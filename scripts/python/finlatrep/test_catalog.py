r"""
File: scripts/python/finlatrep/test_catalog.py

Description: Tests for reading the article's catalog: which lattice each label
  is drawn with, and where the drawing comes from.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _utils.pipeline_types import ErrorType
from finlatrep.catalog import CATALOG_HEADING, parse_catalog, read_catalog
from finlatrep.lattice import CoveringRelation

HERE = Path(__file__).resolve().parent
ARTICLE = HERE.parents[2] / "article" / "SmallLatticeReps.tex"
FIXTURES = HERE.parent / "fixtures" / "tikz"

PENTAGON = CoveringRelation(5, frozenset({(0, 1), (0, 2), (1, 3), (2, 4), (3, 4)}))

# Two entries in the shape the catalog uses: each label followed by the call
# that draws it, whose file is found under FIXTURES.
SYNTHETIC = CATALOG_HEADING + r"""
\begin{tabular}{ccc}
$\bL_1$& \hasse{L1} & $B_1$
\end{tabular}
\begin{tabular}{ccc}
$\bL_6$& \hasse{L6} & $B_6$
\end{tabular}
"""

# Transitional: an entry still drawn inline, with no header.
INLINE = CATALOG_HEADING + r"""
$\bL_2$&
\node(1) at (0,1)[e]{};
\node(0) at (0,-1)[e]{};
\draw(0)--(1);
"""


class FileEntryTests(unittest.TestCase):
    def test_each_label_is_read_from_the_file_its_call_names(self) -> None:
        catalog = parse_catalog(SYNTHETIC, FIXTURES).unwrap()
        self.assertEqual(sorted(catalog), [1, 6])
        self.assertEqual(catalog[1].drawn, PENTAGON)
        self.assertEqual(catalog[1].declared, PENTAGON)
        self.assertEqual(catalog[1].source, "inputs/tikz/L1.tex")
        self.assertEqual(catalog[6].drawn.size, 6)

    def test_a_scaled_call_is_the_same_call(self) -> None:
        catalog = parse_catalog(SYNTHETIC.replace(r"\hasse{L1}", r"\hasse[0.8]{L1}"), FIXTURES).unwrap()
        self.assertEqual(catalog[1].drawn, PENTAGON)

    def test_a_call_drawing_the_wrong_file_beside_a_label_is_an_error(self) -> None:
        """The catalog's L_i must be drawn by L<i>.tex, or the number and the
        picture come apart."""
        outcome = parse_catalog(SYNTHETIC.replace(r"\hasse{L6}", r"\hasse{L1}"), FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertIn("L6.tex", outcome.unwrap_err().message)

    def test_a_call_to_a_missing_file_is_an_error(self) -> None:
        text = SYNTHETIC.replace(r"$\bL_6$", r"$\bL_7$").replace(r"\hasse{L6}", r"\hasse{L7}")
        outcome = parse_catalog(text, FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.FILE_NOT_FOUND)

    def test_a_file_whose_header_disagrees_with_its_drawing_is_read_not_rejected(self) -> None:
        """The disagreement is check.py's to report, with both relations."""
        text = SYNTHETIC.replace(r"$\bL_6$", r"$\bL_9$").replace(r"\hasse{L6}", r"\hasse{L9}")
        catalog = parse_catalog(text, FIXTURES).unwrap()
        assert catalog[9].declared is not None
        self.assertNotEqual(catalog[9].drawn.covers, catalog[9].declared.covers)

    def test_two_calls_beside_one_label_are_an_error(self) -> None:
        text = SYNTHETIC.replace(r"\hasse{L1}", r"\hasse{L1} \hasse{L1}")
        outcome = parse_catalog(text, FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertIn("more than one", outcome.unwrap_err().message)

    def test_a_commented_out_call_is_not_a_call(self) -> None:
        text = SYNTHETIC.replace(r"\hasse{L6}", "%" + r"\hasse{L6}")
        outcome = parse_catalog(text, FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertIn("L6", outcome.unwrap_err().message)


class InlineEntryTests(unittest.TestCase):
    """Transitional: the older inline form, until the last diagram has moved."""

    def test_an_inline_entry_has_no_declared_relation(self) -> None:
        entry = parse_catalog(INLINE, FIXTURES).unwrap()[2]
        self.assertEqual(entry.source, "inline")
        self.assertIsNone(entry.declared)
        self.assertEqual(entry.drawn.sorted_covers(), ((0, 1),))

    def test_orientation_follows_height_not_vertex_number(self) -> None:
        """In L28 the article placed node 4 at y=0.0 and node 3 at y=0.2."""
        upside_down = INLINE.replace("(1) at (0,1)", "(1) at (0,-2)")
        entry = parse_catalog(upside_down, FIXTURES).unwrap()[2]
        self.assertEqual(entry.drawn.sorted_covers(), ((1, 0),))

    def test_a_commented_out_edge_is_not_counted(self) -> None:
        commented = parse_catalog(INLINE.replace(r"\draw(0)--(1);", "%" + r"\draw(0)--(1);"), FIXTURES)
        self.assertEqual(len(commented.unwrap()[2].drawn.covers), 0)

    def test_an_edge_between_two_nodes_at_the_same_height_is_an_error(self) -> None:
        outcome = parse_catalog(INLINE.replace("(1) at (0,1)", "(1) at (1,-1)"), FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertIn("same height", outcome.unwrap_err().message)

    def test_an_edge_naming_an_unplaced_node_is_an_error(self) -> None:
        outcome = parse_catalog(INLINE.replace(r"\draw(0)--(1);", r"\draw(0)--(7);"), FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertIn("never placed", outcome.unwrap_err().message)


class StructureTests(unittest.TestCase):
    def test_text_without_the_catalog_heading_is_an_error(self) -> None:
        outcome = parse_catalog("nothing to see here", FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.PARSING_ERROR)

    def test_a_lattice_labelled_twice_is_an_error(self) -> None:
        """Keeping the first drawing would leave the entry count intact at 35
        while a second, different drawing of the same lattice went uncompared."""
        outcome = parse_catalog(SYNTHETIC + SYNTHETIC[SYNTHETIC.index(r"$\bL_6$"):], FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertIn("labelled more than once", outcome.unwrap_err().message)

    def test_a_label_with_neither_call_nor_drawing_is_an_error(self) -> None:
        outcome = parse_catalog(CATALOG_HEADING + "\n$\\bL_3$& nothing\n", FIXTURES)
        self.assertTrue(outcome.is_err)
        self.assertIn("L3", outcome.unwrap_err().message)

    def test_a_catalog_naming_no_lattices_is_an_error(self) -> None:
        self.assertTrue(parse_catalog(CATALOG_HEADING + "\nempty\n", FIXTURES).is_err)

    def test_a_commented_out_lattice_label_is_not_a_lattice(self) -> None:
        commented = parse_catalog(SYNTHETIC.replace(r"$\bL_6$", "%" + r"$\bL_6$"), FIXTURES).unwrap()
        self.assertEqual(sorted(commented), [1])


class ArticleTests(unittest.TestCase):
    """The shape the reader relies on, asserted against the real article."""

    def test_the_article_is_where_it_is_expected(self) -> None:
        self.assertTrue(ARTICLE.is_file(), f"not found: {ARTICLE}")

    def test_the_catalog_draws_thirty_five_lattices(self) -> None:
        catalog = read_catalog(ARTICLE).unwrap()
        self.assertEqual(len(catalog), 35)

    def test_every_drawn_lattice_has_between_five_and_seven_elements(self) -> None:
        """The catalog is "lattices of size at most 7"; 2 have 5, 6 have 6, 27 have 7."""
        catalog = read_catalog(ARTICLE).unwrap()
        sizes = sorted(entry.drawn.size for entry in catalog.values())
        self.assertEqual(sizes.count(5), 2)
        self.assertEqual(sizes.count(6), 6)
        self.assertEqual(sizes.count(7), 27)


if __name__ == "__main__":
    unittest.main()
