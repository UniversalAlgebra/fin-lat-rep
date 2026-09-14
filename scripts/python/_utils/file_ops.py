"""
File: scripts/python/_utils/file_ops.py

Description: Filesystem access wrapped in Results.

  Pipeline code never calls `open()` directly; it goes through here, so that a
  missing or unreadable file is a value to be handled rather than an exception
  to be caught somewhere up the stack.
"""

from __future__ import annotations

from pathlib import Path

from _utils.pipeline_types import ErrorType, PipelineError, Result


def read_text(path: Path) -> Result[str, PipelineError]:
    """Read a text file, returning a Result."""
    try:
        return Result.ok(path.read_text("utf-8"))
    except FileNotFoundError:
        return Result.err(
            PipelineError(ErrorType.FILE_NOT_FOUND, f"File not found: {path}")
        )
    except Exception as exc:  # noqa: BLE001 - any read failure is the same to callers
        return Result.err(
            PipelineError(ErrorType.COMMAND_FAILED, f"Failed to read file: {path}", cause=exc)
        )
