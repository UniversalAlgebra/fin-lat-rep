r"""
File: scripts/python/finlatrep/latex.py

Description: The one piece of LaTeX lexing the checker needs: cutting `%`
  comments out of a source text before anything in it is read.

  Without this a commented-out diagram is read as if it were drawn.  Both
  readers in this package need it: the catalog reader, so that a diagram
  commented out of the article stays invisible, and the pic reader, so that a
  commented-out edge in a file under article/inputs/tikz/ is not counted.
"""

from __future__ import annotations


def _strip_line_comment(line: str) -> str:
    r"""Cut one line at its first unescaped `%`.

    Whether a `%` is escaped is decided by the PARITY of the backslash run in
    front of it, not by the single preceding character.  In `\%` the percent
    is escaped and is a literal.  In `\\%` the `\\` is its own control
    sequence, a line break, and the `%` still opens a comment.  Reading only
    the character before would keep such a line, which is precisely how a
    commented-out diagram would stay visible to this parser.
    """
    index = 0
    while True:
        found = line.find("%", index)
        if found < 0:
            return line
        backslashes = 0
        probe = found - 1
        while probe >= 0 and line[probe] == "\\":
            backslashes += 1
            probe -= 1
        if backslashes % 2 == 0:
            return line[:found]
        index = found + 1


def strip_latex_comments(text: str) -> str:
    r"""Remove everything a LaTeX `%` comments out, line by line."""
    return "\n".join(_strip_line_comment(line) for line in text.split("\n"))
