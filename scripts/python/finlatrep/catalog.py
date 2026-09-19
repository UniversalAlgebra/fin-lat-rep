r"""
File: scripts/python/finlatrep/catalog.py

Description: Reading the lattices the article's catalog draws.

  Section "Lattices of size at most 7" tabulates each lattice L_i beside the
  algebra B_i said to represent it.  Each L_i is drawn by a call
  `\hasse{L<i>}`, which draws the TikZ pic defined in
  `article/inputs/tikz/L<i>.tex`; this module finds the call beside each
  label, holds it to the naming convention (the catalog's L_i is drawn by
  L<i>.tex and by nothing else), and reads the file through `pic.py`, which
  yields both the drawing and the covering relation the file's header
  declares.

  Transitional: until the last catalog diagram has moved into its file, an
  entry with no `\hasse` call is read in the older inline form, `\node(k) at
  (x,y)[e]{};` and `\draw(a)--(b);` written straight into the article.  That
  form has no header, so such an entry has no declared relation.  Both forms
  orient each edge by the height its endpoints are drawn at, never by the
  order the endpoints are written and never by the vertex numbers: in L28 the
  article placed node 4 at y=0.0 and node 3 at y=0.2.

  The caller is expected to check that every algebra's lattice has an entry
  here (the catalog draws more lattices than there are algebras, by design);
  see `check_diagram_count` in `check.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from _utils.file_ops import read_text
from _utils.pipeline_types import ErrorType, PipelineError, Result
from finlatrep.latex import strip_latex_comments
from finlatrep.lattice import CoveringRelation
from finlatrep.pic import read_pic

CATALOG_HEADING = r"\subsection{Lattices of size at most 7}"
# The pic files, relative to the article's own directory.
TIKZ_DIR = Path("inputs") / "tikz"

_LATTICE_LABEL = re.compile(r"\$\\bL_\{?(\d+)\}?\$")
_HASSE_CALL = re.compile(r"\\hasse(?:\[[^\]]*\])?\{([\w-]+)\}")
_INLINE_NODE = re.compile(r"\\node\((\d+)\)\s*at\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)")
_INLINE_EDGE = re.compile(r"\\draw\((\d+)\)--\((\d+)\)")


@dataclass(frozen=True)
class CatalogEntry:
    """One lattice as the catalog draws it, with the index it is labelled by.

    `drawn` is what the picture shows; `declared` is what the file's header
    says it shows, on the same vertices, or None for an inline entry, which
    has no header.  `source` names where the drawing came from, for messages.
    """

    index: int
    drawn: CoveringRelation
    declared: Optional[CoveringRelation]
    source: str

    @property
    def relation(self) -> CoveringRelation:
        """The drawing, which is what an algebra is compared against."""
        return self.drawn


def _parse_error(message: str) -> PipelineError:
    return PipelineError(ErrorType.PARSING_ERROR, message)


def _entry_from_file(index: int, name: str, tikz_dir: Path) -> Result[CatalogEntry, PipelineError]:
    r"""Read L_i from the file its `\hasse` call names.

    The call must name `L<i>`: the convention that the catalog's L_i lives in
    L<i>.tex is what lets anyone find a lattice's file from its number, and a
    call drawing some other file beside the label would make the picture and
    the algebra check disagree about which lattice L_i is.
    """
    if name != f"L{index}":
        return Result.err(
            _parse_error(
                f"L{index} is drawn by \\hasse{{{name}}}, but the catalog's L{index} "
                f"must be drawn by inputs/tikz/L{index}.tex"
            )
        )
    source = f"{TIKZ_DIR.as_posix()}/{name}.tex"
    pic = read_pic(tikz_dir / f"{name}.tex")
    if pic.is_err:
        return Result.err(pic.unwrap_err().with_context(lattice=f"L{index}"))
    if pic.unwrap().declared is None:
        return Result.err(
            _parse_error(f"L{index}: {source} has no covers: line in its header; a catalog file must declare its covers")
        )
    return Result.ok(
        CatalogEntry(index=index, drawn=pic.unwrap().drawn, declared=pic.unwrap().declared, source=source)
    )


def _entry_from_inline(index: int, chunk: str) -> Result[CatalogEntry, PipelineError]:
    """Transitional: read one lattice written inline between two L_i labels.

    Vertices are renumbered to 0 .. n-1 in the order the article names them.
    Each edge is oriented by the height its endpoints are drawn at.
    """
    heights = {}
    for v, _x, y in _INLINE_NODE.findall(chunk):
        try:
            heights[int(v)] = float(y)
        except ValueError:
            return Result.err(
                _parse_error(f"L{index}: node {v} is placed at y={y!r}, which is not a number")
            )
    if not heights:
        return Result.err(
            _parse_error(f"L{index} is labelled but neither drawn with \\hasse nor drawn inline")
        )
    vertices = sorted(heights)
    position = {vertex: i for i, vertex in enumerate(vertices)}

    covers = set()
    for raw_a, raw_b in _INLINE_EDGE.findall(chunk):
        a, b = int(raw_a), int(raw_b)
        if a not in heights or b not in heights:
            missing = a if a not in heights else b
            return Result.err(
                _parse_error(f"L{index}: edge ({a},{b}) names node {missing}, which is never placed")
            )
        if heights[a] == heights[b]:
            return Result.err(
                _parse_error(
                    f"L{index}: edge ({a},{b}) joins two nodes drawn at the same height, "
                    "so which one covers the other cannot be read off the diagram"
                )
            )
        lower, upper = (a, b) if heights[a] < heights[b] else (b, a)
        covers.add((position[lower], position[upper]))

    return Result.ok(
        CatalogEntry(
            index=index,
            drawn=CoveringRelation(size=len(vertices), covers=frozenset(covers)),
            declared=None,
            source="inline",
        )
    )


def _entry_from_chunk(index: int, chunk: str, tikz_dir: Path) -> Result[CatalogEntry, PipelineError]:
    r"""One catalog entry: a `\hasse` call to a file, else the inline form."""
    calls = _HASSE_CALL.findall(chunk)
    if len(calls) > 1:
        return Result.err(
            _parse_error(
                f"L{index} is drawn by more than one \\hasse call ({', '.join(calls)}); "
                "which drawing the algebra should be checked against is ambiguous"
            )
        )
    if calls:
        return _entry_from_file(index, calls[0], tikz_dir)
    return _entry_from_inline(index, chunk)


def parse_catalog(text: str, tikz_dir: Path) -> Result[Dict[int, CatalogEntry], PipelineError]:
    """Read every lattice drawn in the article's catalog subsection.

    `tikz_dir` is where the pic files are: the article's `inputs/tikz/`.
    """
    start = text.find(CATALOG_HEADING)
    if start < 0:
        return Result.err(
            _parse_error(f"could not find the catalog subsection, expected {CATALOG_HEADING!r}")
        )
    body = strip_latex_comments(text[start:])
    labels: Tuple[Tuple[int, int], ...] = tuple(
        (match.start(), int(match.group(1))) for match in _LATTICE_LABEL.finditer(body)
    )
    if not labels:
        return Result.err(_parse_error("the catalog subsection names no lattices"))
    bounds: List[Tuple[int, str]] = [
        (index, body[position : labels[i + 1][0] if i + 1 < len(labels) else len(body)])
        for i, (position, index) in enumerate(labels)
    ]
    entries: Dict[int, CatalogEntry] = {}
    for index, chunk in bounds:
        if index in entries:
            # Keeping the first reading and dropping the rest would leave the
            # unique-entry count at 35 while a second, different drawing of the
            # same lattice went uncompared, which is the failure
            # check_diagram_count exists to make loud.
            return Result.err(
                _parse_error(
                    f"L{index} is labelled more than once in the catalog; "
                    "which drawing the algebra should be checked against is ambiguous"
                )
            )
        parsed = _entry_from_chunk(index, chunk, tikz_dir)
        if parsed.is_err:
            return Result.err(parsed.unwrap_err())
        entries[index] = parsed.unwrap()
    return Result.ok(entries)


def read_catalog(path: Path) -> Result[Dict[int, CatalogEntry], PipelineError]:
    """Read every lattice the article at `path` draws in its catalog subsection.

    The pic files are found relative to the article, at inputs/tikz/.
    """
    return read_text(path).and_then(lambda text: parse_catalog(text, path.parent / TIKZ_DIR))
