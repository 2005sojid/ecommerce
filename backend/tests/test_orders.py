"""Smoke tests for cart + checkout + orders. Require `make db-seed` to have been run."""
import pytest


@pytest.mark.asyncio
async def test_cart_lifecycle(client, auth_headers):
    listing = (await client.get("/api/products?per_page=1")).json()
    assert listing["items"], "seed required"
    pid = listing["items"][0]["id"]

    # 1. Add
    r = await client.post(
        "/api/cart/items", headers=auth_headers, json={"product_id": pid, "quantity": 1}
    )
    assert r.status_code == 201
    cart = r.json()
    assert any(it["product_id"] == pid for it in cart["items"])

    # 2. Change quantity
    r = await client.patch(
        f"/api/cart/items/{pid}", headers=auth_headers, json={"quantity": 3}
    )
    assert r.status_code == 200
    found = next(it for it in r.json()["items"] if it["product_id"] == pid)
    assert found["quantity"] == 3

    # 3. Remove
    r = await client.delete(f"/api/cart/items/{pid}", headers=auth_headers)
    assert r.status_code == 200
    assert all(it["product_id"] != pid for it in r.json()["items"])


@pytest.mark.asyncio
async def test_checkout_empty_cart_returns_400(client, auth_headers):
    r = await client.post(
        "/api/orders", headers=auth_headers, json={"shipping_address": "Some street 1"}
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_full_checkout_flow(client, auth_headers):
    # pick a product with confirmed stock
    listing = (await client.get("/api/products?per_page=10")).json()
    pid = None
    for item in listing["items"]:
        d = (await client.get(f"/api/products/{item['id']}")).json()
        if d.get("available_quantity", 0) >= 1:
            pid = item["id"]
            break
    assert pid, "no product with stock -- re-seed"

    await client.post(
        "/api/cart/items", headers=auth_headers, json={"product_id": pid, "quantity": 1}
    )
    r = await client.post(
        "/api/orders", headers=auth_headers, json={"shipping_address": "Test addr 1"}
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["status"] == "pending"
    assert any(it["product_id"] == pid for it in order["items"])
    assert order["events"][0]["to_status"] == "pending"

    # The order is visible in the user's own list
    r = await client.get("/api/orders", headers=auth_headers)
    assert r.status_code == 200
    assert any(o["id"] == order["id"] for o in r.json()["items"])

    # And via the detail endpoint
    r = await client.get(f"/api/orders/{order['id']}", headers=auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_other_user_cannot_see_order(client, auth_headers):
    """Authorization for order detail: only owner or admin."""
    listing = (await client.get("/api/products?per_page=10")).json()
    pid = None
    for item in listing["items"]:
        detail = (await client.get(f"/api/products/{item['id']}")).json()
        if detail.get("available_quantity", 0) >= 1:
            pid = item["id"]
            break
    assert pid

    await client.post(
        "/api/cart/items", headers=auth_headers, json={"product_id": pid, "quantity": 1}
    )
    r = await client.post(
        "/api/orders", headers=auth_headers, json={"shipping_address": "1 Test Street"}
    )
    assert r.status_code == 201, r.text
    order = r.json()

    # Register a second user
    import uuid
    email = f"other+{uuid.uuid4().hex[:8]}@example.com"
    r = await client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "name": "Other"},
    )
    other_headers = {"Authorization": f"Bearer {r.json()['tokens']['access_token']}"}

    r = await client.get(f"/api/orders/{order['id']}", headers=other_headers)
    assert r.status_code == 403
