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

  Until #6 the diagrams were TikZ written straight into the article, and this
  module read them there.  The file form is read by pic.py, which orients each
  edge by the height its endpoints are drawn at, never by the order they are
  written in and never by their names: the catalog's own numbering was not
  bottom to top (L28 placed node 4 at y=0.0 and node 3 at y=0.2).

  The caller is expected to check that every algebra's lattice has an entry
  here (the catalog draws more lattices than there are algebras, by design);
  see `check_diagram_count` in `check.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

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


@dataclass(frozen=True)
class CatalogEntry:
    """One lattice as the catalog draws it, with the index it is labelled by.

    `drawn` is what the picture shows; `declared` is what the file's header
    says it shows, on the same vertices.  `source` is the file, for messages.
    """

    index: int
    drawn: CoveringRelation
    declared: CoveringRelation
    source: str


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
    read = read_pic(tikz_dir / f"{name}.tex")
    if read.is_err:
        return Result.err(read.unwrap_err().with_context(lattice=f"L{index}"))
    pic = read.unwrap()
    if pic.declared is None:
        return Result.err(
            _parse_error(f"L{index}: {source} has no covers: line in its header; a catalog file must declare its covers")
        )
    return Result.ok(CatalogEntry(index=index, drawn=pic.drawn, declared=pic.declared, source=source))


def _entry_from_chunk(index: int, chunk: str, tikz_dir: Path) -> Result[CatalogEntry, PipelineError]:
    r"""One catalog entry: the one `\hasse` call between this label and the next."""
    calls = _HASSE_CALL.findall(chunk)
    if len(calls) > 1:
        return Result.err(
            _parse_error(
                f"L{index} is drawn by more than one \\hasse call ({', '.join(calls)}); "
                "which drawing the algebra should be checked against is ambiguous"
            )
        )
    if not calls:
        return Result.err(
            _parse_error(f"L{index} is labelled but not drawn: expected \\hasse{{L{index}}} beside the label")
        )
    return _entry_from_file(index, calls[0], tikz_dir)


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
