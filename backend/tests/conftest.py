"""Shared pytest fixtures.

The tests are integration tests on top of live Postgres + Redis from docker compose:
  make up && make db-migrate && make db-seed && make test

ASGITransport does not invoke lifespan automatically -- workers / scheduler / event_bus
do not start during tests, which is what we want.
"""
import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped loop so the module-level async SQLAlchemy engine
    (created at import time and bound to the first loop it touches)
    stays valid across all tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client):
    """Creates a new customer with a unique email and returns (user, tokens)."""
    email = f"test+{uuid.uuid4().hex[:10]}@example.com"
    payload = {"email": email, "password": "password123", "name": "Test User"}
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    return {"email": email, "password": payload["password"], "user": data["user"], "tokens": data["tokens"]}


@pytest_asyncio.fixture
async def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['tokens']['access_token']}"}


@pytest_asyncio.fixture
async def admin_headers(client):
    """Logs in as the seeded admin (admin@example.com / admin123)."""
    r = await client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
