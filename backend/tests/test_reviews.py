"""Tests for the reviews endpoint.

Covers:
  - 201 on first review
  - 409 on duplicate (uq_reviews_user_product)
  - 404 on unknown product
  - 422 on rating outside 1..5
  - Auth required (401 without token)
"""
import uuid

import pytest


async def _pick_product_id(client) -> str:
    r = await client.get("/api/products?per_page=1")
    items = r.json()["items"]
    assert items, "products table is empty -- did the seed run?"
    return items[0]["id"]


@pytest.mark.asyncio
async def test_create_review_returns_201(client, auth_headers):
    pid = await _pick_product_id(client)
    r = await client.post(
        "/api/reviews",
        json={"product_id": pid, "rating": 5, "comment": "Excellent."},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["product_id"] == pid
    assert body["rating"] == 5
    assert body["comment"] == "Excellent."


@pytest.mark.asyncio
async def test_duplicate_review_returns_409(client, auth_headers):
    """One user, one review per product -- second attempt is rejected."""
    pid = await _pick_product_id(client)
    first = await client.post(
        "/api/reviews",
        json={"product_id": pid, "rating": 4, "comment": "Good."},
        headers=auth_headers,
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        "/api/reviews",
        json={"product_id": pid, "rating": 3, "comment": "Changed my mind."},
        headers=auth_headers,
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_review_for_unknown_product_returns_404(client, auth_headers):
    r = await client.post(
        "/api/reviews",
        json={"product_id": str(uuid.uuid4()), "rating": 5},
        headers=auth_headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_invalid_rating_returns_422(client, auth_headers):
    pid = await _pick_product_id(client)
    too_high = await client.post(
        "/api/reviews",
        json={"product_id": pid, "rating": 6},
        headers=auth_headers,
    )
    assert too_high.status_code == 422

    too_low = await client.post(
        "/api/reviews",
        json={"product_id": pid, "rating": 0},
        headers=auth_headers,
    )
    assert too_low.status_code == 422


@pytest.mark.asyncio
async def test_review_requires_auth(client):
    pid = await _pick_product_id(client)
    r = await client.post("/api/reviews", json={"product_id": pid, "rating": 5})
    assert r.status_code == 401
