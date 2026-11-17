"""Test harness.

Environment variables are set *before* importing the app so the settings object and the
SQLAlchemy engine point at a throwaway SQLite database instead of ./app.db.
"""

from __future__ import annotations

import os
import pathlib

_DB_DIR = pathlib.Path(__file__).resolve().parent / "_artifacts"
_DB_DIR.mkdir(exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{(_DB_DIR / 'test.db').as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"

from collections.abc import Callable, Iterator  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402

DEFAULT_USER: dict[str, Any] = {
    "email": "driver@example.com",
    "password": "SuperSecret123",
    "full_name": "Jan Kowalski",
    "age": 34,
    "country": "PL",
    "city": "Warsaw",
}


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    """Give every test a clean database."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def register(client: TestClient) -> Callable[..., dict[str, Any]]:
    """Register a user and return {'headers', 'token', 'user', 'credentials'}."""

    def _register(**overrides: Any) -> dict[str, Any]:
        payload = {**DEFAULT_USER, **overrides}
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201, response.text
        body = response.json()
        token = body["access_token"]
        return {
            "headers": {"Authorization": f"Bearer {token}"},
            "token": token,
            "user": body["user"],
            "credentials": {"email": payload["email"], "password": payload["password"]},
        }

    return _register


@pytest.fixture
def driver(register: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    """A logged-in default user."""
    return register()
