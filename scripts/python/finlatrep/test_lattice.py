"""
File: scripts/python/finlatrep/test_lattice.py

Description: Tests for comparison of finite lattices by covering relation.
"""

from __future__ import annotations

import unittest

from finlatrep.lattice import CoveringRelation, are_isomorphic

# The five lattices on five elements, as covering pairs with 0 the bottom.
PENTAGON = CoveringRelation(5, frozenset({(0, 1), (0, 2), (1, 3), (2, 4), (3, 4)}))
CHAIN_THEN_FORK = CoveringRelation(5, frozenset({(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)}))
FORK_THEN_CHAIN = CoveringRelation(5, frozenset({(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)}))
DIAMOND_M3 = CoveringRelation(5, frozenset({(0, 1), (0, 2), (0, 3), (1, 4), (2, 4), (3, 4)}))
CHAIN_5 = CoveringRelation(5, frozenset({(0, 1), (1, 2), (2, 3), (3, 4)}))


class IsomorphismTests(unittest.TestCase):
    def test_a_lattice_is_isomorphic_to_a_relabelling_of_itself(self) -> None:
        relabelled = PENTAGON.relabelled((4, 3, 2, 1, 0))
        self.assertTrue(are_isomorphic(PENTAGON, relabelled))

    def test_counting_covers_cannot_distinguish_the_pentagon(self) -> None:
        """The near miss this comparison exists to avoid.

        N5 and `0 < a < {b,c} < 1` both have five elements and five covering
        pairs.  Anything comparing by counts would call the second one N5.
        """
        self.assertEqual(len(PENTAGON.covers), len(CHAIN_THEN_FORK.covers))
        self.assertEqual(PENTAGON.size, CHAIN_THEN_FORK.size)
        self.assertFalse(are_isomorphic(PENTAGON, CHAIN_THEN_FORK))

    def test_the_pentagon_is_not_its_own_dual_shaped_neighbour(self) -> None:
        self.assertFalse(are_isomorphic(PENTAGON, FORK_THEN_CHAIN))

    def test_the_pentagon_is_not_the_diamond(self) -> None:
        self.assertFalse(are_isomorphic(PENTAGON, DIAMOND_M3))

    def test_differing_sizes_are_never_isomorphic(self) -> None:
        smaller = CoveringRelation(4, frozenset({(0, 1), (0, 2), (1, 3), (2, 3)}))
        self.assertFalse(are_isomorphic(PENTAGON, smaller))

    def test_differing_edge_counts_are_never_isomorphic(self) -> None:
        self.assertFalse(are_isomorphic(PENTAGON, CHAIN_5))

    def test_sorted_covers_is_stable(self) -> None:
        self.assertEqual(
            PENTAGON.sorted_covers(), ((0, 1), (0, 2), (1, 3), (2, 4), (3, 4))
        )


if __name__ == "__main__":
    unittest.main()
