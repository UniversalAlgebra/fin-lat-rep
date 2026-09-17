"""
File: scripts/python/finlatrep/test_ua.py

Description: Tests for reading algebras out of a UACalc `.ua` file.
"""

from __future__ import annotations

import unittest

from _utils.pipeline_types import ErrorType
from finlatrep.ua import parse_algebras

WELL_FORMED = """<?xml version="1.0"?>
<algebraList>
<algebra><basicAlgebra>
  <algName>B2</algName>
  <cardinality>3</cardinality>
  <operations><op>
    <opSymbol><opName>h0</opName><arity>1</arity></opSymbol>
    <opTable><intArray><row>0, 1, 2</row></intArray></opTable>
  </op></operations>
</basicAlgebra></algebra>
</algebraList>
"""


def _with_table(row: str, cardinality: str = "3") -> str:
    return WELL_FORMED.replace("<row>0, 1, 2</row>", f"<row>{row}</row>").replace(
        "<cardinality>3</cardinality>", f"<cardinality>{cardinality}</cardinality>"
    )


class ParsingTests(unittest.TestCase):
    def test_reads_name_cardinality_and_table(self) -> None:
        algebras = parse_algebras(WELL_FORMED).unwrap()
        self.assertEqual(len(algebras), 1)
        self.assertEqual(algebras[0].name, "B2")
        self.assertEqual(algebras[0].cardinality, 3)
        self.assertEqual(algebras[0].unary_operations, ((0, 1, 2),))

    def test_malformed_xml_is_an_error_not_an_exception(self) -> None:
        outcome = parse_algebras("<algebraList><algebra>")
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.PARSING_ERROR)

    def test_a_short_table_is_rejected(self) -> None:
        """A truncated table would otherwise yield a plausible wrong lattice."""
        outcome = parse_algebras(_with_table("0, 1"))
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.VALIDATION_ERROR)
        self.assertIn("expected 3 values, found 2", outcome.unwrap_err().message)

    def test_a_value_outside_the_carrier_is_rejected(self) -> None:
        outcome = parse_algebras(_with_table("0, 1, 7"))
        self.assertTrue(outcome.is_err)
        self.assertIn("outside the carrier", outcome.unwrap_err().message)

    def test_a_binary_table_is_sized_by_arity(self) -> None:
        """Cardinality ** arity, so a 2-ary operation on 3 points needs 9 values."""
        binary = WELL_FORMED.replace("<arity>1</arity>", "<arity>2</arity>")
        self.assertTrue(parse_algebras(binary).is_err)

    def test_a_non_integer_table_entry_is_an_error_not_an_exception(self) -> None:
        """Malformed input must come back as a Result, not a ValueError."""
        outcome = parse_algebras(_with_table("0, x, 2"))
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.PARSING_ERROR)
        self.assertIn("is not an integer", outcome.unwrap_err().message)

    def test_a_negative_table_entry_parses_and_is_then_range_checked(self) -> None:
        """`-1` is an integer, so it fails on range rather than on syntax."""
        outcome = parse_algebras(_with_table("0, 1, -1"))
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.VALIDATION_ERROR)

    def test_a_file_with_no_algebras_is_rejected(self) -> None:
        """Otherwise the caller compares nothing and reports that all of it agreed."""
        outcome = parse_algebras("<algebraList></algebraList>")
        self.assertTrue(outcome.is_err)
        self.assertEqual(outcome.unwrap_err().error_type, ErrorType.VALIDATION_ERROR)
        self.assertIn("no <basicAlgebra>", outcome.unwrap_err().message)

    def test_a_file_with_the_wrong_root_is_rejected(self) -> None:
        self.assertTrue(parse_algebras("<notAlgebras><x/></notAlgebras>").is_err)

    def test_unary_operations_ignores_higher_arity(self) -> None:
        """Group files carry a binary multiplication the catalog check must skip."""
        binary = WELL_FORMED.replace("<arity>1</arity>", "<arity>2</arity>").replace(
            "<row>0, 1, 2</row>", "<row>0,1,2,1,2,0,2,0,1</row>"
        )
        algebras = parse_algebras(binary).unwrap()
        self.assertEqual(algebras[0].unary_operations, ())


if __name__ == "__main__":
    unittest.main()
