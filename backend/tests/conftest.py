import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac

@pytest_asyncio.fixture
async def registered_user(client):
    email = f'test+{uuid.uuid4().hex[:10]}@example.com'
    payload = {'email': email, 'password': 'password123', 'name': 'Test User'}
    r = await client.post('/api/auth/register', json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    return {'email': email, 'password': payload['password'], 'user': data['user'], 'tokens': data['tokens']}

@pytest_asyncio.fixture
async def auth_headers(registered_user):
    return {'Authorization': f"Bearer {registered_user['tokens']['access_token']}"}

@pytest_asyncio.fixture
async def admin_headers(client):
    r = await client.post('/api/auth/login', json={'email': 'admin@example.com', 'password': 'admin123'})
    assert r.status_code == 200, r.text
    return {'Authorization': f"Bearer {r.json()['access_token']}"}
