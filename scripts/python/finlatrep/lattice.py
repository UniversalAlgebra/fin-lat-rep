"""
File: scripts/python/finlatrep/lattice.py

Description: Finite lattices as their covering relations, and comparison of two.

  A lattice is carried here as the set of covering pairs `(lower, upper)` on
  vertices `0 .. n-1`.  That is all the catalog check compares, and it is what
  both sources give directly: the article draws edges, and a congruence lattice
  yields covers by inclusion.

Design note:

  Two lattices are compared by brute-force isomorphism of their covering
  digraphs.  Counting vertices and edges is NOT enough, and the near miss is
  worth naming: with three elements strictly between bottom and top, both the
  pentagon N5 and the modular lattice `0 < a < {b,c} < 1` have five covering
  pairs.  Anything that distinguished them by counting would call the second
  one N5.  At seven elements the search is 5040 permutations, which costs
  nothing, so there is no reason to be clever.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import FrozenSet, Tuple


@dataclass(frozen=True)
class CoveringRelation:
    """A finite poset given by its covering pairs on vertices 0 .. size - 1."""

    size: int
    covers: FrozenSet[Tuple[int, int]]

    def relabelled(self, mapping: Tuple[int, ...]) -> "CoveringRelation":
        """The same relation with vertex `i` renamed to `mapping[i]`."""
        return CoveringRelation(
            size=self.size,
            covers=frozenset((mapping[a], mapping[b]) for a, b in self.covers),
        )

    def sorted_covers(self) -> Tuple[Tuple[int, int], ...]:
        """The covering pairs in a stable order, for printing."""
        return tuple(sorted(self.covers))


def are_isomorphic(left: CoveringRelation, right: CoveringRelation) -> bool:
    """True if the two covering digraphs are isomorphic.

    Cheap necessary conditions first, so the permutation search is only
    reached by candidates that could actually match.
    """
    if left.size != right.size or len(left.covers) != len(right.covers):
        return False
    return any(
        left.relabelled(mapping).covers == right.covers
        for mapping in permutations(range(right.size))
    )
