r"""
File: scripts/python/finlatrep/test_catalog.py

Description: Tests for reading the article's drawn lattices out of its LaTeX.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _utils.pipeline_types import ErrorType
from finlatrep.catalog import CATALOG_HEADING, parse_catalog, read_catalog

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

    def test_the_catalog_subsection_uses_no_input(self) -> None:
        text = ARTICLE.read_text("utf-8")
        body = text[text.index(CATALOG_HEADING):]
        self.assertNotIn(r"\input{", body)


if __name__ == "__main__":
    unittest.main()
