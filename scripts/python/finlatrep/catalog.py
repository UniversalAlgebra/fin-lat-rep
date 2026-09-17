r"""
File: scripts/python/finlatrep/catalog.py

Description: Reading the lattices the article draws, out of its LaTeX source.

  Section "Lattices of size at most 7" tabulates each lattice L_i beside the
  algebra B_i said to represent it.  Each diagram is TikZ written inline, as
  `\node(k) at (x,y)[e]{};` for vertices and `\draw(a)--(b);` for covering
  edges.  Those two forms are all that appears there: measured at the time of
  writing, the subsection held 235 node lines and 278 edges, with no `\input`
  and no chained `\draw ... to ...` paths.

  Which end of an edge is the lower one is decided by the y coordinate the
  node is drawn at, NOT by the order the two endpoints happen to be written
  in, and NOT by the vertex numbers.  TikZ's `--` is undirected, so
  `\draw(0)--(1)` and `\draw(1)--(0)` produce the same picture and must
  produce the same covering pair.  And the vertex numbers do not run bottom to
  top: in L28 the article places node 4 at y=0.0 and node 3 at y=0.2, so
  ordering an edge by its endpoint numbers would invert it.  (An earlier
  version of this file claimed the numbering was bottom to top.  It is not.)

  The files under `article/inputs/tikz/` DO use the chained form, but they are
  illustrations in the body of the paper, several of lattices with no catalog
  algebra at all, and are deliberately out of scope.  To stop that going
  quietly out of date, the caller is expected to check the diagram count
  against the algebra count; see `check.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from _utils.file_ops import read_text
from _utils.pipeline_types import ErrorType, PipelineError, Result
from finlatrep.lattice import CoveringRelation

CATALOG_HEADING = r"\subsection{Lattices of size at most 7}"

_LATTICE_LABEL = re.compile(r"\$\\bL_\{?(\d+)\}?\$")
_NODE = re.compile(r"\\node\((\d+)\)\s*at\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)")
_EDGE = re.compile(r"\\draw\((\d+)\)--\((\d+)\)")
# A `%` that is not escaped starts a LaTeX comment and runs to end of line.
_COMMENT = re.compile(r"(?<!\\)%.*$", re.MULTILINE)


@dataclass(frozen=True)
class CatalogEntry:
    """One lattice as the article draws it, with the index it is labelled by."""

    index: int
    relation: CoveringRelation


def strip_latex_comments(text: str) -> str:
    """Remove everything a LaTeX `%` comments out.

    Without this the parser reads commented-out diagrams as if they were
    drawn.  That matters most in exactly the situation `check_diagram_count`
    exists to catch: commenting an inline diagram out and replacing it with an
    `\input` would leave the stale relation visible here, and the check would
    pass while the article no longer draws what it compared against.
    """
    return _COMMENT.sub("", text)


def _entry_from_chunk(index: int, chunk: str) -> Result[CatalogEntry, PipelineError]:
    """Read one lattice out of the LaTeX between two L_i labels.

    Vertices are renumbered to 0 .. n-1 in the order the article names them,
    so that the relation is comparable with a congruence lattice's, which is
    indexed the same way.  Each edge is oriented by the height its endpoints
    are drawn at, so that reversing how an edge is written cannot change the
    lattice it denotes.
    """
    heights = {int(v): float(y) for v, _x, y in _NODE.findall(chunk)}
    vertices = sorted(heights)
    position = {vertex: i for i, vertex in enumerate(vertices)}

    covers = set()
    for raw_a, raw_b in _EDGE.findall(chunk):
        a, b = int(raw_a), int(raw_b)
        if a not in heights or b not in heights:
            missing = a if a not in heights else b
            return Result.err(
                PipelineError(
                    ErrorType.PARSING_ERROR,
                    f"L{index}: edge ({a},{b}) names node {missing}, which is never placed",
                )
            )
        if heights[a] == heights[b]:
            return Result.err(
                PipelineError(
                    ErrorType.PARSING_ERROR,
                    f"L{index}: edge ({a},{b}) joins two nodes drawn at the same height, "
                    "so which one covers the other cannot be read off the diagram",
                )
            )
        lower, upper = (a, b) if heights[a] < heights[b] else (b, a)
        covers.add((position[lower], position[upper]))

    return Result.ok(
        CatalogEntry(
            index=index,
            relation=CoveringRelation(size=len(vertices), covers=frozenset(covers)),
        )
    )


def parse_catalog(text: str) -> Result[Dict[int, CatalogEntry], PipelineError]:
    """Read every lattice drawn in the article's catalog subsection."""
    start = text.find(CATALOG_HEADING)
    if start < 0:
        return Result.err(
            PipelineError(
                ErrorType.PARSING_ERROR,
                f"could not find the catalog subsection, expected {CATALOG_HEADING!r}",
            )
        )
    body = strip_latex_comments(text[start:])
    labels: Tuple[Tuple[int, int], ...] = tuple(
        (match.start(), int(match.group(1))) for match in _LATTICE_LABEL.finditer(body)
    )
    if not labels:
        return Result.err(
            PipelineError(ErrorType.PARSING_ERROR, "the catalog subsection names no lattices")
        )
    bounds = [
        (index, body[position : labels[i + 1][0] if i + 1 < len(labels) else len(body)])
        for i, (position, index) in enumerate(labels)
    ]
    # A lattice labelled twice would silently lose one reading; keep the first.
    entries: Dict[int, CatalogEntry] = {}
    for index, chunk in bounds:
        if index in entries:
            continue
        parsed = _entry_from_chunk(index, chunk)
        if parsed.is_err:
            return Result.err(parsed.unwrap_err())
        entries[index] = parsed.unwrap()
    return Result.ok(entries)


def read_catalog(path: Path) -> Result[Dict[int, CatalogEntry], PipelineError]:
    """Read every lattice drawn in the article's catalog subsection."""
    return read_text(path).and_then(parse_catalog)
