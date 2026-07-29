"""Centralised error handlers for consistent JSON error responses."""
import json

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _safe_errors(exc: RequestValidationError) -> list:
    """Convert Pydantic v2 validation errors to a JSON-safe list."""
    try:
        raw = exc.errors()
        # Pydantic v2 errors may contain non-serialisable objects (e.g. PydanticUndefined)
        # Round-trip through JSON with a default converter to catch them.
        json.dumps(raw, default=str)
        return raw
    except Exception:
        return [{"msg": str(e) for e in exc.errors()}]


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        try:
            body_repr = str(exc.body)
        except Exception:
            body_repr = "<unserializable>"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": _safe_errors(exc), "body": body_repr},
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Resource not found"},
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
