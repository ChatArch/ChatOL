"""Typed exceptions for ChatOL workflows."""

from __future__ import annotations


class ChatOLError(Exception):
    """Base class for all user-facing ChatOL errors."""

    code = "chatol_error"

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class AuthenticationError(ChatOLError):
    """Raised when login or session validation fails."""

    code = "auth_required"


class UnsupportedRouteError(ChatOLError):
    """Raised when an Overleaf internal route is unavailable."""

    code = "unsupported_route"


class ProjectNotFoundError(ChatOLError):
    """Raised when a project cannot be resolved by id or name."""

    code = "project_not_found"


class FileOperationError(ChatOLError):
    """Raised when an Overleaf file operation fails."""

    code = "file_operation_failed"


class CompileError(ChatOLError):
    """Raised when Overleaf returns a non-success compile status."""

    code = "compile_failed"

    def __init__(
        self,
        status: str,
        message: str | None = None,
        *,
        retryable: bool | None = None,
    ) -> None:
        self.status = status
        if retryable is None:
            retryable = status in {"too-recently-compiled", "compile-in-progress"}
        super().__init__(message or f"Compilation failed: {status}", retryable=retryable)
        if status == "too-recently-compiled":
            self.code = "compile_too_recent"
