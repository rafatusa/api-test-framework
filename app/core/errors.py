"""Centralised error handlers for consistent JSON error responses."""
import json

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _safe_errors(exc: RequestValidationError) -> list:
    """Convert Pydantic v2 validation errors to a JSON-safe list.

    Pydantic v2 error objects can contain non-serialisable types such as
    PydanticUndefined in the 'input' field.  We round-trip through json.dumps
    with default=str to coerce every value to a primitive, then parse back so
    the response body stays a proper list-of-dicts rather than a raw string.
    """
    try:
        # include_url=False drops the pydantic docs URL (not needed in API responses)
        raw = exc.errors(include_url=False)
    except TypeError:
        # older pydantic / passlib shim that doesn't accept include_url
        try:
            raw = exc.errors()
        except Exception:
            return [{"msg": str(exc)}]

    try:
        serialised = json.dumps(raw, default=str)
        return json.loads(serialised)
    except Exception:
        # absolute last resort — turn each error into a plain string dict
        result = []
        for e in raw:
            try:
                result.append({"msg": str(e)})
            except Exception:
                result.append({"msg": "validation error"})
        return result


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
