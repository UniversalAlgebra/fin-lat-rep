r"""
File: scripts/python/finlatrep/test_latex.py

Description: Tests for stripping LaTeX comments, the parity rule included.
"""

from __future__ import annotations

import unittest

from finlatrep.latex import strip_latex_comments


class CommentTests(unittest.TestCase):
    def test_comments_are_stripped(self) -> None:
        self.assertEqual(strip_latex_comments("keep % drop\nkeep2"), "keep \nkeep2")

    def test_an_escaped_percent_is_not_a_comment(self) -> None:
        self.assertEqual(strip_latex_comments(r"100\% sure"), r"100\% sure")

    def test_a_percent_after_an_even_backslash_run_still_opens_a_comment(self) -> None:
        r"""TeX escaping is by backslash parity, not by the preceding character.

        In `\\%` the `\\` is its own control sequence, so the `%` still starts
        a comment.  Reading only the character before would keep that line, and
        a commented-out diagram would stay visible to the parser.
        """
        self.assertEqual(strip_latex_comments(r"a\\% dropped"), "a" + "\\" * 2)
        self.assertEqual(strip_latex_comments(r"a\\\% kept"), r"a\\\% kept")

    def test_line_count_is_preserved(self) -> None:
        """Stripping must not join lines: a later reader may count them."""
        self.assertEqual(strip_latex_comments("a%x\nb%y\nc").count("\n"), 2)


if __name__ == "__main__":
    unittest.main()
