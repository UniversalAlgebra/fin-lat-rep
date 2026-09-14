"""
File: scripts/python/_utils/pipeline_types.py

Description: Functional error handling for this repository's Python.

  A `Result[T, E]` is either a success or a failure, and a function that can
  fail returns one instead of raising.  `raise` is reserved for genuine bugs.

Provenance:

  The `Result`, `ErrorType` and `PipelineError` API is copied deliberately,
  name for name, from the `_utils` package these projects carry elsewhere (see
  williamdemeo.github.io and agda-algebras), so that code moves between them
  without adaptation.  Only the pieces this repository actually uses are here:
  the upstream package also carries a documentation-build pipeline's domain
  types, which a LaTeX paper repository has no use for and which would rot.
  If this repository ever grows a second Python tool that needs more, take the
  additional pieces from upstream rather than inventing them here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar

T = TypeVar("T")
B = TypeVar("B")
E = TypeVar("E")


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Either a successful computation (Ok) or a failure (Err)."""

    _is_ok: bool
    _value: Optional[T] = None
    _error: Optional[E] = None

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """Construct a successful result."""
        return cls(_is_ok=True, _value=value, _error=None)

    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        """Construct a failed result."""
        if error is None:
            raise ValueError("Cannot create an Err result with a None value.")
        return cls(_is_ok=False, _value=None, _error=error)

    @property
    def is_ok(self) -> bool:
        """True if this is a successful result."""
        return self._is_ok

    @property
    def is_err(self) -> bool:
        """True if this is a failed result."""
        return not self._is_ok

    def unwrap(self) -> T:
        """Extract the success value; raises if this is an error."""
        if self._is_ok:
            return self._value  # type: ignore[return-value]
        raise ValueError(f"Called unwrap() on error result: {self._error}")

    def unwrap_or(self, default: T) -> T:
        """Extract the success value, or return the default."""
        return self._value if self._is_ok and self._value is not None else default

    def unwrap_err(self) -> E:
        """Extract the error value; raises if this is a success."""
        if self._is_ok:
            raise ValueError(f"Called unwrap_err() on a success result: {self._value}")
        if self._error is None:
            raise ValueError("Called unwrap_err() on an Err holding no error value.")
        return self._error

    def map(self, f: Callable[[T], B]) -> "Result[B, E]":
        """Apply a function to the success value, preserving an error."""
        if self._is_ok:
            return Result.ok(f(self._value))  # type: ignore[arg-type]
        return Result.err(self._error)  # type: ignore[arg-type]

    def map_err(self, f: Callable[[E], B]) -> "Result[T, B]":
        """Apply a function to the error value, preserving a success."""
        if self._is_ok:
            return Result.ok(self._value)  # type: ignore[arg-type]
        return Result.err(f(self._error))  # type: ignore[arg-type]

    def flat_map(self, f: Callable[[T], "Result[B, E]"]) -> "Result[B, E]":
        """Monadic bind: chain a computation that might itself fail."""
        if self._is_ok:
            return f(self._value)  # type: ignore[arg-type]
        return Result.err(self._error)  # type: ignore[arg-type]

    def and_then(self, f: Callable[[T], "Result[B, E]"]) -> "Result[B, E]":
        """Alias for flat_map, which reads better in a chain."""
        return self.flat_map(f)


class ErrorType(Enum):
    """Categorization of errors, for structured handling."""

    FILE_NOT_FOUND = auto()
    PARSING_ERROR = auto()
    VALIDATION_ERROR = auto()
    COMMAND_FAILED = auto()


@dataclass(frozen=True)
class PipelineError:
    """An immutable error with a category, a message, and context."""

    error_type: ErrorType
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    cause: Optional[Exception] = None

    def with_context(self, **kwargs: Any) -> "PipelineError":
        """Add context, returning a new error."""
        return PipelineError(
            error_type=self.error_type,
            message=self.message,
            context={**self.context, **kwargs},
            cause=self.cause,
        )

    def __str__(self) -> str:
        parts = [f"{self.error_type.name}: {self.message}"]
        if self.context:
            parts.append("Context: " + ", ".join(f"{k}={v}" for k, v in self.context.items()))
        if self.cause:
            parts.append(f"Caused by: {self.cause}")
        return " | ".join(parts)


def sequence_results(results: List[Result[T, E]]) -> Result[List[T], E]:
    """Turn a list of Results into a Result of a list, failing on the first error."""
    values: List[T] = []
    for result in results:
        if result.is_err:
            return Result.err(result.unwrap_err())
        values.append(result.unwrap())
    return Result.ok(values)


def collect_errors(results: List[Result[T, E]]) -> Tuple[List[T], List[E]]:
    """Partition a list of Results into its successes and its failures."""
    return (
        [r.unwrap() for r in results if r.is_ok],
        [r.unwrap_err() for r in results if r.is_err],
    )
