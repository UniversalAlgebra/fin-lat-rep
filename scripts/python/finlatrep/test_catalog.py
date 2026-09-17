r"""
File: scripts/python/finlatrep/test_catalog.py

Description: Tests for reading the article's drawn lattices out of its LaTeX.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from _utils.pipeline_types import ErrorType
from finlatrep.catalog import (
    CATALOG_HEADING,
    parse_catalog,
    read_catalog,
    strip_latex_comments,
)

ARTICLE = Path(__file__).resolve().parents[3] / "article" / "SmallLatticeReps.tex"

# Two entries in the shape the article uses: a pentagon and a 2-chain.
SYNTHETIC = CATALOG_HEADING + r"""
\begin{tabular}{ccc}
$\bL_1$&
\node(4) at (0,1)[e]{};
\node(3) at (0.33,0.33)[e]{};
\node(2) at (-0.5,0.0)[e]{};
\node(1) at (0.33,-0.33)[e]{};
\node(0) at (0,-1)[e]{};
\draw(3)--(4);
\draw(2)--(4);
\draw(1)--(3);
\draw(0)--(1);
\draw(0)--(2);
\end{tabular}
\begin{tabular}{ccc}
$\bL_2$&
\node(1) at (0,1)[e]{};
\node(0) at (0,-1)[e]{};
\draw(0)--(1);
\end{tabular}
"""


class ParsingTests(unittest.TestCase):
    def test_reads_each_drawn_lattice(self) -> None:
        catalog = parse_catalog(SYNTHETIC).unwrap()
        self.assertEqual(sorted(catalog), [1, 2])
        self.assertEqual(catalog[1].relation.size, 5)
        self.assertEqual(len(catalog[1].relation.covers), 5)
        self.assertEqual(catalog[2].relation.size, 2)

    def test_vertices_are_renumbered_from_zero_in_article_order(self) -> None:
        catalog = parse_catalog(SYNTHETIC).unwrap()
        self.assertEqual(
            catalog[1].relation.sorted_covers(),
            ((0, 1), (0, 2), (1, 3), (2, 4), (3, 4)),
        )

    def test_text_without_the_catalog_heading_is_an_error(self) -> None:
        outcome = parse_catalog("nothing to see here")
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.PARSING_ERROR)

    def test_a_catalog_naming_no_lattices_is_an_error(self) -> None:
        self.assertTrue(parse_catalog(CATALOG_HEADING + "\nempty\n").is_err)


class CommentTests(unittest.TestCase):
    """A commented-out diagram must not be read as if it were drawn."""

    def test_comments_are_stripped(self) -> None:
        self.assertEqual(strip_latex_comments("keep % drop\nkeep2"), "keep \nkeep2")

    def test_an_escaped_percent_is_not_a_comment(self) -> None:
        self.assertEqual(strip_latex_comments(r"100\% sure"), r"100\% sure")

    def test_a_commented_out_edge_is_not_counted(self) -> None:
        """The case that matters: an inline diagram commented out and replaced.

        Without stripping, the stale relation stays visible here and the check
        compares against a picture the article no longer draws.
        """
        live = parse_catalog(SYNTHETIC).unwrap()[2]
        commented = parse_catalog(
            SYNTHETIC.replace(r"\draw(0)--(1);", "%" + r"\draw(0)--(1);")
        ).unwrap()[2]
        self.assertEqual(len(live.relation.covers), 1)
        self.assertEqual(len(commented.relation.covers), 0)

    def test_a_commented_out_lattice_label_is_not_a_lattice(self) -> None:
        commented = parse_catalog(SYNTHETIC.replace(r"$\bL_2$", "%" + r"$\bL_2$")).unwrap()
        self.assertEqual(sorted(commented), [1])


class EdgeOrientationTests(unittest.TestCase):
    r"""TikZ `--` is undirected, so how an edge is written must not matter."""

    def test_reversing_how_an_edge_is_written_changes_nothing(self) -> None:
        forward = parse_catalog(SYNTHETIC).unwrap()
        reversed_ = parse_catalog(
            SYNTHETIC.replace(r"\draw(3)--(4);", r"\draw(4)--(3);")
        ).unwrap()
        self.assertEqual(forward[1].relation.covers, reversed_[1].relation.covers)

    def test_orientation_follows_height_not_vertex_number(self) -> None:
        """The article's vertex numbers do NOT run bottom to top.

        In L28 it places node 4 at y=0.0 and node 3 at y=0.2, so ordering an
        edge by its endpoint numbers would invert it.  Height is the only
        thing that says which element covers which.
        """
        upside_down = CATALOG_HEADING + "\n" + r"""
$\bL_9$&
\node(0) at (0,1)[e]{};
\node(1) at (0,-1)[e]{};
\draw(0)--(1);
"""
        entry = parse_catalog(upside_down).unwrap()[9]
        # node 1 is the LOWER one, so the cover runs from it to node 0.
        self.assertEqual(entry.relation.sorted_covers(), ((1, 0),))

    def test_an_edge_between_two_nodes_at_the_same_height_is_an_error(self) -> None:
        flat = CATALOG_HEADING + "\n" + r"""
$\bL_9$&
\node(0) at (-1,0)[e]{};
\node(1) at (1,0)[e]{};
\draw(0)--(1);
"""
        outcome = parse_catalog(flat)
        self.assertTrue(outcome.is_err)
        self.assertIn("same height", outcome.unwrap_err().message)

    def test_an_edge_naming_an_unplaced_node_is_an_error(self) -> None:
        dangling = CATALOG_HEADING + "\n" + r"""
$\bL_9$&
\node(0) at (0,0)[e]{};
\draw(0)--(7);
"""
        outcome = parse_catalog(dangling)
        self.assertTrue(outcome.is_err)
        self.assertIn("never placed", outcome.unwrap_err().message)


class ArticleTests(unittest.TestCase):
    r"""The shape the parser relies on, asserted against the real article.

    If a catalog diagram is ever moved into an `\input`, or rewritten with
    chained `\draw ... to ...` paths, these fail and say so, rather than the
    checker quietly comparing fewer lattices.
    """

    def test_the_article_is_where_it_is_expected(self) -> None:
        self.assertTrue(ARTICLE.is_file(), f"not found: {ARTICLE}")

    def test_the_catalog_draws_thirty_five_lattices(self) -> None:
        catalog = read_catalog(ARTICLE).unwrap()
        self.assertEqual(len(catalog), 35)

    def test_every_drawn_lattice_has_between_five_and_seven_elements(self) -> None:
        """The catalog is "lattices of size at most 7"; 2 have 5, 6 have 6, 27 have 7."""
        catalog = read_catalog(ARTICLE).unwrap()
        sizes = sorted(entry.relation.size for entry in catalog.values())
        self.assertEqual(sizes.count(5), 2)
        self.assertEqual(sizes.count(6), 6)
        self.assertEqual(sizes.count(7), 27)

    def test_the_vertex_numbering_is_not_bottom_to_top(self) -> None:
        """Guards the reason edges are oriented by height rather than number.

        If this ever starts failing, the article has been renumbered and the
        comment in catalog.py explaining why height is used needs revisiting.
        """
        text = ARTICLE.read_text("utf-8")
        body = text[text.index(CATALOG_HEADING):]
        chunk = body[body.index(r"$\bL_{28}$"):][:900]
        heights = {
            int(v): float(y)
            for v, _x, y in re.findall(
                r"\\node\((\d+)\)\s*at\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)", chunk
            )
        }
        self.assertLess(heights[4], heights[3])

    def test_the_catalog_subsection_uses_no_input(self) -> None:
        text = ARTICLE.read_text("utf-8")
        body = text[text.index(CATALOG_HEADING):]
        self.assertNotIn(r"\input{", body)


if __name__ == "__main__":
    unittest.main()
