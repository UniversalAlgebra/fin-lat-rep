"""
File: scripts/python/finlatrep/test_congruence.py

Description: Tests for the congruence lattice of a finite unary algebra.
"""

from __future__ import annotations

import unittest

from finlatrep.congruence import congruences, covering_relation, principal_congruences
from finlatrep.lattice import are_isomorphic
from finlatrep.test_lattice import PENTAGON

# B1 of the article: four elements, two unary operations, Con(B1) is the
# pentagon and this is the smallest algebra representing N5.
B1_SIZE = 4
B1_OPS = ((1, 0, 3, 2), (1, 0, 1, 0))


class CongruenceTests(unittest.TestCase):
    def test_b1_has_the_pentagon_as_its_congruence_lattice(self) -> None:
        self.assertTrue(are_isomorphic(covering_relation(B1_SIZE, B1_OPS), PENTAGON))

    def test_b1_has_five_congruences(self) -> None:
        self.assertEqual(len(congruences(B1_SIZE, B1_OPS)), 5)

    def test_the_identity_congruence_is_always_present(self) -> None:
        """An algebra whose operations merge everything still has a bottom."""
        collapsing = ((0, 0, 0),)
        universe = congruences(3, collapsing)
        self.assertIn(tuple(range(3)), universe)

    def test_a_one_element_algebra_has_a_one_element_congruence_lattice(self) -> None:
        """There are no pairs to merge, so there are no principal congruences."""
        self.assertEqual(principal_congruences(1, ((0,),)), frozenset())
        self.assertEqual(covering_relation(1, ((0,),)).size, 1)

    def test_an_algebra_with_no_operations_has_every_equivalence_as_a_congruence(self) -> None:
        """On three points there are five partitions, and all are congruences."""
        self.assertEqual(len(congruences(3, ())), 5)

    def test_congruences_are_canonical_so_duplicates_collapse(self) -> None:
        universe = congruences(B1_SIZE, B1_OPS)
        self.assertEqual(len(universe), len(set(universe)))


if __name__ == "__main__":
    unittest.main()
