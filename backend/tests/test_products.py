"""Smoke tests for products endpoints. Require `make db-seed` to have been run."""
import pytest


@pytest.mark.asyncio
async def test_list_products_returns_paginated_response(client):
    r = await client.get("/api/products?page=1&per_page=5")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
    assert body["page"] == 1
    assert body["per_page"] == 5
    assert len(body["items"]) <= 5


@pytest.mark.asyncio
async def test_list_products_with_price_filter(client):
    r = await client.get("/api/products?min_price=10&max_price=50&per_page=20")
    assert r.status_code == 200
    for item in r.json()["items"]:
        price = float(item["price"])
        assert 10 <= price <= 50


@pytest.mark.asyncio
async def test_get_product_detail(client):
    listing = (await client.get("/api/products?per_page=1")).json()
    assert listing["items"], "seed required (make db-seed)"
    pid = listing["items"][0]["id"]

    r = await client.get(f"/api/products/{pid}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == pid
    assert "available_quantity" in body
    assert "average_rating" in body
    assert "reviews_count" in body


@pytest.mark.asyncio
async def test_get_product_returns_404_for_unknown_id(client):
    r = await client.get("/api/products/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_product_requires_admin(client, auth_headers):
    """A customer cannot create a product."""
    r = await client.post(
        "/api/products",
        headers=auth_headers,
        json={
            "name": "X", "slug": "x-slug", "price": "1.00",
            "category_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_search_returns_results_or_falls_back(client):
    """If Meilisearch is unavailable -- fallback to SQL ILIKE; in any case 200."""
    r = await client.get("/api/products?search=wireless")
    assert r.status_code == 200
