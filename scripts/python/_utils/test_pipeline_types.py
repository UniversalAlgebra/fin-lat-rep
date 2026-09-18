"""
File: scripts/python/_utils/test_pipeline_types.py

Description: Tests for the Result type's eliminators.
"""

from __future__ import annotations

import unittest
from typing import Optional

from _utils.pipeline_types import ErrorType, PipelineError, Result, sequence_results

ERROR = PipelineError(ErrorType.VALIDATION_ERROR, "boom")


class UnwrapOrTests(unittest.TestCase):
    def test_returns_the_value_on_success(self) -> None:
        self.assertEqual(Result.ok(7).unwrap_or(0), 7)

    def test_returns_the_default_on_error(self) -> None:
        outcome: Result[int, PipelineError] = Result.err(ERROR)
        self.assertEqual(outcome.unwrap_or(0), 0)

    def test_a_successful_none_is_not_an_error(self) -> None:
        """Result.ok(None) is a success, so unwrap_or must not take the default.

        check_diagram_count returns exactly this when it has nothing to report,
        and conflating it with failure would silently invert the meaning.
        """
        outcome: Result[Optional[str], PipelineError] = Result.ok(None)
        self.assertIsNone(outcome.unwrap_or("fallback"))

    def test_a_successful_falsy_value_is_not_an_error(self) -> None:
        self.assertEqual(Result.ok(0).unwrap_or(99), 0)
        self.assertEqual(Result.ok("").unwrap_or("x"), "")


class ResultBasicsTests(unittest.TestCase):
    def test_map_preserves_an_error(self) -> None:
        outcome: Result[int, PipelineError] = Result.err(ERROR)
        self.assertTrue(outcome.map(lambda v: v).is_err)

    def test_and_then_chains_on_success(self) -> None:
        start: Result[int, PipelineError] = Result.ok(2)
        outcome: Result[int, PipelineError] = start.and_then(lambda v: Result.ok(v * 3))
        self.assertEqual(outcome.unwrap(), 6)

    def test_and_then_short_circuits_on_error(self) -> None:
        outcome: Result[int, PipelineError] = Result.err(ERROR)
        chained: Result[int, PipelineError] = outcome.and_then(Result.ok)
        self.assertTrue(chained.is_err)

    def test_sequence_returns_the_first_error(self) -> None:
        middle: Result[int, PipelineError] = Result.err(ERROR)
        outcome = sequence_results([Result.ok(1), middle, Result.ok(3)])
        self.assertTrue(outcome.is_err)

    def test_sequence_collects_every_value(self) -> None:
        self.assertEqual(sequence_results([Result.ok(1), Result.ok(2)]).unwrap(), [1, 2])


if __name__ == "__main__":
    unittest.main()
