"""
File: scripts/python/_utils/test_run_tests.py

The runner's two pure helpers: where a test lives, and what it says it tests.
The runner itself is exercised by every `make test`.
"""

import unittest

from _utils.run_tests import describe, first_sentence, relative_source


class _Documented(unittest.TestCase):
    def test_something(self) -> None:
        """The docstring's first line is the description.

        This second paragraph is not.
        """


class _Undocumented(unittest.TestCase):
    def test_a_short_table_is_rejected(self) -> None:
        pass


class DescribeTests(unittest.TestCase):
    def test_a_docstring_gives_its_first_line(self) -> None:
        self.assertEqual(
            describe(_Documented("test_something")),
            "The docstring's first line is the description.",
        )

    def test_no_docstring_gives_the_name_in_words(self) -> None:
        self.assertEqual(
            describe(_Undocumented("test_a_short_table_is_rejected")),
            "a short table is rejected",
        )


class FirstSentenceTests(unittest.TestCase):
    def test_a_wrapped_sentence_is_rejoined(self) -> None:
        """A sentence wrapped over two lines is one sentence, not its first line."""
        self.assertEqual(
            first_sentence("`0` is a digit string and a table of length 0\n    has the right shape.  A second sentence."),
            "`0` is a digit string and a table of length 0 has the right shape.",
        )

    def test_a_paragraph_without_a_period_is_taken_whole(self) -> None:
        self.assertEqual(first_sentence("no period here\n\nsecond paragraph"), "no period here")


class RelativeSourceTests(unittest.TestCase):
    def test_the_file_is_named_relative_to_scripts_python(self) -> None:
        self.assertEqual(
            relative_source(self), "_utils/test_run_tests.py"
        )
