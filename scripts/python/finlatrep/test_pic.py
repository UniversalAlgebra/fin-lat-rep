r"""
File: scripts/python/finlatrep/test_pic.py

Description: Tests for reading a Hasse diagram and its header out of a TikZ
  pic file in the shape article/inputs/tikz/README.md prescribes.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from _utils.pipeline_types import ErrorType
from finlatrep.latex import strip_latex_comments
from finlatrep.lattice import CoveringRelation, are_isomorphic
from finlatrep.pic import HEADER_KEYS, parse_header, parse_pic, read_pic

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures" / "tikz"
ARTICLE = HERE.parents[2] / "article" / "SmallLatticeReps.tex"
TIKZ = ARTICLE.parent / "inputs" / "tikz"
# The two files there that are not pics: the list of inputs, and the gallery.
NOT_PICS = {"all.tex", "gallery.tex"}

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

    def test_an_edge_written_with_to_is_rejected(self) -> None:
        r"""The case a lax reader gets wrong in the unsafe direction.

        TeX draws `\draw (0) to (4);`, so skipping it would leave an edge in
        the picture that is in neither the parsed drawing nor the header, and
        the cross-check would agree with itself about a lattice nobody sees.
        """
        body = GOOD_BODY + "\n" + r"  \draw (0) to (4);"
        outcome = parse_pic(pic(GOOD_HEADER, body))
        self.assertTrue(outcome.is_err)
        self.assertIn("not a form the checker reads", outcome.unwrap_err().message)
        self.assertIn(r"\draw (0) to (4);", outcome.unwrap_err().message)

    def test_an_edge_with_options_is_rejected(self) -> None:
        body = GOOD_BODY.replace(r"  \draw (0) -- (1);", r"  \draw[semithick] (0) -- (1);")
        outcome = parse_pic(pic(GOOD_HEADER, body))
        self.assertTrue(outcome.is_err)
        self.assertIn("not a form the checker reads", outcome.unwrap_err().message)

    def test_a_chained_edge_is_rejected(self) -> None:
        r"""`\draw (0) -- (1) -- (3);` draws two edges and is read as none."""
        body = GOOD_BODY.replace(r"  \draw (0) -- (1);", r"  \draw (0) -- (1) -- (3);")
        self.assertTrue(parse_pic(pic(GOOD_HEADER, body)).is_err)

    def test_two_edges_on_one_line_are_rejected(self) -> None:
        body = GOOD_BODY.replace(
            r"  \draw (0) -- (1);", r"  \draw (0) -- (1); \draw (0) -- (4);"
        )
        self.assertTrue(parse_pic(pic(GOOD_HEADER, body)).is_err)

    def test_a_stray_label_is_rejected(self) -> None:
        """Labels belong at the call site, and the reader now says so."""
        body = GOOD_BODY + "\n" + r"  \draw (4) node[above] {$1$};"
        self.assertTrue(parse_pic(pic(GOOD_HEADER, body)).is_err)

    def test_a_schematic_file_may_draw_what_it_likes(self) -> None:
        """No `covers:` means nothing to cross-check, so the body is free.

        The potato diagrams of Figures 2 and 4 are curves and ellipses; there
        is no covering relation to disagree with.
        """
        body = "\n".join([
            r"  \node[lat] (bot) at (0,0) {};",
            r"  \node[lat] (top) at (0,4) {};",
            r"  \draw (bot) to [out=50,in=-50] (top);",
            r"  \draw (0,2) node {$\vdots$};",
        ])
        result = parse_pic(pic("% id: L1\n% tags: schematic", body)).unwrap()
        self.assertIsNone(result.declared)
        self.assertEqual(result.drawn.size, 2)

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

    def test_a_non_numeric_y_coordinate_is_an_error(self) -> None:
        outcome = parse_pic(pic(GOOD_HEADER, GOOD_BODY.replace("(0) at (0,0)", "(0) at (0,.)")))
        self.assertTrue(outcome.is_err)
        self.assertIn("y='.'", outcome.unwrap_err().message)
        self.assertIn("not a number", outcome.unwrap_err().message)

    def test_a_non_numeric_x_coordinate_is_an_error(self) -> None:
        """The x never reaches the covering relation, but the file is still
        malformed and TeX will not draw it."""
        outcome = parse_pic(pic(GOOD_HEADER, GOOD_BODY.replace("(0) at (0,0)", "(0) at (.,0)")))
        self.assertTrue(outcome.is_err)
        self.assertIn("x='.'", outcome.unwrap_err().message)

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


class TikzDirectoryTests(unittest.TestCase):
    """The real files under article/inputs/tikz/, held to the convention.

    These are what make a new lattice that is not listed fail `make test`
    rather than compile to nothing.
    """

    def pics(self) -> list[Path]:
        return sorted(p for p in TIKZ.glob("*.tex") if p.name not in NOT_PICS)

    def test_the_directory_is_where_it_is_expected(self) -> None:
        self.assertTrue((TIKZ / "all.tex").is_file(), f"not found: {TIKZ / 'all.tex'}")

    def test_every_file_is_a_pic_named_after_itself(self) -> None:
        for path in self.pics():
            with self.subTest(file=path.name):
                outcome = read_pic(path)
                self.assertTrue(outcome.is_ok, str(outcome.unwrap_err()) if outcome.is_err else "")
                self.assertEqual(outcome.unwrap().header.get("id"), path.stem)

    def test_every_lattice_file_draws_the_covers_its_header_declares(self) -> None:
        for path in self.pics():
            pic = read_pic(path).unwrap()
            if pic.declared is not None:
                with self.subTest(file=path.name):
                    self.assertEqual(pic.named(pic.drawn), pic.named(pic.declared))

    def test_every_lattice_file_carries_the_full_header(self) -> None:
        """A file that declares covers is a lattice file, and carries every key."""
        for path in self.pics():
            pic = read_pic(path).unwrap()
            if pic.declared is not None:
                with self.subTest(file=path.name):
                    self.assertEqual(sorted(pic.header), sorted(HEADER_KEYS))

    def test_every_lattice_file_puts_its_bottom_element_at_the_origin(self) -> None:
        """The coordinate convention, so that one scale gives one height."""
        for path in self.pics():
            pic_read = read_pic(path).unwrap()
            if pic_read.declared is None:
                continue
            placed = {
                name: (float(x), float(y))
                for name, x, y in re.findall(
                    r"\\node\[lat\]\s*\(([\w-]+)\)\s*at\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)",
                    path.read_text("utf-8"),
                )
            }
            lowest = min(placed, key=lambda name: (placed[name][1], placed[name][0]))
            with self.subTest(file=path.name):
                self.assertEqual(placed[lowest], (0.0, 0.0))

    def test_a_file_without_covers_says_it_is_schematic(self) -> None:
        for path in self.pics():
            pic = read_pic(path).unwrap()
            if pic.declared is None:
                with self.subTest(file=path.name):
                    self.assertIn("schematic", pic.header.get("tags", ""))

    def test_all_tex_inputs_every_file_once_and_nothing_else(self) -> None:
        listed = re.findall(r"^\\input\{inputs/tikz/([\w-]+)\.tex\}$", (TIKZ / "all.tex").read_text("utf-8"), re.M)
        self.assertEqual(len(listed), len(set(listed)), "a file is input twice")
        self.assertEqual(sorted(listed), sorted(p.stem for p in self.pics()))

    def test_the_gallery_shows_every_pic(self) -> None:
        gallery = strip_latex_comments((TIKZ / "gallery.tex").read_text("utf-8"))
        shown = re.findall(r"^\\entry(?:\[[^\]]*\])?\{([\w-]+)\}$", gallery, re.M)
        self.assertEqual(sorted(shown), sorted(p.stem for p in self.pics()))

    def test_every_catalog_lattice_has_its_file(self) -> None:
        missing = [f"L{i}" for i in range(1, 36) if not (TIKZ / f"L{i}.tex").is_file()]
        self.assertEqual(missing, [])

    def test_the_article_inputs_the_list_once_from_its_preamble(self) -> None:
        text = ARTICLE.read_text("utf-8")
        self.assertEqual(text.count(r"\input{inputs/tikz/all.tex}"), 1)
        self.assertLess(text.index(r"\input{inputs/tikz/all.tex}"), text.index(r"\begin{document}"))

    def test_the_article_inputs_no_pic_file_directly(self) -> None:
        r"""A pic is defined once, from all.tex; a second \input would redefine it."""
        text = ARTICLE.read_text("utf-8")
        inputs = re.findall(r"\\input\{inputs/tikz/([\w-]+)\.tex\}", text)
        self.assertEqual(inputs, ["all"])


if __name__ == "__main__":
    unittest.main()
