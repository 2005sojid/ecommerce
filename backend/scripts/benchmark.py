import asyncio
import os
import statistics
import time
from typing import Any
import httpx
from sqlalchemy import text
from app.cache.redis_cache import redis_client
from app.database import async_session, engine
API_BASE = os.environ.get('BENCH_API_BASE', 'http://localhost')
QUERIES = {
    'list products in category': "SELECT * FROM products WHERE category_id = (SELECT id FROM categories LIMIT 1) AND is_active = true ORDER BY created_at DESC LIMIT 20",
    'get product detail': "SELECT p.*, i.quantity, i.reserved FROM products p LEFT JOIN inventory i ON i.product_id = p.id LIMIT 1",
    'user orders sorted': "SELECT * FROM orders WHERE user_id = (SELECT id FROM users LIMIT 1) ORDER BY created_at DESC LIMIT 20",
    'order events by order': "SELECT * FROM order_events WHERE order_id = (SELECT id FROM orders LIMIT 1) ORDER BY timestamp DESC",
    'reviews for product': "SELECT * FROM reviews WHERE product_id = (SELECT id FROM products LIMIT 1) ORDER BY created_at DESC LIMIT 20",
}
INDEX_DEFS: list[tuple[str, str]] = [
    ('ix_products_category_id', 'CREATE INDEX IF NOT EXISTS ix_products_category_id ON products(category_id)'),
    ('ix_products_active_price', 'CREATE INDEX IF NOT EXISTS ix_products_active_price ON products(is_active, price)'),
    ('ix_orders_user_created', 'CREATE INDEX IF NOT EXISTS ix_orders_user_created ON orders(user_id, created_at)'),
    ('ix_order_events_order_ts', 'CREATE INDEX IF NOT EXISTS ix_order_events_order_ts ON order_events(order_id, timestamp)'),
    ('ix_reviews_product_id', 'CREATE INDEX IF NOT EXISTS ix_reviews_product_id ON reviews(product_id)'),
]

async def explain_analyze(sql: str) -> float:
    async with async_session() as db:
        rows = (await db.execute(text(f'EXPLAIN (ANALYZE, FORMAT JSON) {sql}'))).all()
        plan = rows[0][0][0]
        return float(plan['Execution Time'])

async def drop_indexes() -> None:
    async with engine.begin() as conn:
        for name, _ in INDEX_DEFS:
            await conn.execute(text(f'DROP INDEX IF EXISTS {name}'))

async def recreate_indexes() -> None:
    async with engine.begin() as conn:
        for _, ddl in INDEX_DEFS:
            await conn.execute(text(ddl))

async def measure_endpoint(client: httpx.AsyncClient, url: str, runs: int=5) -> float:
    times: list[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        r = await client.get(url)
        r.raise_for_status()
        times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)

async def main() -> None:
    print('== EXPLAIN ANALYZE: without indexes ==')
    await drop_indexes()
    no_index: dict[str, float] = {}
    for (label, sql) in QUERIES.items():
        no_index[label] = await explain_analyze(sql)
        print(f'  {label:<35} {no_index[label]:>8.3f} ms')
    print('\n== EXPLAIN ANALYZE: with indexes ==')
    await recreate_indexes()
    with_index: dict[str, float] = {}
    for (label, sql) in QUERIES.items():
        with_index[label] = await explain_analyze(sql)
        print(f'  {label:<35} {with_index[label]:>8.3f} ms')
    print('\n== API: without / with cache (median of 5 runs) ==')
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f'{API_BASE}/api/products?per_page=1')
        r.raise_for_status()
        product_id = r.json()['items'][0]['id']
        url = f'{API_BASE}/api/products/{product_id}'
        await redis_client.delete(f'product:{product_id}', f'product:{product_id}:avg_rating')
        cold = await measure_endpoint(client, url)
        warm = await measure_endpoint(client, url)
        await redis_client.delete('categories:tree')
        cat_cold = await measure_endpoint(client, f'{API_BASE}/api/categories')
        cat_warm = await measure_endpoint(client, f'{API_BASE}/api/categories')
    print(f'  GET /products/{{id}}     cold={cold:7.2f} ms   warm={warm:7.2f} ms')
    print(f'  GET /categories         cold={cat_cold:7.2f} ms   warm={cat_warm:7.2f} ms')
    print('\n== Markdown table for the report ==')
    print('| Query | No Index | With Index |')
    print('|---|---|---|')
    for label in QUERIES:
        print(f'| {label} | {no_index[label]:.2f} ms | {with_index[label]:.2f} ms |')
    print()
    print('| Endpoint | Cold | Warm (cache) |')
    print('|---|---|---|')
    print(f'| GET /products/{{id}} | {cold:.2f} ms | {warm:.2f} ms |')
    print(f'| GET /categories | {cat_cold:.2f} ms | {cat_warm:.2f} ms |')
    await engine.dispose()
    await redis_client.aclose()
if __name__ == '__main__':
    asyncio.run(main())
