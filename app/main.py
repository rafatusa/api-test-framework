"""API Test Framework — FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.routers import items, users, auth
from app.core.errors import register_error_handlers

app = FastAPI(
    title="API Test Framework",
    description=(
        "A reference FastAPI service with items, users, and JWT auth "
        "— built to exercise a full API test suite."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(items.router, prefix="/items", tags=["items"])

_LANDING = (Path(__file__).parent / "static" / "index.html").read_text()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return _LANDING


@app.get("/health", tags=["health"])
def health() -> dict:
    """Liveness probe — returns 200 when the service is up."""
    return {"status": "ok", "version": "1.0.0"}
