"""
File: scripts/python/_utils/test_run_tests.py

The runner's pure helpers: where a test lives, what it says it tests, and how
a docstring is cut to one sentence.  The runner itself is exercised by every
`make test`.

The fixture TestCases are defined inside the tests that use them, not at
module level: unittest discovers every TestCase subclass in a test module
whatever its name, and a module-level fixture would be run and counted as a
real test.
"""

import unittest

from _utils.run_tests import describe, first_sentence, relative_source


class DescribeTests(unittest.TestCase):
    def test_a_docstring_gives_its_first_sentence(self) -> None:
        class Documented(unittest.TestCase):
            def test_something(self) -> None:
                """The docstring's first sentence is the description.  Not this one.

                Nor this paragraph.
                """

        self.assertEqual(
            describe(Documented("test_something")),
            "The docstring's first sentence is the description.",
        )

    def test_no_docstring_gives_the_name_in_words(self) -> None:
        class Undocumented(unittest.TestCase):
            def test_a_short_table_is_rejected(self) -> None:
                pass

        self.assertEqual(
            describe(Undocumented("test_a_short_table_is_rejected")),
            "a short table is rejected",
        )


class FirstSentenceTests(unittest.TestCase):
    def test_a_wrapped_sentence_is_rejoined(self) -> None:
        """A sentence wrapped over two lines is one sentence, not its first line."""
        self.assertEqual(
            first_sentence(
                "`0` is a digit string and a table of length 0\n    has the right shape.  A second sentence."
            ),
            "`0` is a digit string and a table of length 0 has the right shape.",
        )

    def test_a_paragraph_without_a_period_is_taken_whole(self) -> None:
        self.assertEqual(first_sentence("no period here\n\nsecond paragraph"), "no period here")


class RelativeSourceTests(unittest.TestCase):
    def test_the_file_is_named_relative_to_scripts_python(self) -> None:
        self.assertEqual(relative_source(self), "_utils/test_run_tests.py")
