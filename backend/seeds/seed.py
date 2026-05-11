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
from app.models import Category, Product, Inventory, User, UserRole, Order, OrderItem, OrderEvent, OrderStatus, Review, FlashSale, ProductVariant, Seller, Address, Coupon, Return, Conversation, Message
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
    await conn.execute(text('TRUNCATE TABLE messages, conversations, returns, coupon_usages, coupons, notifications, wishlists, product_variants, order_events, order_items, orders, reviews, flash_sales, inventory, addresses, products, sellers, categories, users RESTART IDENTITY CASCADE'))

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
            qty = random.randint(10, 500)
            db.add(Inventory(id=uuid.uuid4(), product_id=p.id, quantity=qty, reserved=0, warehouse_location=random.choice(['WH-A', 'WH-B', 'WH-C'])))
            db.add(ProductVariant(id=uuid.uuid4(), product_id=p.id, sku=f'SKU-{str(p.id).replace("-", "")}', variant_name='Default', attributes=None, price=p.price, stock_quantity=qty, reserved_quantity=0, is_active=True))
        customer_names = ['Aziz Karimov', 'Dilshod Yusupov', 'Malika Tashkentova', 'Bobur Aliyev']
        users: list[User] = []
        for i, full_name in enumerate(customer_names, start=1):
            u = User(id=uuid.uuid4(), email=f'customer{i}@example.com', password_hash=pwd.hash('password123'), name=full_name, role=UserRole.customer, is_active=True)
            db.add(u)
            users.append(u)
        admin = User(id=uuid.uuid4(), email='admin@example.com', password_hash=pwd.hash('admin123'), name='Site Admin', role=UserRole.admin, is_active=True)
        db.add(admin)
        seller_users = []
        for spec in [('seller1@example.com', 'Rustam Nazarov', 'Tashkent Tech Bazaar', 'tashkent-tech-bazaar', 'Curated electronics and gadgets, shipping nationwide from Tashkent.'), ('seller2@example.com', 'Gulnora Salimova', 'Silk Road Home', 'silk-road-home', 'Quality home and kitchen essentials inspired by Uzbek tradition.')]:
            email, name, store_name, store_slug, desc = spec
            su = User(id=uuid.uuid4(), email=email, password_hash=pwd.hash('seller123'), name=name, role=UserRole.seller, is_active=True)
            db.add(su)
            seller_users.append((su, store_name, store_slug, desc))
        await db.flush()
        sellers: list[Seller] = []
        for su, store_name, store_slug, desc in seller_users:
            s = Seller(id=uuid.uuid4(), user_id=su.id, store_name=store_name, slug=store_slug, description=desc, logo_url=None, banner_url=None, is_verified=True, is_active=True)
            db.add(s)
            sellers.append(s)
        await db.flush()
        for idx, p in enumerate(products):
            p.seller_id = sellers[idx % len(sellers)].id
        size_variants = [('Small', '0.95'), ('Medium', '1.00'), ('Large', '1.15')]
        for p in random.sample(products, k=min(3, len(products))):
            base_qty = random.randint(20, 100)
            for variant_name, price_mult in size_variants:
                db.add(ProductVariant(id=uuid.uuid4(), product_id=p.id, sku=f'SKU-{str(p.id).replace("-", "")[:16]}-{variant_name[0]}', variant_name=variant_name, attributes={'size': variant_name}, price=(p.price * Decimal(price_mult)).quantize(Decimal('0.01')), stock_quantity=base_qty, reserved_quantity=0, is_active=True))
        uz_operator_codes = ['90', '91', '93', '94', '97', '98', '99']
        def _uz_phone() -> str:
            return f'+998{random.choice(uz_operator_codes)}{random.randint(1000000, 9999999)}'
        home_streets = ['Amir Temur Avenue', 'Mustaqillik Street', 'Shota Rustaveli Street', 'Navoi Street', 'Bobur Street']
        office_streets = ['Buyuk Ipak Yuli Street', 'Mirzo Ulugbek Avenue', 'Afrosiab Street', 'Yunusabad Avenue']
        tashkent_postal = ['100000', '100007', '100011', '100015', '100047', '100100']
        for u in users[:2]:
            db.add(Address(id=uuid.uuid4(), user_id=u.id, label='Home', recipient_name=u.name, line1=f'{random.randint(1, 120)} {random.choice(home_streets)}', line2=f'Apt {random.randint(1, 90)}', city='Tashkent', state='Tashkent', postal_code=random.choice(tashkent_postal), country='UZ', phone=_uz_phone(), is_default=True))
            if random.random() < 0.5:
                db.add(Address(id=uuid.uuid4(), user_id=u.id, label='Office', recipient_name=u.name, line1=f'{random.randint(1, 60)} {random.choice(office_streets)}', line2=f'Floor {random.randint(2, 12)}', city='Tashkent', state='Tashkent', postal_code=random.choice(tashkent_postal), country='UZ', phone=None, is_default=False))
        coupons_spec = [('WELCOME10', 'percent', Decimal('10'), 'platform', None, None, 100), ('SAVE5', 'fixed', Decimal('5.00'), 'platform', Decimal('25.00'), 200, 500), ('MEGA20', 'percent', Decimal('20'), 'seller', sellers[0].id, None, 50)]
        for code, dtype, dvalue, scope, min_or_seller, min_amt, max_uses in coupons_spec:
            if scope == 'seller':
                seller_id_val = min_or_seller
                min_order_val = None
            else:
                seller_id_val = None
                min_order_val = min_or_seller if isinstance(min_or_seller, Decimal) else None
            db.add(Coupon(id=uuid.uuid4(), code=code, discount_type=dtype, discount_value=dvalue, scope=scope, seller_id=seller_id_val, min_order_amount=min_order_val, max_uses=max_uses, used_count=0, valid_from=None, valid_to=datetime.now(timezone.utc) + timedelta(days=60), is_active=True))
        await db.flush()
        statuses_pipeline = [OrderStatus.pending, OrderStatus.confirmed, OrderStatus.processing, OrderStatus.packed, OrderStatus.shipped, OrderStatus.delivered]
        now = datetime.now(timezone.utc)
        delivered_order_id: str | None = None
        delivered_order_user_id: uuid.UUID | None = None
        for n in range(7):
            user = random.choice(users)
            chosen = random.sample(products, k=random.randint(1, 3))
            items_data = [(p, random.randint(1, 3)) for p in chosen]
            total = sum((p.price * qty for (p, qty) in items_data))
            final_status = OrderStatus.delivered if n == 0 else random.choice(statuses_pipeline)
            uz_cities = [('Tashkent', 'Tashkent', '100000'), ('Samarkand', 'Samarqand', '140100'), ('Bukhara', 'Bukhoro', '200100'), ('Andijan', 'Andijon', '170100'), ('Namangan', 'Namangan', '160100'), ('Fergana', 'Fargona', '150100')]
            uz_streets = ['Amir Temur Avenue', 'Mustaqillik Street', 'Navoi Street', 'Bobur Street', 'Ibn Sino Street', 'Furqat Street']
            city_name, region, postal = random.choice(uz_cities)
            shipping = f'{random.choice(customer_names + [u.name for u in [admin]])}, {random.randint(1, 200)} {random.choice(uz_streets)}, Apt {random.randint(1, 90)}, {city_name}, {region} region, {postal}, Uzbekistan, Tel: +998{random.choice(uz_operator_codes)}{random.randint(1000000, 9999999)}'
            order = Order(id=gen_order_id(), user_id=user.id, status=final_status, total_amount=total, shipping_address=shipping)
            db.add(order)
            await db.flush()
            if n == 0:
                delivered_order_id = order.id
                delivered_order_user_id = user.id
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
        if delivered_order_id is not None and delivered_order_user_id is not None:
            db.add(Return(id=uuid.uuid4(), order_id=delivered_order_id, user_id=delivered_order_user_id, status='pending', reason='Item arrived with a minor scratch.', refund_amount=None, admin_note=None))
        conv = Conversation(id=uuid.uuid4(), buyer_id=users[0].id, seller_id=sellers[0].id)
        db.add(conv)
        await db.flush()
        msg_ts = now - timedelta(hours=2)
        db.add(Message(id=uuid.uuid4(), conversation_id=conv.id, sender_user_id=users[0].id, body='Hi, is this still in stock?', is_read=True, created_at=msg_ts))
        db.add(Message(id=uuid.uuid4(), conversation_id=conv.id, sender_user_id=sellers[0].user_id, body='Yes, plenty in stock. Free shipping over $50.', is_read=True, created_at=msg_ts + timedelta(minutes=12)))
        db.add(Message(id=uuid.uuid4(), conversation_id=conv.id, sender_user_id=users[0].id, body='Great, ordering now!', is_read=False, created_at=msg_ts + timedelta(minutes=20)))
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
