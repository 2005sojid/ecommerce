import uuid
import pytest

@pytest.mark.asyncio
async def test_register_returns_user_and_tokens(client):
    email = f'test+{uuid.uuid4().hex[:10]}@example.com'
    r = await client.post('/api/auth/register', json={'email': email, 'password': 'password123', 'name': 'Alice'})
    assert r.status_code == 201
    body = r.json()
    assert body['user']['email'] == email
    assert body['user']['role'] == 'customer'
    assert body['tokens']['access_token']
    assert body['tokens']['refresh_token']

@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client, registered_user):
    r = await client.post('/api/auth/register', json={'email': registered_user['email'], 'password': 'password123', 'name': 'Dup'})
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_login_with_correct_credentials(client, registered_user):
    r = await client.post('/api/auth/login', json={'email': registered_user['email'], 'password': registered_user['password']})
    assert r.status_code == 200
    assert r.json()['access_token']

@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client, registered_user):
    r = await client.post('/api/auth/login', json={'email': registered_user['email'], 'password': 'wrong-password'})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_me_returns_profile(client, auth_headers, registered_user):
    r = await client.get('/api/auth/me', headers=auth_headers)
    assert r.status_code == 200
    assert r.json()['email'] == registered_user['email']

@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    r = await client.get('/api/auth/me')
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_refresh_returns_new_pair(client, registered_user):
    r = await client.post('/api/auth/refresh', json={'refresh_token': registered_user['tokens']['refresh_token']})
    assert r.status_code == 200
    body = r.json()
    assert body['access_token'] and body['refresh_token']
