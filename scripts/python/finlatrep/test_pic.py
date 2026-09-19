r"""
File: scripts/python/finlatrep/test_pic.py

Description: Tests for reading a Hasse diagram and its header out of a TikZ
  pic file in the shape article/inputs/tikz/README.md prescribes.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _utils.pipeline_types import ErrorType
from finlatrep.lattice import CoveringRelation, are_isomorphic
from finlatrep.pic import parse_header, parse_pic, read_pic

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "tikz"

PENTAGON = CoveringRelation(5, frozenset({(0, 1), (0, 2), (1, 3), (2, 4), (3, 4)}))


def pic(header: str, body: str, name: str = "L1") -> str:
    return f"{header}\n\\tikzset{{{name}/.pic={{\n{body}\n}}}}\n"


GOOD_HEADER = "\n".join([
    "% id: L1",
    "% aliases: pentagon, N5",
    "% elements: 5",
    "% covers: 0<1 0<2 1<3 2<4 3<4",
    "% represented-by: B1 (SmallLatticeReps.ua)",
    "% tags: nonmodular, self-dual",
])
GOOD_BODY = "\n".join([
    r"  \node[lat] (0) at (0,0) {};",
    r"  \node[lat] (1) at (0.5,1) {};",
    r"  \node[lat] (2) at (-0.75,1.5) {};",
    r"  \node[lat] (3) at (0.5,2) {};",
    r"  \node[lat] (4) at (0,3) {};",
    r"  \draw (0) -- (1);",
    r"  \draw (0) -- (2);",
    r"  \draw (1) -- (3);",
    r"  \draw (4) -- (2);",
    r"  \draw (3) -- (4);",
])


class FixtureTests(unittest.TestCase):
    """The three fixtures the design asked for, read from disk."""

    def test_a_file_in_the_prescribed_shape_is_read(self) -> None:
        result = read_pic(FIXTURES / "L1.tex").unwrap()
        self.assertEqual(result.name, "L1")
        self.assertEqual(result.vertices, ("0", "1", "2", "3", "4"))
        self.assertEqual(result.drawn, PENTAGON)
        self.assertEqual(result.declared, PENTAGON)
        self.assertEqual(result.header["represented-by"], "B1 (SmallLatticeReps.ua)")

    def test_a_file_whose_header_and_drawing_disagree_reads_both(self) -> None:
        """Disagreement is not a parse error; it is what check.py reports."""
        result = read_pic(FIXTURES / "L9.tex").unwrap()
        assert result.declared is not None
        self.assertEqual(result.drawn, PENTAGON)
        self.assertNotEqual(result.drawn.covers, result.declared.covers)
        self.assertFalse(are_isomorphic(result.drawn, result.declared))

    def test_vertices_named_by_words_are_read(self) -> None:
        result = read_pic(FIXTURES / "L6.tex").unwrap()
        self.assertEqual(result.vertices[0], "bottom")
        self.assertEqual(result.drawn.size, 6)
        self.assertEqual(result.drawn, result.declared)
        self.assertIn("bottom<left-low", result.named(result.drawn))

    def test_a_missing_file_is_an_error_not_an_exception(self) -> None:
        outcome = read_pic(FIXTURES / "L99.tex")
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.FILE_NOT_FOUND)


class HeaderTests(unittest.TestCase):
    def test_reads_every_key(self) -> None:
        header = parse_header(GOOD_HEADER).unwrap()
        self.assertEqual(sorted(header), ["aliases", "covers", "elements", "id", "represented-by", "tags"])
        self.assertEqual(header["covers"], "0<1 0<2 1<3 2<4 3<4")

    def test_an_empty_value_is_allowed(self) -> None:
        self.assertEqual(parse_header("% aliases:\n% id: L1").unwrap()["aliases"], "")

    def test_a_free_text_comment_line_is_skipped(self) -> None:
        header = parse_header("%% file: L1.tex\n% see the catalog\n% id: L1").unwrap()
        self.assertEqual(header, {"id": "L1"})

    def test_an_unknown_key_is_an_error(self) -> None:
        """A misspelt `cover:` must not silently drop the covers check."""
        outcome = parse_header("% id: L1\n% cover: 0<1")
        self.assertTrue(outcome.is_err)
        self.assertIn("cover", outcome.unwrap_err().message)

    def test_a_repeated_key_is_an_error(self) -> None:
        self.assertTrue(parse_header("% id: L1\n% id: L2").is_err)

    def test_the_header_ends_at_the_first_non_comment_line(self) -> None:
        header = parse_header("% id: L1\n\\tikzset{}\n% tags: late").unwrap()
        self.assertNotIn("tags", header)


class BodyTests(unittest.TestCase):
    def test_reads_the_drawing_and_the_declaration(self) -> None:
        result = parse_pic(pic(GOOD_HEADER, GOOD_BODY)).unwrap()
        self.assertEqual(result.drawn, PENTAGON)
        self.assertEqual(result.declared, PENTAGON)

    def test_edges_are_oriented_by_height_not_by_how_they_are_written(self) -> None:
        r"""`\draw (4) -- (2);` above draws the cover 2<4, whichever way it is written."""
        reversed_ = parse_pic(pic(GOOD_HEADER, GOOD_BODY.replace(r"(4) -- (2)", r"(2) -- (4)"))).unwrap()
        self.assertEqual(reversed_.drawn, PENTAGON)

    def test_a_commented_out_edge_is_not_drawn(self) -> None:
        body = GOOD_BODY.replace(r"  \draw (3) -- (4);", r"  %\draw (3) -- (4);")
        result = parse_pic(pic(GOOD_HEADER, body)).unwrap()
        self.assertEqual(len(result.drawn.covers), 4)
        assert result.declared is not None
        self.assertNotEqual(result.drawn.covers, result.declared.covers)

    def test_a_chained_edge_is_not_read_and_the_header_catches_it(self) -> None:
        r"""The reader knows only `\draw (a) -- (b);`.

        A chain such as `\draw (0) -- (1) -- (3);` is quietly not an edge, which
        is safe precisely because the header then disagrees with the drawing.
        """
        body = GOOD_BODY.replace(r"  \draw (0) -- (1);" + "\n" + r"  \draw (0) -- (2);",
                                 r"  \draw (0) -- (1) -- (3);")
        result = parse_pic(pic(GOOD_HEADER, body)).unwrap()
        assert result.declared is not None
        self.assertLess(len(result.drawn.covers), len(result.declared.covers))

    def test_a_pic_named_differently_from_its_id_is_an_error(self) -> None:
        outcome = parse_pic(pic(GOOD_HEADER, GOOD_BODY, name="L2"))
        self.assertTrue(outcome.is_err)
        self.assertIn("id: L1", outcome.unwrap_err().message)

    def test_a_file_without_an_id_is_an_error(self) -> None:
        self.assertTrue(parse_pic(pic("% elements: 5", GOOD_BODY)).is_err)

    def test_a_file_with_no_pic_is_an_error(self) -> None:
        self.assertTrue(parse_pic(GOOD_HEADER + "\n" + GOOD_BODY).is_err)

    def test_a_file_with_two_pics_is_an_error(self) -> None:
        text = pic(GOOD_HEADER, GOOD_BODY) + pic("", GOOD_BODY, name="L2")
        self.assertTrue(parse_pic(text).is_err)

    def test_a_wrong_element_count_is_an_error(self) -> None:
        outcome = parse_pic(pic(GOOD_HEADER.replace("elements: 5", "elements: 6"), GOOD_BODY))
        self.assertTrue(outcome.is_err)
        self.assertIn("elements: 6", outcome.unwrap_err().message)

    def test_a_cover_naming_an_unplaced_vertex_is_an_error(self) -> None:
        outcome = parse_pic(pic(GOOD_HEADER.replace("3<4", "3<9"), GOOD_BODY))
        self.assertTrue(outcome.is_err)
        self.assertIn("9", outcome.unwrap_err().message)

    def test_a_malformed_cover_token_is_an_error(self) -> None:
        outcome = parse_pic(pic(GOOD_HEADER.replace("3<4", "3-4"), GOOD_BODY))
        self.assertTrue(outcome.is_err)
        self.assertIn("lower<upper", outcome.unwrap_err().message)

    def test_an_edge_to_an_unplaced_vertex_is_an_error(self) -> None:
        outcome = parse_pic(pic(GOOD_HEADER, GOOD_BODY + "\n" + r"  \draw (0) -- (7);"))
        self.assertTrue(outcome.is_err)
        self.assertIn("never placed", outcome.unwrap_err().message)

    def test_an_edge_between_vertices_at_the_same_height_is_an_error(self) -> None:
        body = GOOD_BODY.replace("(3) at (0.5,2)", "(3) at (0.5,1.5)")
        outcome = parse_pic(pic(GOOD_HEADER, body + "\n" + r"  \draw (2) -- (3);"))
        self.assertTrue(outcome.is_err)
        self.assertIn("same height", outcome.unwrap_err().message)

    def test_a_vertex_placed_twice_is_an_error(self) -> None:
        outcome = parse_pic(pic(GOOD_HEADER, GOOD_BODY + "\n" + r"  \node[lat] (0) at (0,9) {};"))
        self.assertTrue(outcome.is_err)
        self.assertIn("twice", outcome.unwrap_err().message)

    def test_a_non_numeric_coordinate_is_an_error(self) -> None:
        outcome = parse_pic(pic(GOOD_HEADER, GOOD_BODY.replace("(0) at (0,0)", "(0) at (0,.)")))
        self.assertTrue(outcome.is_err)
        self.assertIn("not a number", outcome.unwrap_err().message)

    def test_a_file_without_a_covers_line_has_no_declared_relation(self) -> None:
        header = "% id: L1\n% tags: schematic"
        result = parse_pic(pic(header, GOOD_BODY)).unwrap()
        self.assertIsNone(result.declared)
        self.assertEqual(result.drawn, PENTAGON)

    def test_vertex_names_sort_numbers_by_value_before_words(self) -> None:
        body = "\n".join([
            r"\node[lat] (2) at (0,0) {};",
            r"\node[lat] (10) at (0,1) {};",
            r"\node[lat] (top) at (0,2) {};",
            r"\draw (2) -- (10);",
            r"\draw (10) -- (top);",
        ])
        result = parse_pic(pic("% id: L1", body)).unwrap()
        self.assertEqual(result.vertices, ("2", "10", "top"))


if __name__ == "__main__":
    unittest.main()
