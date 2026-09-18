"""
File: scripts/python/finlatrep/ua.py

Description: Reading finite algebras out of a UACalc `.ua` file.

  A `.ua` file is XML describing one algebra or a list of them.  This module
  reads the parts the catalog check needs, a name, a cardinality and the
  operation tables, and validates their shape before anything downstream
  trusts them.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from _utils.file_ops import read_text
from _utils.pipeline_types import ErrorType, PipelineError, Result, sequence_results

_INTEGER = re.compile(r"[+-]?\d+")


@dataclass(frozen=True)
class Operation:
    """One operation of a finite algebra, as its table of values."""

    name: str
    arity: int
    table: Tuple[int, ...]


@dataclass(frozen=True)
class Algebra:
    """A finite algebra on the carrier {0, 1, ..., cardinality - 1}."""

    name: str
    cardinality: int
    operations: Tuple[Operation, ...]

    @property
    def unary_operations(self) -> Tuple[Tuple[int, ...], ...]:
        """The tables of the unary operations, which is all the catalog uses."""
        return tuple(op.table for op in self.operations if op.arity == 1)


def _parse_operation(element: ElementTree.Element) -> Result[Operation, PipelineError]:
    """Read one <op> element into an Operation."""
    name = (element.findtext(".//opName") or "?").strip()
    arity_text = (element.findtext(".//arity") or "").strip()
    if not arity_text.isdigit():
        return Result.err(
            PipelineError(ErrorType.PARSING_ERROR, f"operation {name} has no readable arity")
        )
    values: List[int] = []
    for row in element.findall(".//row"):
        for token in (row.text or "").replace(",", " ").split():
            # A stray token here is malformed input, not a bug, so it has to
            # come back as an error rather than a ValueError out of int().
            if not _INTEGER.fullmatch(token):
                return Result.err(
                    PipelineError(
                        ErrorType.PARSING_ERROR,
                        f"operation {name}: {token!r} in an operation table is not an integer",
                    )
                )
            values.append(int(token))
    return Result.ok(Operation(name=name, arity=int(arity_text), table=tuple(values)))


def _validate(algebra: Algebra) -> Result[Algebra, PipelineError]:
    """Reject an algebra whose tables are the wrong shape or out of range.

    Worth doing before any congruence is computed: a truncated table otherwise
    produces a plausible-looking lattice rather than an error.
    """
    for op in algebra.operations:
        expected = algebra.cardinality**op.arity
        if len(op.table) != expected:
            return Result.err(
                PipelineError(
                    ErrorType.VALIDATION_ERROR,
                    f"{algebra.name}.{op.name}: expected {expected} values, found {len(op.table)}",
                )
            )
        out_of_range = sorted({v for v in op.table if not 0 <= v < algebra.cardinality})
        if out_of_range:
            return Result.err(
                PipelineError(
                    ErrorType.VALIDATION_ERROR,
                    f"{algebra.name}.{op.name}: values outside the carrier: {out_of_range}",
                )
            )
    return Result.ok(algebra)


def _parse_algebra(element: ElementTree.Element) -> Result[Algebra, PipelineError]:
    """Read one <basicAlgebra> element into a validated Algebra."""
    name = (element.findtext("algName") or "?").strip()
    cardinality_text = (element.findtext("cardinality") or "").strip()
    if not cardinality_text.isdigit():
        return Result.err(
            PipelineError(ErrorType.PARSING_ERROR, f"algebra {name} has no readable cardinality")
        )
    if int(cardinality_text) < 1:
        # `0` is a digit string, and a unary table of length zero then passes
        # the shape check, so an empty carrier would reach the congruence code
        # and be reported as having a one-element congruence lattice.  An
        # algebra has a nonempty carrier.
        return Result.err(
            PipelineError(
                ErrorType.VALIDATION_ERROR,
                f"algebra {name} has cardinality {cardinality_text}; a carrier cannot be empty",
            )
        )
    operations = sequence_results([_parse_operation(op) for op in element.findall(".//op")])
    return operations.and_then(
        lambda ops: _validate(
            Algebra(name=name, cardinality=int(cardinality_text), operations=tuple(ops))
        )
    )


def parse_algebras(text: str) -> Result[Tuple[Algebra, ...], PipelineError]:
    """Read every algebra in the XML of a `.ua` file, in document order."""
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        return Result.err(
            PipelineError(ErrorType.PARSING_ERROR, "file is not well-formed XML", cause=exc)
        )
    elements = list(root.iter("basicAlgebra"))
    if not elements:
        # Otherwise the caller compares nothing, reports that everything it
        # compared agreed, and exits 0.  A gate that does no work must fail.
        return Result.err(
            PipelineError(
                ErrorType.VALIDATION_ERROR,
                "no <basicAlgebra> elements: this is not a UACalc algebra file, "
                "or it is empty",
            )
        )
    parsed = sequence_results([_parse_algebra(element) for element in elements])
    return parsed.map(tuple)


def read_algebras(path: Path) -> Result[Tuple[Algebra, ...], PipelineError]:
    """Read every algebra in a `.ua` file."""
    return read_text(path).and_then(parse_algebras)
