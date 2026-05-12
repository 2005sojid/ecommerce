import io
import uuid
import pytest

from app.routers import product_images as router_mod


class _DummyStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, str]] = []
        self.deletes: list[str] = []
        self._public = 'http://localhost:9000'
        self.bucket = 'product-images'

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        self.uploads.append((key, data, content_type))

    async def delete(self, key: str) -> None:
        self.deletes.append(key)

    def public_url(self, key: str) -> str:
        return f'{self._public}/{self.bucket}/{key}'

    def key_from_url(self, url: str) -> str | None:
        prefix = f'{self._public}/{self.bucket}/'
        if url.startswith(prefix):
            return url[len(prefix):]
        return None


@pytest.fixture
def fake_storage(monkeypatch):
    dummy = _DummyStorage()
    monkeypatch.setattr(router_mod, 'storage_service', dummy)
    return dummy


async def _create_product(client, admin_headers) -> str:
    # Need a real category id from seed data
    listing = (await client.get('/api/products?per_page=1')).json()
    assert listing['items'], 'seed required (make db-seed)'
    cat_id = listing['items'][0]['category_id']
    slug = f'img-test-{uuid.uuid4().hex[:8]}'
    payload = {
        'name': 'Image Test Product',
        'slug': slug,
        'price': '9.99',
        'category_id': cat_id,
        'initial_quantity': 1,
    }
    r = await client.post('/api/products', headers=admin_headers, json=payload)
    assert r.status_code == 201, r.text
    return r.json()['id']


@pytest.mark.asyncio
async def test_upload_image_succeeds(client, admin_headers, fake_storage):
    pid = await _create_product(client, admin_headers)
    files = {'file': ('test.png', io.BytesIO(b'\x89PNG\r\n\x1a\nfakepng'), 'image/png')}
    data = {'alt': 'a photo', 'position': '2'}
    r = await client.post(
        f'/api/products/{pid}/images',
        headers=admin_headers,
        files=files,
        data=data,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body['product_id'] == pid
    assert body['alt'] == 'a photo'
    assert body['position'] == 2
    assert body['url'].startswith('http://localhost:9000/product-images/')
    assert body['url'].endswith('.png')

    assert len(fake_storage.uploads) == 1
    key, data_bytes, ctype = fake_storage.uploads[0]
    assert key.startswith(f'{pid}/')
    assert key.endswith('.png')
    assert ctype == 'image/png'
    assert data_bytes == b'\x89PNG\r\n\x1a\nfakepng'

    # List should now include this image
    r2 = await client.get(f'/api/products/{pid}/images')
    assert r2.status_code == 200
    ids = [i['id'] for i in r2.json()]
    assert body['id'] in ids


@pytest.mark.asyncio
async def test_upload_rejects_bad_content_type(client, admin_headers, fake_storage):
    pid = await _create_product(client, admin_headers)
    files = {'file': ('evil.txt', io.BytesIO(b'hello'), 'text/plain')}
    r = await client.post(f'/api/products/{pid}/images', headers=admin_headers, files=files)
    assert r.status_code == 415
    assert fake_storage.uploads == []


@pytest.mark.asyncio
async def test_upload_rejects_too_large(client, admin_headers, fake_storage):
    pid = await _create_product(client, admin_headers)
    big = b'\x00' * (5 * 1024 * 1024 + 1)
    files = {'file': ('big.jpg', io.BytesIO(big), 'image/jpeg')}
    r = await client.post(f'/api/products/{pid}/images', headers=admin_headers, files=files)
    assert r.status_code == 413
    assert fake_storage.uploads == []


@pytest.mark.asyncio
async def test_upload_requires_auth(client, fake_storage):
    pid = '00000000-0000-0000-0000-000000000000'
    files = {'file': ('x.png', io.BytesIO(b'x'), 'image/png')}
    r = await client.post(f'/api/products/{pid}/images', files=files)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_delete_image_removes_row_and_storage(client, admin_headers, fake_storage):
    pid = await _create_product(client, admin_headers)
    files = {'file': ('a.webp', io.BytesIO(b'webpdata'), 'image/webp')}
    r = await client.post(f'/api/products/{pid}/images', headers=admin_headers, files=files)
    assert r.status_code == 201
    img_id = r.json()['id']

    r2 = await client.delete(f'/api/products/{pid}/images/{img_id}', headers=admin_headers)
    assert r2.status_code == 204
    assert len(fake_storage.deletes) == 1
    assert fake_storage.deletes[0].startswith(f'{pid}/')
    assert fake_storage.deletes[0].endswith('.webp')

    # No longer in listing
    r3 = await client.get(f'/api/products/{pid}/images')
    ids = [i['id'] for i in r3.json()]
    assert img_id not in ids


@pytest.mark.asyncio
async def test_delete_continues_when_storage_fails(client, admin_headers, fake_storage, monkeypatch):
    pid = await _create_product(client, admin_headers)
    files = {'file': ('a.gif', io.BytesIO(b'gif89a'), 'image/gif')}
    r = await client.post(f'/api/products/{pid}/images', headers=admin_headers, files=files)
    assert r.status_code == 201
    img_id = r.json()['id']

    async def boom(key):
        raise RuntimeError('minio down')

    monkeypatch.setattr(fake_storage, 'delete', boom)

    r2 = await client.delete(f'/api/products/{pid}/images/{img_id}', headers=admin_headers)
    assert r2.status_code == 204  # DB row still deleted even though storage failed

    r3 = await client.get(f'/api/products/{pid}/images')
    ids = [i['id'] for i in r3.json()]
    assert img_id not in ids
