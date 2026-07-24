"""Typed failures shared by the modern-judge package."""

from __future__ import annotations

from typing import Any


class JudgeError(RuntimeError):
    """Base package error."""


class AdapterError(JudgeError):
    """Provider or local runtime failure."""


class ParseError(JudgeError):
    """Raw model output violates the frozen parser contract."""


class RoutingRejected(JudgeError):
    """Returned model or route violates the frozen routing policy."""

    def __init__(self, message: str, *, response: Any | None = None) -> None:
        super().__init__(message)
        self.response = response


class ConfigurationError(JudgeError):
    """Immutable run configuration is invalid; fail before row execution."""


class IntegrityError(JudgeError):
    """Input, prompt, context-length, or stored-state integrity failure."""
