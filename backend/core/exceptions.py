"""
backend/core/exceptions.py
Custom HTTP exception classes and FastAPI exception handlers.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class LISSClearException(Exception):
    """Base exception for LISSclear API."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ModelNotLoadedException(LISSClearException):
    def __init__(self):
        super().__init__(
            message="Model not loaded. Check checkpoint path in config.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class InvalidFileFormatException(LISSClearException):
    def __init__(self, filename: str, accepted: list):
        super().__init__(
            message=f"Invalid file format for '{filename}'. Accepted: {accepted}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class FileTooLargeException(LISSClearException):
    def __init__(self, size_mb: float, max_mb: int):
        super().__init__(
            message=f"File too large: {size_mb:.1f}MB. Maximum: {max_mb}MB",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class InferenceFailedException(LISSClearException):
    def __init__(self, detail: str):
        super().__init__(
            message=f"Inference failed: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers with the FastAPI app."""

    @app.exception_handler(LISSClearException)
    async def lissclear_exception_handler(
        request: Request, exc: LISSClearException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": type(exc).__name__,
                "message": exc.message,
                "path": str(request.url),
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Please try again.",
                "path": str(request.url),
            },
        )
