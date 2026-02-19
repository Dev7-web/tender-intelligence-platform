"""
Custom exceptions for the application.
"""

from __future__ import annotations

from typing import Optional


class AppError(Exception):
    """Base application error."""

    code = "APP_ERROR"

    def __init__(self, message: str, code: Optional[str] = None, field: Optional[str] = None) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.field = field


class NotFoundError(AppError):
    """Raised when a resource is not found."""

    code = "NOT_FOUND"


class ValidationError(AppError):
    """Raised when validation fails."""

    code = "VALIDATION_ERROR"


class ProcessingError(AppError):
    """Raised when processing fails."""

    code = "PROCESSING_ERROR"
