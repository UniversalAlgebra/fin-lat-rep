"""
File: scripts/python/finlatrep/check.py

Description: Check every algebra in a `.ua` file against the lattice the
  article draws beside it.

  For each algebra named `B`*i* in the algebra file, compute Con(B_i) and
  compare it with the lattice `L`*i* drawn in the catalog subsection of
  `article/SmallLatticeReps.tex`.  Disagreement is reported with both covering
  relations and makes the run exit non-zero.

  Why this exists: B28 was wrong from 2017 until 2026, six operations instead
  of seven and an 8-element congruence lattice rather than L28's 7, and nobody
  noticed because checking meant doing it by hand.  See
  docs/CHECKING-AN-ALGEBRA.md to check a single entry yourself.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from _utils.file_ops import read_text
from _utils.pipeline_types import ErrorType, PipelineError, Result
from finlatrep.catalog import CatalogEntry, read_catalog
from finlatrep.congruence import covering_relation
from finlatrep.lattice import CoveringRelation, are_isomorphic
from finlatrep.ua import Algebra, read_algebras

# `B12`, and also `B4-prime`, a second representation of L4 by an intransitive
# group action, which is checked against L4 like any other.
_ALGEBRA_NAME = re.compile(r"^B(\d+)(?:-(\w+))?$")


# Every line this script prints about a check starts with a mark and this
# name, so that in `make verify` a reader can see what was tested and by whom.
ME = "finlatrep/check.py"
PASS = "✅"
FAIL = "❌"

@dataclass(frozen=True)
class Comparison:
    """The outcome of checking one algebra against one drawn lattice."""

    algebra: str
    lattice_index: int
    cardinality: int
    computed: CoveringRelation
    drawn: CoveringRelation
    agrees: bool

    def describe(self) -> str:
        """One line per algebra: the mark, this script, and what was compared."""
        return (
            f"{PASS if self.agrees else FAIL} {ME}  "
            f"{self.algebra:<10} |A| = {self.cardinality:>2}   "
            f"|Con(A)| = {self.computed.size}   "
            f"L{self.lattice_index} has {self.drawn.size}"
        )

    def describe_failure(self) -> str:
        """The detail a reader needs when the two disagree."""
        return "\n".join(
            [
                f"  {self.algebra} does not represent L{self.lattice_index}:",
                f"    Con({self.algebra}) has {self.computed.size} elements, "
                f"covers {list(self.computed.sorted_covers())}",
                f"    L{self.lattice_index} has {self.drawn.size} elements, "
                f"covers {list(self.drawn.sorted_covers())}",
            ]
        )


def lattice_index_of(algebra_name: str) -> Optional[int]:
    """The lattice an algebra is named for, or None if the name is not `B`*i*."""
    match = _ALGEBRA_NAME.match(algebra_name)
    return int(match.group(1)) if match else None


def compare(algebra: Algebra, entry: CatalogEntry) -> Comparison:
    """Check one algebra against the lattice drawn for it."""
    computed = covering_relation(algebra.cardinality, algebra.unary_operations)
    return Comparison(
        algebra=algebra.name,
        lattice_index=entry.index,
        cardinality=algebra.cardinality,
        computed=computed,
        drawn=entry.relation,
        agrees=are_isomorphic(computed, entry.relation),
    )


def compare_all(
    algebras: Sequence[Algebra], catalog: Dict[int, CatalogEntry]
) -> Result[Tuple[Comparison, ...], PipelineError]:
    """Check every algebra whose name identifies a lattice in the catalog."""
    comparisons: List[Comparison] = []
    for algebra in algebras:
        index = lattice_index_of(algebra.name)
        if index is None:
            return Result.err(
                PipelineError(
                    ErrorType.VALIDATION_ERROR,
                    f"algebra {algebra.name!r} is not named for a lattice; expected B<i>",
                )
            )
        entry = catalog.get(index)
        if entry is None:
            return Result.err(
                PipelineError(
                    ErrorType.VALIDATION_ERROR,
                    f"the article draws no lattice L{index} for algebra {algebra.name}",
                )
            )
        comparisons.append(compare(algebra, entry))
    return Result.ok(tuple(comparisons))


def check_diagram_count(
    catalog: Dict[int, CatalogEntry], algebras: Sequence[Algebra]
) -> Result[None, PipelineError]:
    """Refuse to run if the article draws fewer lattices than there are algebras.

    The catalog's diagrams are inline TikZ today.  Should one ever be moved
    into an `\\input`, the parser would simply not see it, and a check that
    quietly skipped an algebra would be worse than no check at all.  Fewer
    diagrams than algebras is that situation, so stop loudly.
    """
    missing = sorted(
        {
            index
            for algebra in algebras
            if (index := lattice_index_of(algebra.name)) is not None
            and index not in catalog
        }
    )
    if missing:
        return Result.err(
            PipelineError(
                ErrorType.VALIDATION_ERROR,
                "the article draws no diagram for "
                + ", ".join(f"L{i}" for i in missing)
                + "; if a diagram moved into an \\input, catalog.py must learn to follow it",
            )
        )
    return Result.ok(None)


@dataclass(frozen=True)
class UACalcRow:
    """One line of the table scripts/jython/con_table.py emits."""

    cardinality: int
    congruences: int


def parse_uacalc_table(text: str) -> Result[Dict[str, UACalcRow], PipelineError]:
    """Read `<name> <cardinality> <|Con(A)|>` lines from scripts/jython/con_table.py."""
    rows: Dict[str, UACalcRow] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 3 or not fields[1].isdigit() or not fields[2].isdigit():
            return Result.err(
                PipelineError(
                    ErrorType.PARSING_ERROR,
                    f"line {number} of the UACalc table is not '<name> <card> <con>': {line!r}",
                )
            )
        if fields[0] in rows:
            # con_table.py emits one line per algebra, so a repeat means the
            # table is not what it claims.  Keeping the last would let two
            # contradictory readings of the same algebra pass as agreement
            # with whichever came second.
            return Result.err(
                PipelineError(
                    ErrorType.PARSING_ERROR,
                    f"line {number}: {fields[0]} appears more than once in the UACalc table",
                )
            )
        rows[fields[0]] = UACalcRow(cardinality=int(fields[1]), congruences=int(fields[2]))
    return Result.ok(rows)


def cross_check(
    comparisons: Sequence[Comparison], uacalc_rows: Dict[str, UACalcRow]
) -> Result[None, PipelineError]:
    """Require UACalc to agree with our own reading of every algebra.

    This is what makes the check a second opinion rather than a restatement:
    the article's algebras were produced with UACalc, so an independent
    implementation agreeing with it is evidence, and a disagreement is a bug in
    one of the two that has to be resolved before either is trusted.

    Both numbers on each row are compared, not just the congruence count.  A
    table generated from a different or stale algebra file would otherwise
    still read as agreement whenever a name and a congruence count happened to
    coincide, which is precisely when a mismatched table is hardest to notice.
    """
    disagreements = [
        message
        for c in comparisons
        if c.algebra in uacalc_rows
        for message in _row_disagreements(c, uacalc_rows[c.algebra])
    ]
    checked = {c.algebra for c in comparisons}
    missing = sorted(name for name in checked if name not in uacalc_rows)
    # Rows we never asked about mean the table was produced from some other
    # file.  Ignoring them lets "UACalc agrees" be printed about a run where
    # the two engines read different algebras, which is the opposite of what
    # the cross-check is for.
    extra = sorted(name for name in uacalc_rows if name not in checked)
    if disagreements or missing or extra:
        detail = "; ".join(
            disagreements
            + [f"{m}: absent from the UACalc table" for m in missing]
            + [f"{e}: in the UACalc table but not in this run" for e in extra]
        )
        return Result.err(PipelineError(ErrorType.VALIDATION_ERROR, detail))
    return Result.ok(None)


def _row_disagreements(comparison: Comparison, row: UACalcRow) -> List[str]:
    """Every way one UACalc row fails to match what we computed."""
    problems = []
    if row.cardinality != comparison.cardinality:
        problems.append(
            f"{comparison.algebra}: we read |A| = {comparison.cardinality}, "
            f"UACalc read {row.cardinality} (the table is from a different algebra file)"
        )
    if row.congruences != comparison.computed.size:
        problems.append(
            f"{comparison.algebra}: we compute {comparison.computed.size}, "
            f"UACalc computes {row.congruences}"
        )
    return problems


def run(algebra_file: Path, article: Path) -> Result[Tuple[Comparison, ...], PipelineError]:
    """Read both sources and compare them.  The pure core of the tool."""
    return read_algebras(algebra_file).and_then(
        lambda algebras: read_catalog(article).and_then(
            lambda catalog: check_diagram_count(catalog, algebras).and_then(
                lambda _: compare_all(algebras, catalog)
            )
        )
    )


def _report(comparisons: Sequence[Comparison]) -> int:
    """Print the outcome, one marked line per check, and return the exit code."""
    # Reaching here means check_diagram_count passed inside run(); say so,
    # since it is a check of its own and would otherwise leave no line.
    print(
        f"{PASS} {ME}  the article draws a diagram for each of the "
        f"{len(comparisons)} lattices these algebras are named for"
    )
    for comparison in comparisons:
        print(comparison.describe())
    failures = [c for c in comparisons if not c.agrees]
    print()
    if failures:
        for failure in failures:
            print(failure.describe_failure())
        print(f"\n{FAIL} {ME}  {len(failures)} of {len(comparisons)} algebras disagree with the article.")
        return 1
    print(f"{PASS} {ME}  all {len(comparisons)} algebras agree with the lattices the article draws.")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse arguments, run the check, turn the Result into an exit code."""
    parser = argparse.ArgumentParser(
        description="Check the article's algebras against the lattices it draws."
    )
    parser.add_argument("algebra_file", type=Path,
                        help="a UACalc .ua file holding the algebras B_i")
    parser.add_argument("article", type=Path,
                        help="article/SmallLatticeReps.tex")
    parser.add_argument("--uacalc-table", type=Path, default=None,
                        help="output of scripts/jython/con_table.py, to cross-check against")
    args = parser.parse_args(argv)

    outcome = run(args.algebra_file, args.article)
    if outcome.is_err:
        print(f"error: {outcome.unwrap_err()}", file=sys.stderr)
        return 2
    comparisons = outcome.unwrap()

    if args.uacalc_table is not None:
        table = read_text(args.uacalc_table).and_then(parse_uacalc_table)
        if table.is_err:
            print(f"error: {table.unwrap_err()}", file=sys.stderr)
            return 2
        rows = table.unwrap()
        agreed = cross_check(comparisons, rows)
        if agreed.is_err:
            print(f"{FAIL} {ME}  UACalc disagrees: {agreed.unwrap_err()}", file=sys.stderr)
            return 2
        # One line per algebra here too: the agreement is 29 checks, not one.
        for comparison in comparisons:
            row = rows[comparison.algebra]
            print(
                f"{PASS} {ME}  {comparison.algebra:<10} UACalc also reads |A| = "
                f"{row.cardinality:>2} and computes |Con(A)| = {row.congruences}"
            )
        print(f"{PASS} {ME}  UACalc agrees on |A| and |Con(A)| for all {len(comparisons)} algebras.\n")

    return _report(comparisons)


if __name__ == "__main__":
    sys.exit(main())
