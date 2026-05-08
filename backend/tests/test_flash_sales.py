from datetime import datetime, timedelta, timezone
import pytest

def _sale_payload(product_id: str, *, stock: int=2, starts_in: int=-60, lasts: int=3600):
    now = datetime.now(timezone.utc)
    return {'product_id': product_id, 'sale_price': '9.99', 'original_price': '19.99', 'start_at': (now + timedelta(seconds=starts_in)).isoformat(), 'end_at': (now + timedelta(seconds=starts_in + lasts)).isoformat(), 'initial_stock': stock}

async def _pick_product_id(client) -> str:
    r = await client.get('/api/products?per_page=1')
    items = r.json()['items']
    assert items, 'products table is empty -- did the seed run?'
    return items[0]['id']

@pytest.mark.asyncio
async def test_create_flash_sale_requires_admin(client, auth_headers):
    pid = await _pick_product_id(client)
    r = await client.post('/api/flash-sales', json=_sale_payload(pid), headers=auth_headers)
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_admin_creates_active_sale_and_it_appears_in_active_list(client, admin_headers):
    pid = await _pick_product_id(client)
    r = await client.post('/api/flash-sales', json=_sale_payload(pid), headers=admin_headers)
    assert r.status_code == 201, r.text
    sale = r.json()
    assert sale['remaining_stock'] == 2
    assert sale['product_id'] == pid
    listing = (await client.get('/api/flash-sales/active')).json()
    assert any((s['id'] == sale['id'] for s in listing))

@pytest.mark.asyncio
async def test_claim_decrements_stock_and_creates_order(client, admin_headers, auth_headers):
    pid = await _pick_product_id(client)
    sale = (await client.post('/api/flash-sales', json=_sale_payload(pid, stock=2), headers=admin_headers)).json()
    r = await client.post(f"/api/flash-sales/{sale['id']}/claim", json={'shipping_address': '1 Test Street'}, headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['remaining_stock'] == 1
    assert body['sale_id'] == sale['id']
    assert body['order_id']

@pytest.mark.asyncio
async def test_claim_returns_409_when_sold_out(client, admin_headers, auth_headers, registered_user):
    pid = await _pick_product_id(client)
    sale = (await client.post('/api/flash-sales', json=_sale_payload(pid, stock=1), headers=admin_headers)).json()
    r1 = await client.post(f"/api/flash-sales/{sale['id']}/claim", json={'shipping_address': '1 Test Street'}, headers=auth_headers)
    assert r1.status_code == 200, r1.text
    assert r1.json()['remaining_stock'] == 0
    import uuid
    email = f'buyer+{uuid.uuid4().hex[:8]}@example.com'
    reg = await client.post('/api/auth/register', json={'email': email, 'password': 'password123', 'name': 'Buyer'})
    other = {'Authorization': f"Bearer {reg.json()['tokens']['access_token']}"}
    r2 = await client.post(f"/api/flash-sales/{sale['id']}/claim", json={'shipping_address': '2 Other Street'}, headers=other)
    assert r2.status_code == 409
    assert 'sold out' in r2.json()['detail'].lower()

@pytest.mark.asyncio
async def test_claim_returns_409_when_sale_not_running(client, admin_headers, auth_headers):
    pid = await _pick_product_id(client)
    future = (await client.post('/api/flash-sales', json=_sale_payload(pid, starts_in=3600, lasts=3600), headers=admin_headers)).json()
    r = await client.post(f"/api/flash-sales/{future['id']}/claim", json={'shipping_address': '1 Test Street'}, headers=auth_headers)
    assert r.status_code == 409
