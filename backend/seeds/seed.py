import asyncio
import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from passlib.context import CryptContext
from sqlalchemy import text
from app.cache.redis_cache import redis_client
from app.database import async_session, engine
from app.services.search_service import search_service
from app.models import Category, Product, Inventory, User, UserRole, Order, OrderItem, OrderEvent, OrderStatus, Review, FlashSale
from app.services.flash_sale_service import stock_key
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

def slugify(s: str) -> str:
    return ''.join((c.lower() if c.isalnum() else '-' for c in s)).strip('-')

def gen_order_id() -> str:
    ts = datetime.now(timezone.utc).strftime('%y%m%d')
    rnd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f'ORD{ts}{rnd}'[:20]
CATEGORIES = ['Electronics', 'Clothing', 'Home & Kitchen', 'Sports', 'Books']
PRODUCTS_BY_CAT = {'Electronics': [('Wireless Headphones X200', 'Noise-cancelling over-ear headphones, 30h battery', '129.99'), ('Smartphone Pulse 5', '6.5" OLED, 128GB, dual camera', '499.00'), ('Laptop ProBook 14', 'Intel i7, 16GB RAM, 512GB SSD', '1199.00'), ('4K Action Camera', 'Waterproof, image stabilization', '249.50'), ('Bluetooth Speaker Mini', 'Portable, 12h battery, IPX7', '59.90'), ('Smartwatch Aero', 'Heart-rate, GPS, 7-day battery', '199.00'), ('USB-C Hub 7-in-1', 'HDMI, SD, 100W PD passthrough', '39.99')], 'Clothing': [("Men's Cotton T-Shirt", 'Soft 100% cotton, regular fit', '19.99'), ("Women's Denim Jacket", 'Classic mid-blue wash', '79.00'), ('Running Shoes Velocity', 'Lightweight mesh upper', '89.99'), ('Wool Beanie', 'Warm winter beanie, one size', '14.50'), ('Leather Belt Classic', 'Genuine leather, brass buckle', '34.99'), ('Hooded Sweatshirt', 'Fleece-lined, kangaroo pocket', '44.90')], 'Home & Kitchen': [('Stainless Steel Frying Pan', 'Non-stick, induction-ready', '49.00'), ('Espresso Maker Brio', '15-bar pump, milk frother', '189.00'), ('Cordless Vacuum Cleaner', 'Cyclone tech, 45min runtime', '229.00'), ('LED Desk Lamp', 'Dimmable, USB charging port', '32.99'), ('Knife Set 6-piece', 'German steel, wooden block', '69.50'), ('Cotton Bed Sheet Set', 'Queen size, 300 thread count', '54.00')], 'Sports': [('Yoga Mat Pro', '6mm thick, anti-slip', '29.99'), ('Adjustable Dumbbells 20kg', 'Quick-change weight system', '159.00'), ('Mountain Bike Helmet', 'MIPS protection, ventilated', '84.00'), ('Resistance Bands Set', '5 levels, door anchor included', '21.50'), ('Football Size 5', 'FIFA quality, hand-stitched', '27.99')], 'Books': [('Designing Data-Intensive Applications', 'Martin Kleppmann', '42.00'), ('Clean Code', 'Robert C. Martin', '31.50'), ('The Pragmatic Programmer', 'Hunt & Thomas, 20th anniv. ed.', '37.00'), ('System Design Interview Vol. 1', 'Alex Xu', '29.99'), ('Atomic Habits', 'James Clear', '18.50'), ('Deep Work', 'Cal Newport', '16.99')]}

async def truncate_all(conn) -> None:
    await conn.execute(text('TRUNCATE TABLE order_events, order_items, orders, reviews, flash_sales, inventory, products, categories, users RESTART IDENTITY CASCADE'))

async def seed(force: bool=False) -> None:
    async with engine.begin() as conn:
        existing = (await conn.execute(text('SELECT COUNT(*) FROM products'))).scalar_one()
        if existing and (not force):
            print(f'Seed skipped: {existing} products already present (pass --force to wipe).')
            await engine.dispose()
            return
        await truncate_all(conn)
    async with async_session() as db:
        cats: dict[str, Category] = {}
        for name in CATEGORIES:
            c = Category(id=uuid.uuid4(), name=name, slug=slugify(name))
            db.add(c)
            cats[name] = c
        await db.flush()
        products: list[Product] = []
        for (cat_name, items) in PRODUCTS_BY_CAT.items():
            for (name, desc, price) in items:
                p = Product(id=uuid.uuid4(), name=name, slug=slugify(name), description=desc, price=Decimal(price), category_id=cats[cat_name].id, is_active=True)
                db.add(p)
                products.append(p)
        await db.flush()
        for p in products:
            db.add(Inventory(id=uuid.uuid4(), product_id=p.id, quantity=random.randint(10, 500), reserved=0, warehouse_location=random.choice(['WH-A', 'WH-B', 'WH-C'])))
        users: list[User] = []
        for i in range(1, 5):
            u = User(id=uuid.uuid4(), email=f'customer{i}@example.com', password_hash=pwd.hash('password123'), name=f'Customer {i}', role=UserRole.customer, is_active=True)
            db.add(u)
            users.append(u)
        admin = User(id=uuid.uuid4(), email='admin@example.com', password_hash=pwd.hash('admin123'), name='Site Admin', role=UserRole.admin, is_active=True)
        db.add(admin)
        await db.flush()
        statuses_pipeline = [OrderStatus.pending, OrderStatus.confirmed, OrderStatus.processing, OrderStatus.packed, OrderStatus.shipped, OrderStatus.delivered]
        now = datetime.now(timezone.utc)
        for n in range(7):
            user = random.choice(users)
            chosen = random.sample(products, k=random.randint(1, 3))
            items_data = [(p, random.randint(1, 3)) for p in chosen]
            total = sum((p.price * qty for (p, qty) in items_data))
            final_status = random.choice(statuses_pipeline)
            order = Order(id=gen_order_id(), user_id=user.id, status=final_status, total_amount=total, shipping_address=f'{random.randint(1, 200)} Sample Street, City, 100{n:02d}')
            db.add(order)
            await db.flush()
            for (p, qty) in items_data:
                db.add(OrderItem(id=uuid.uuid4(), order_id=order.id, product_id=p.id, quantity=qty, unit_price=p.price))
            prev = None
            ts = now - timedelta(days=random.randint(1, 30))
            for st in statuses_pipeline:
                db.add(OrderEvent(id=uuid.uuid4(), order_id=order.id, from_status=prev, to_status=st.value, event_metadata={'source': 'seed'}, timestamp=ts))
                prev = st.value
                ts += timedelta(hours=random.randint(1, 12))
                if st == final_status:
                    break
        seen_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
        attempts = 0
        while len(seen_pairs) < 8 and attempts < 50:
            attempts += 1
            u = random.choice(users)
            p = random.choice(products)
            if (u.id, p.id) in seen_pairs:
                continue
            seen_pairs.add((u.id, p.id))
            db.add(Review(id=uuid.uuid4(), user_id=u.id, product_id=p.id, rating=random.randint(3, 5), comment=random.choice(['Great!', 'Solid quality.', 'Recommended.', 'As described.', None])))
        await db.flush()
        now_dt = datetime.now(timezone.utc)
        flash_specs = [(random.choice(products), -timedelta(minutes=10), timedelta(hours=6), 100), (random.choice(products), -timedelta(minutes=30), timedelta(hours=2), 50), (random.choice(products), timedelta(hours=1), timedelta(hours=4), 200)]
        flash_sales: list[FlashSale] = []
        for (product, start_offset, duration, stock) in flash_specs:
            sale = FlashSale(id=uuid.uuid4(), product_id=product.id, sale_price=product.price * Decimal('0.5'), original_price=product.price, start_at=now_dt + start_offset, end_at=now_dt + start_offset + duration, initial_stock=stock, remaining_stock=stock, is_active=True)
            db.add(sale)
            flash_sales.append(sale)
        await db.commit()
        for sale in flash_sales:
            await redis_client.set(stock_key(sale.id), sale.remaining_stock)
        try:
            await search_service.init_index()
            indexed = await search_service.reindex_all(db)
            print(f'Indexed {indexed} products into Meilisearch.')
        except Exception as exc:
            print(f'Meilisearch reindex skipped: {exc}')
    await redis_client.aclose()
    await search_service.close()
    await engine.dispose()
    print('Seed complete.')
if __name__ == '__main__':
    import sys
    asyncio.run(seed(force='--force' in sys.argv))
