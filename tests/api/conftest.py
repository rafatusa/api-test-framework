"""
Shared fixtures for the API test suite.

When running locally:   pytest tests/api/ --base-url=http://localhost:8000
When running in CI:     base_url is set via --base-url CLI arg OR API_BASE_URL env var.

The conftest also spins up a TestClient for pure-unit API runs (no live server needed)
when --base-url is not provided (defaults to the ASGI test client).
"""
import os
from typing import Generator

import pytest
import requests
from fastapi.testclient import TestClient

from app.main import app as fastapi_app


# ── pytest CLI option ──────────────────────────────────────────────────────────


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help=(
            "Base URL of the deployed API (e.g. http://1.2.3.4). "
            "Falls back to API_BASE_URL env var, then TestClient."
        ),
    )


# ── Base URL fixture ───────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def base_url(request) -> str:
    url = (
        request.config.getoption("--base-url")
        or os.environ.get("API_BASE_URL")
        or "testclient"
    )
    return url.rstrip("/")


# ── HTTP client fixtures ───────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def client(base_url) -> Generator:
    """
    Returns a requests.Session (live server) or a FastAPI TestClient.
    All test functions call client.get/post/etc. uniformly.
    """
    if base_url == "testclient":
        with TestClient(fastapi_app) as tc:
            yield tc
    else:
        session = requests.Session()
        session.base_url = base_url  # type: ignore[attr-defined]

        original_get = session.get
        original_post = session.post
        original_patch = session.patch
        original_delete = session.delete

        def _get(path, **kw):
            return original_get(base_url + path, **kw)

        def _post(path, **kw):
            return original_post(base_url + path, **kw)

        def _patch(path, **kw):
            return original_patch(base_url + path, **kw)

        def _delete(path, **kw):
            return original_delete(base_url + path, **kw)

        session.get = _get  # type: ignore[method-assign]
        session.post = _post  # type: ignore[method-assign]
        session.patch = _patch  # type: ignore[method-assign]
        session.delete = _delete  # type: ignore[method-assign]

        yield session


# ── Auth token fixtures ────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def alice_token(client) -> str:
    resp = client.post(
        "/auth/token",
        json={"username": "alice", "password": "alicepassword123"},
    )
    assert resp.status_code == 200, f"Alice login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def bob_token(client) -> str:
    resp = client.post(
        "/auth/token",
        json={"username": "bob", "password": "bobpassword456"},
    )
    assert resp.status_code == 200, f"Bob login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def alice_headers(alice_token) -> dict:
    return {"Authorization": f"Bearer {alice_token}"}


@pytest.fixture(scope="session")
def bob_headers(bob_token) -> dict:
    return {"Authorization": f"Bearer {bob_token}"}
