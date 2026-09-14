r"""
File: scripts/python/finlatrep/catalog.py

Description: Reading the lattices the article draws, out of its LaTeX source.

  Section "Lattices of size at most 7" tabulates each lattice L_i beside the
  algebra B_i said to represent it.  Each diagram is TikZ written inline, as
  `\node(k) at (x,y)[e]{};` for vertices and `\draw(a)--(b);` for covering
  edges, and the vertex numbers run bottom to top.  Those two forms are all
  that appears there: measured at the time of writing, the subsection held 235
  node lines and 278 edges, with no `\input` and no chained `\draw ... to ...`
  paths.

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
_NODE = re.compile(r"\\node\((\d+)\)\s*at")
_EDGE = re.compile(r"\\draw\((\d+)\)--\((\d+)\)")


@dataclass(frozen=True)
class CatalogEntry:
    """One lattice as the article draws it, with the index it is labelled by."""

    index: int
    relation: CoveringRelation


def _entry_from_chunk(index: int, chunk: str) -> CatalogEntry:
    """Read one lattice out of the LaTeX between two L_i labels.

    Vertices are renumbered to 0 .. n-1 in the order the article names them,
    so that the relation is comparable with a congruence lattice's, which is
    indexed the same way.
    """
    vertices = sorted({int(v) for v in _NODE.findall(chunk)})
    position = {vertex: i for i, vertex in enumerate(vertices)}
    covers = frozenset(
        (position[int(a)], position[int(b)]) for a, b in _EDGE.findall(chunk)
    )
    return CatalogEntry(
        index=index,
        relation=CoveringRelation(size=len(vertices), covers=covers),
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
    body = text[start:]
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
        entries.setdefault(index, _entry_from_chunk(index, chunk))
    return Result.ok(entries)


def read_catalog(path: Path) -> Result[Dict[int, CatalogEntry], PipelineError]:
    """Read every lattice drawn in the article's catalog subsection."""
    return read_text(path).and_then(parse_catalog)
