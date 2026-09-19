r"""
File: scripts/python/finlatrep/pic.py

Description: Reading a Hasse diagram out of one TikZ pic file under
  article/inputs/tikz/, together with the metadata header the file opens with.

  Every file there has the same shape, written down in
  article/inputs/tikz/README.md: a header of `% key: value` lines, then one
  `\tikzset{NAME/.pic={ ... }}` whose body places vertices as
  `\node[lat] (name) at (x,y) {};` and draws covering edges as
  `\draw (a) -- (b);`, one per line.

  The pic's body is found by matching the braces of `\tikzset{NAME/.pic={`,
  and a file whose pic is never closed, or that carries anything after the
  close, is rejected: TeX would otherwise read on into the next `\input` and
  the build would die with "File ended while scanning", with every node and
  edge line in the file perfectly readable here.

  In a lattice file, one that declares `covers:`, those two forms are the ONLY
  ones allowed, and a line that is neither is rejected.  Ignoring such a line
  instead would be unsound in one direction: a line this module cannot read is
  still drawn by TeX, so `\draw (0) to (4);` would put an edge in the picture
  that is in neither the parsed drawing nor the header, and the cross-check
  would agree with itself about a lattice the reader never sees.  (A line that
  LOSES a vertex or an edge is caught by the header either way.)  A schematic
  file, one with no `covers:`, draws things this module has no opinion about,
  so its body is not restricted.

  Which end of an edge is the lower one is decided by the y coordinate the two
  vertices are placed at.  TikZ's `--` is undirected, so `\draw (0) -- (1);`
  and `\draw (1) -- (0);` draw the same picture and must yield the same cover.

  Vertices are indexed by the sorted order of their names, so that a relation
  read here can be compared with a congruence lattice's, which is indexed 0 to
  n-1 in its own order; comparison is by isomorphism in any case.  Between the
  drawing and the header, though, the names are the same names, and the two
  relations are compared for equality, which is the stronger check and gives
  the better message: the pairs that differ.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, Optional, Set, Tuple

from _utils.file_ops import read_text
from _utils.pipeline_types import ErrorType, PipelineError, Result
from finlatrep.latex import strip_latex_comments
from finlatrep.lattice import CoveringRelation

# The fixed vocabulary of the header.  A file may omit `elements`, `covers`
# and `represented-by` when it draws something that is not a lattice (the
# potato diagrams of the closure-properties figures); a lattice file carries
# them all, and the checker holds it to them.
HEADER_KEYS: Tuple[str, ...] = (
    "id", "aliases", "elements", "covers", "represented-by", "tags",
)

# A header line is a single `%`, one space, a key from HEADER_KEYS, a colon.
# Any other comment line at the top of the file is free text and ignored.
_HEADER_LINE = re.compile(r"^% ([a-z][a-z-]*):[ \t]*(.*?)\s*$")
_PIC_OPEN = re.compile(r"\\tikzset\{([\w-]+)/\.pic=\{")
_NODE = re.compile(
    r"\\node\[lat\]\s*\(([\w-]+)\)\s*at\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)\s*\{\}\s*;"
)
_EDGE = re.compile(r"\\draw\s*\(([\w-]+)\)\s*--\s*\(([\w-]+)\)\s*;")
_COVER = re.compile(r"^([\w-]+)<([\w-]+)$")
# The two lines that open and close the pic, which a body otherwise consists
# entirely of vertices and edges.
_PIC_OPEN_LINE = re.compile(r"\s*\\tikzset\{[\w-]+/\.pic=\{\s*")
_PIC_CLOSE_LINE = re.compile(r"\s*\}\}\s*")


@dataclass(frozen=True)
class Pic:
    """One pic file: its name, its header, and the lattice it draws.

    `drawn` is read off the body and `declared` off the header's `covers:`
    line; both are on the same vertices, indexed by `vertices`.  `declared` is
    None when the header has no `covers:` line, which only a non-lattice file
    is allowed.
    """

    name: str
    header: Dict[str, str]
    vertices: Tuple[str, ...]
    drawn: CoveringRelation
    declared: Optional[CoveringRelation]

    def named(self, relation: CoveringRelation) -> Tuple[str, ...]:
        """A relation on this pic's vertices, as `a<b` strings for a message."""
        return tuple(
            f"{self.vertices[a]}<{self.vertices[b]}" for a, b in relation.sorted_covers()
        )


def _error(where: str, message: str) -> PipelineError:
    return PipelineError(ErrorType.PARSING_ERROR, f"{where}: {message}")


def parse_header(text: str, where: str = "pic") -> Result[Dict[str, str], PipelineError]:
    """Read the `% key: value` lines a pic file opens with.

    The header ends at the first line that is not a comment.  A comment line
    that is not of the `% key:` form is free text and is skipped; a line of
    that form with a key outside HEADER_KEYS is an error, so that a misspelt
    `% cover:` cannot silently drop the check that `covers:` exists to make.
    """
    header: Dict[str, str] = {}
    for line in text.split("\n"):
        if not line.startswith("%"):
            break
        match = _HEADER_LINE.match(line)
        if match is None:
            continue
        key, value = match.group(1), match.group(2)
        if key not in HEADER_KEYS:
            return Result.err(
                _error(where, f"unknown header key {key!r}; the keys are {', '.join(HEADER_KEYS)}")
            )
        if key in header:
            return Result.err(_error(where, f"header key {key!r} appears twice"))
        header[key] = value
    return Result.ok(header)


def _pic_body(text: str, where: str) -> Result[str, PipelineError]:
    r"""The text inside `\tikzset{NAME/.pic={ ... }}`, found by matching braces.

    A file is a header and one pic, and this is where that is enforced on
    both sides: nothing but whitespace before the opener, nothing after the
    close.  Reading the body rather than the whole file is what makes an
    unterminated pic an error here instead of a file that parses cleanly and
    then stops `make paper` with "File ended while scanning use of
    \pgfkeys@@qset" and no PDF.  Counting the opener alone cannot see that:
    every node and edge line before the missing `}}` is still perfectly
    readable.

    The same is true of a line before the opener.  It is read by neither the
    drawing nor the header, so the cross-check passes, and TeX meets it at
    the point of `\input`, which is the article's preamble: measured, a
    `\node[lat]` line there ends the build with "Undefined control sequence"
    and no PDF.

    Braces are counted literally.  No file in this directory escapes one, and
    a file that did would be reported here as unbalanced rather than silently
    miscounted, which is the safe direction for a gate.
    """
    opener = _PIC_OPEN.search(text)
    if opener is None:
        return Result.err(_error(where, "no pic to read"))
    # Comments are already stripped, so whatever is left here is TeX that
    # sits outside the pic and is read where the file is \input.
    before = text[: opener.start()].strip()
    if before:
        return Result.err(
            _error(
                where,
                "there is text before the pic's `\\tikzset`: "
                f"{before.splitlines()[0]!r}; a file is a header and one pic, and a "
                "node or edge written outside the pic is drawn by neither the pic nor "
                "anything else, but TeX still reads it where the file is \\input",
            )
        )
    # Two braces are already open at the end of the match: `	ikzset{` and
    # the `{` of `.pic={`.
    depth = 2
    body_ends = None
    for index in range(opener.end(), len(text)):
        character = text[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 1 and body_ends is None:
                body_ends = index
            if depth == 0:
                trailing = text[index + 1 :].strip()
                if trailing:
                    return Result.err(
                        _error(
                            where,
                            "there is text after the pic's closing `}}`: "
                            f"{trailing.splitlines()[0]!r}; a file defines one pic and "
                            "nothing else (an extra `}}` looks like this too)",
                        )
                    )
                return Result.ok(text[opener.end() : body_ends])
    return Result.err(
        _error(
            where,
            "the pic is never closed: the file ends inside "
            "`\\tikzset{...}}`.  TeX would go on reading the next \\input, and the "
            "build would fail with `File ended while scanning`",
        )
    )


def _recognized(line: str) -> bool:
    """Whether one line of a pic body is a form this module reads."""
    stripped = line.strip()
    if not stripped:
        return True
    return bool(
        _NODE.fullmatch(stripped)
        or _EDGE.fullmatch(stripped)
        or _PIC_OPEN_LINE.fullmatch(line)
        or _PIC_CLOSE_LINE.fullmatch(line)
    )


def _check_every_line_is_read(body: str, where: str) -> Result[None, PipelineError]:
    r"""Refuse a lattice file that draws anything this module cannot read.

    TeX draws what this module skips.  An edge written `\draw (0) to (4);`, or
    with options, is therefore in the picture but in neither the parsed drawing
    nor the header, and the drawing would agree with `covers:` about a lattice
    that is not the one on the page.
    """
    offending = [
        (number, line.strip())
        for number, line in enumerate(body.split("\n"), start=1)
        if not _recognized(line)
    ]
    if offending:
        number, text = offending[0]
        return Result.err(
            _error(
                where,
                f"line {number} is not a form the checker reads: {text!r}; a lattice file's "
                "pic body holds only `\\node[lat] (name) at (x,y) {};` and `\\draw (a) -- (b);` "
                "lines, one per line (a file with no covers: line is a schematic and is exempt)",
            )
        )
    return Result.ok(None)


def _coordinate(
    where: str, name: str, axis: str, value: str
) -> Result[float, PipelineError]:
    r"""One coordinate as a number.

    `[-\d.]+` will happily match `.` or `-.-`, and float() would then raise
    straight past the Result the rest of this module returns.  Both
    coordinates are checked: an unreadable x never reaches the covering
    relation, but it is still a malformed file and TeX will not draw it.
    """
    try:
        return Result.ok(float(value))
    except ValueError:
        return Result.err(
            _error(where, f"vertex {name} is placed at {axis}={value!r}, which is not a number")
        )


def _heights(body: str, where: str) -> Result[Dict[str, float], PipelineError]:
    """Every placed vertex and the height it is placed at."""
    heights: Dict[str, float] = {}
    for name, x, y in _NODE.findall(body):
        if name in heights:
            return Result.err(_error(where, f"vertex {name} is placed twice"))
        across = _coordinate(where, name, "x", x)
        if across.is_err:
            return Result.err(across.unwrap_err())
        height = _coordinate(where, name, "y", y)
        if height.is_err:
            return Result.err(height.unwrap_err())
        heights[name] = height.unwrap()
    if not heights:
        return Result.err(_error(where, r"places no vertex; expected `\node[lat] (name) at (x,y) {};` lines"))
    return Result.ok(heights)


def _drawn(
    body: str, heights: Dict[str, float], position: Dict[str, int], where: str
) -> Result[FrozenSet[Tuple[int, int]], PipelineError]:
    """The covering pairs the body draws, each oriented by height."""
    covers: Set[Tuple[int, int]] = set()
    for a, b in _EDGE.findall(body):
        if a not in heights or b not in heights:
            missing = a if a not in heights else b
            return Result.err(
                _error(where, f"edge ({a})--({b}) names vertex {missing}, which is never placed")
            )
        if heights[a] == heights[b]:
            return Result.err(
                _error(
                    where,
                    f"edge ({a})--({b}) joins two vertices drawn at the same height, "
                    "so which one covers the other cannot be read off the diagram",
                )
            )
        lower, upper = (a, b) if heights[a] < heights[b] else (b, a)
        covers.add((position[lower], position[upper]))
    return Result.ok(frozenset(covers))


def _declared(
    header: Dict[str, str], position: Dict[str, int], where: str
) -> Result[Optional[FrozenSet[Tuple[int, int]]], PipelineError]:
    """The covering pairs the header's `covers:` line declares, if it has one."""
    line = header.get("covers")
    if line is None:
        return Result.ok(None)
    covers: Set[Tuple[int, int]] = set()
    for token in line.split():
        match = _COVER.match(token)
        if match is None:
            return Result.err(
                _error(where, f"covers: token {token!r} is not of the form lower<upper")
            )
        lower, upper = match.group(1), match.group(2)
        for name in (lower, upper):
            if name not in position:
                return Result.err(
                    _error(where, f"covers: names vertex {name}, which the drawing never places")
                )
        covers.add((position[lower], position[upper]))
    return Result.ok(frozenset(covers))


def _check_elements(header: Dict[str, str], count: int, where: str) -> Result[None, PipelineError]:
    """`elements:`, when present, must be the number of vertices drawn."""
    declared = header.get("elements")
    if declared is None:
        return Result.ok(None)
    if not declared.isdigit() or int(declared) != count:
        return Result.err(
            _error(where, f"header says elements: {declared}, but the drawing places {count} vertices")
        )
    return Result.ok(None)


def _sort_key(name: str) -> Tuple[int, int, str]:
    """Numbers before words, numbers by value: `2` before `10`, both before `top`."""
    return (0, int(name), "") if name.isdigit() else (1, 0, name)


def parse_pic(text: str, where: str = "pic") -> Result[Pic, PipelineError]:
    r"""Read one pic file's header, name, drawing, and declared covers."""
    header_result = parse_header(text, where)
    if header_result.is_err:
        return Result.err(header_result.unwrap_err())
    header = header_result.unwrap()

    body = strip_latex_comments(text)
    names = _PIC_OPEN.findall(body)
    if len(names) != 1:
        return Result.err(
            _error(where, f"expected exactly one \\tikzset{{NAME/.pic={{...}}}}, found {len(names)}")
        )
    name = names[0]
    if "id" not in header:
        return Result.err(_error(where, "the header has no id: line"))
    if header["id"] != name:
        return Result.err(
            _error(where, f"the header says id: {header['id']} but the pic is named {name}")
        )

    if "covers" in header:
        strict = _check_every_line_is_read(body, where)
        if strict.is_err:
            return Result.err(strict.unwrap_err())

    enclosed = _pic_body(body, where)
    if enclosed.is_err:
        return Result.err(enclosed.unwrap_err())
    # Vertices and edges are read from inside the pic, so that anything
    # outside it cannot contribute to the drawing this file claims to be.
    drawing = enclosed.unwrap()

    heights_result = _heights(drawing, where)
    if heights_result.is_err:
        return Result.err(heights_result.unwrap_err())
    heights = heights_result.unwrap()
    vertices = tuple(sorted(heights, key=_sort_key))
    position = {vertex: i for i, vertex in enumerate(vertices)}

    counted = _check_elements(header, len(vertices), where)
    if counted.is_err:
        return Result.err(counted.unwrap_err())
    drawn = _drawn(drawing, heights, position, where)
    if drawn.is_err:
        return Result.err(drawn.unwrap_err())
    declared = _declared(header, position, where)
    if declared.is_err:
        return Result.err(declared.unwrap_err())
    declared_covers = declared.unwrap()

    return Result.ok(
        Pic(
            name=name,
            header=header,
            vertices=vertices,
            drawn=CoveringRelation(size=len(vertices), covers=drawn.unwrap()),
            declared=(
                None
                if declared_covers is None
                else CoveringRelation(size=len(vertices), covers=declared_covers)
            ),
        )
    )


def read_pic(path: Path) -> Result[Pic, PipelineError]:
    """Read a pic file, and require the pic to be named after the file."""
    def named_after_file(pic: Pic) -> Result[Pic, PipelineError]:
        if pic.name != path.stem:
            return Result.err(
                _error(path.name, f"the pic is named {pic.name}, but a file's pic must share its name")
            )
        return Result.ok(pic)

    return read_text(path).and_then(lambda text: parse_pic(text, path.name)).and_then(named_after_file)
