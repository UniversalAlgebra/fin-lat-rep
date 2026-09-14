"""
File: scripts/python/finlatrep/congruence.py

Description: The congruence lattice of a finite unary algebra.

  Con(A) is computed in two steps.  The principal congruence Cg(a, b) is the
  least congruence identifying a and b, obtained by merging the pair and then
  closing under the operations until nothing more merges.  Every congruence of
  a finite algebra is a join of principal ones, so join-closing the principals
  gives the whole lattice.

  This is an independent implementation on purpose.  The article's algebras
  were produced with the Universal Algebra Calculator, and checking them with
  the same program would only show the file round-trips.  See
  docs/CHECKING-AN-ALGEBRA.md for how to run UACalc over the same file and
  compare, which is the second opinion.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Sequence, Set, Tuple

from finlatrep.lattice import CoveringRelation

# A congruence is carried as a tuple of block representatives: position i holds
# the least element of i's block.  Equality of tuples is then equality of
# partitions, which makes the join-closure a straightforward set computation.
Partition = Tuple[int, ...]


def _canonical(parent: List[int], size: int) -> Partition:
    """Collapse a union-find forest into a tuple of block representatives."""

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    return tuple(find(i) for i in range(size))


def _close(pairs: Sequence[Tuple[int, int]], size: int,
           operations: Sequence[Sequence[int]]) -> Partition:
    """The least congruence containing `pairs`."""
    parent = list(range(size))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> bool:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[max(ra, rb)] = min(ra, rb)
        return True

    for a, b in pairs:
        union(a, b)
    changed = True
    while changed:
        changed = False
        for table in operations:
            for x in range(size):
                for y in range(x + 1, size):
                    if find(x) == find(y) and union(table[x], table[y]):
                        changed = True
    return _canonical(parent, size)


def principal_congruences(size: int,
                          operations: Sequence[Sequence[int]]) -> FrozenSet[Partition]:
    """Cg(a, b) for every pair a < b."""
    return frozenset(
        _close([(a, b)], size, operations)
        for a in range(size)
        for b in range(a + 1, size)
    )


def _join(left: Partition, right: Partition, size: int,
          operations: Sequence[Sequence[int]]) -> Partition:
    """The least congruence above both arguments."""
    pairs = [(i, left[i]) for i in range(size)] + [(i, right[i]) for i in range(size)]
    return _close(pairs, size, operations)


def congruences(size: int, operations: Sequence[Sequence[int]]) -> Tuple[Partition, ...]:
    """Every congruence of the algebra, as canonical partitions.

    The identity congruence is included explicitly: an algebra with no pair to
    merge has no principal congruences at all, and the lattice is still a
    one-element lattice rather than an empty one.
    """
    identity: Partition = tuple(range(size))
    principals = principal_congruences(size, operations)
    universe: Set[Partition] = {identity} | set(principals)
    frontier: Set[Partition] = set(universe)
    while frontier:
        fresh = {
            joined
            for current in frontier
            for principal in principals
            if (joined := _join(current, principal, size, operations)) not in universe
        }
        universe |= fresh
        frontier = fresh
    return tuple(sorted(universe))


def _leq(finer: Partition, coarser: Partition) -> bool:
    """True if every block of `finer` lies inside a block of `coarser`."""
    return all(coarser[i] == coarser[finer[i]] for i in range(len(finer)))


def covering_relation(size: int,
                      operations: Sequence[Sequence[int]]) -> CoveringRelation:
    """Con(A) as a covering relation on 0 .. |Con(A)| - 1."""
    universe = congruences(size, operations)
    index: Dict[Partition, int] = {p: i for i, p in enumerate(universe)}
    covers = {
        (index[lower], index[upper])
        for lower in universe
        for upper in universe
        if lower != upper and _leq(lower, upper)
        and not any(
            middle not in (lower, upper) and _leq(lower, middle) and _leq(middle, upper)
            for middle in universe
        )
    }
    return CoveringRelation(size=len(universe), covers=frozenset(covers))
