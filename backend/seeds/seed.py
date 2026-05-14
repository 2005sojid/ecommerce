import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from passlib.context import CryptContext
from sqlalchemy import text
from app.cache.redis_cache import redis_client
from app.database import async_session, engine
from app.from_scratch.snowflake_id import next_id
from app.services.search_service import search_service
from app.models import Category, Product, Inventory, User, UserRole, Order, OrderItem, OrderEvent, OrderStatus, Review, FlashSale, ProductVariant, Seller, Address, Coupon, Return, Conversation, Message, Settlement, Wishlist
from app.models.notification import Notification
from app.models.product_image import ProductImage
from app.services.flash_sale_service import stock_key
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

def slugify(s: str) -> str:
    return ''.join((c.lower() if c.isalnum() else '-' for c in s)).strip('-')

PRODUCT_IMAGE_LIBRARY: dict[str, dict[str, object]] = {
    'Wireless Headphones X200': {
        'primary': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&q=80',
            'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=800&q=80',
            'https://images.unsplash.com/photo-1577174881658-0f30ed549adc?w=800&q=80',
        ],
    },
    'Smartphone Pulse 5': {
        'primary': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&q=80',
            'https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=800&q=80',
            'https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?w=800&q=80',
        ],
    },
    'Laptop ProBook 14': {
        'primary': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=800&q=80',
            'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&q=80',
            'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80',
        ],
    },
    '4K Action Camera': {
        'primary': 'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1525385133512-2f3bdd039054?w=800&q=80',
            'https://images.unsplash.com/photo-1623126908029-58cb08a2b272?w=800&q=80',
            'https://images.unsplash.com/photo-1473876988266-ca0860a443b8?w=800&q=80',
        ],
    },
    'Bluetooth Speaker Mini': {
        'primary': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1543512214-318c7553f230?w=800&q=80',
            'https://images.unsplash.com/photo-1589003077984-894e133dabab?w=800&q=80',
            'https://images.unsplash.com/photo-1545454675-3531b543be5d?w=800&q=80',
        ],
    },
    'Smartwatch Aero': {
        'primary': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=800&q=80',
            'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=800&q=80',
            'https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=800&q=80',
        ],
    },
    'USB-C Hub 7-in-1': {
        'primary': 'https://images.unsplash.com/photo-1625948515291-69613efd103f?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=800&q=80',
            'https://images.unsplash.com/photo-1601524909162-ae8725290836?w=800&q=80',
            'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=800&q=80',
        ],
    },
    "Men's Cotton T-Shirt": {
        'primary': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=800&q=80',
            'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&q=80',
            'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800&q=80',
        ],
    },
    "Women's Denim Jacket": {
        'primary': 'https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=800&q=80',
            'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&q=80',
            'https://images.unsplash.com/photo-1542272604-787c3835535d?w=800&q=80',
        ],
    },
    'Running Shoes Velocity': {
        'primary': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1539185441755-769473a23570?w=800&q=80',
            'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=800&q=80',
            'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=800&q=80',
        ],
    },
    'Wool Beanie': {
        'primary': 'https://images.unsplash.com/photo-1576871337632-b9aef4c17ab9?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1521369909029-2afed882baee?w=800&q=80',
            'https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=800&q=80',
            'https://images.unsplash.com/photo-1604644401890-0bd678c83788?w=800&q=80',
        ],
    },
    'Leather Belt Classic': {
        'primary': 'https://images.unsplash.com/photo-1624222247344-550fb60583dc?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&q=80',
            'https://images.unsplash.com/photo-1606760227091-3dd870d97f1d?w=800&q=80',
            'https://images.unsplash.com/photo-1605733513597-a8f8341084e6?w=800&q=80',
        ],
    },
    'Hooded Sweatshirt': {
        'primary': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=800&q=80',
            'https://images.unsplash.com/photo-1578768079052-aa76e52ff62e?w=800&q=80',
            'https://images.unsplash.com/photo-1620799139507-2a76f79a2f4d?w=800&q=80',
        ],
    },
    'Stainless Steel Frying Pan': {
        'primary': 'https://images.unsplash.com/photo-1581873372796-635b67ca2008?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1574781330855-d0db8cc6a79c?w=800&q=80',
            'https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=800&q=80',
            'https://images.unsplash.com/photo-1593618998160-e34014e67546?w=800&q=80',
        ],
    },
    'Espresso Maker Brio': {
        'primary': 'https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1611854779393-1b2da9d400fe?w=800&q=80',
            'https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=800&q=80',
            'https://images.unsplash.com/photo-1610557892470-55d9e80c0bce?w=800&q=80',
        ],
    },
    'Cordless Vacuum Cleaner': {
        'primary': 'https://images.unsplash.com/photo-1558317374-067fb5f30001?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800&q=80',
            'https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?w=800&q=80',
            'https://images.unsplash.com/photo-1610557892470-55d9e80c0bce?w=800&q=80',
        ],
    },
    'LED Desk Lamp': {
        'primary': 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1534126511673-b6899657816a?w=800&q=80',
            'https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=800&q=80',
            'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800&q=80',
        ],
    },
    'Knife Set 6-piece': {
        'primary': 'https://images.unsplash.com/photo-1567521464027-f127ff144326?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=800&q=80',
            'https://images.unsplash.com/photo-1566454544259-f4b94c3d758c?w=800&q=80',
            'https://images.unsplash.com/photo-1593618998160-e34014e67546?w=800&q=80',
        ],
    },
    'Cotton Bed Sheet Set': {
        'primary': 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1631049552057-403cdb8f0658?w=800&q=80',
            'https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800&q=80',
            'https://images.unsplash.com/photo-1631679706909-1844bbd07221?w=800&q=80',
        ],
    },
    'Yoga Mat Pro': {
        'primary': 'https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1592432678016-e910b452f9a2?w=800&q=80',
            'https://images.unsplash.com/photo-1593810450967-f9c42742e326?w=800&q=80',
            'https://images.unsplash.com/photo-1599447421416-3414500d18a5?w=800&q=80',
        ],
    },
    'Adjustable Dumbbells 20kg': {
        'primary': 'https://images.unsplash.com/photo-1638536532686-d610adfc8e5c?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800&q=80',
            'https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=800&q=80',
            'https://images.unsplash.com/photo-1517344884509-a0c97ec11bcc?w=800&q=80',
        ],
    },
    'Mountain Bike Helmet': {
        'primary': 'https://images.unsplash.com/photo-1571333250630-f0230c320b6d?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1505705694340-019e1e335916?w=800&q=80',
            'https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=800&q=80',
            'https://images.unsplash.com/photo-1559348349-86f1f65817fe?w=800&q=80',
        ],
    },
    'Resistance Bands Set': {
        'primary': 'https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1652363722833-509b3aac287b?w=800&q=80',
            'https://images.unsplash.com/photo-1620188467120-5042ed1eb5da?w=800&q=80',
            'https://images.unsplash.com/photo-1591741535018-d042766c62eb?w=800&q=80',
        ],
    },
    'Football Size 5': {
        'primary': 'https://images.unsplash.com/photo-1614632537190-23e4146777db?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1551958219-acbc608c6377?w=800&q=80',
            'https://images.unsplash.com/photo-1486286701208-1d58e9338013?w=800&q=80',
            'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=800&q=80',
        ],
    },
    'Designing Data-Intensive Applications': {
        'primary': 'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=800&q=80',
            'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=800&q=80',
            'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=800&q=80',
        ],
    },
    'Clean Code': {
        'primary': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1519682337058-a94d519337bc?w=800&q=80',
            'https://images.unsplash.com/photo-1535905557558-afc4877a26fc?w=800&q=80',
            'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=800&q=80',
        ],
    },
    'The Pragmatic Programmer': {
        'primary': 'https://images.unsplash.com/photo-1518744386442-2d48ac47a7eb?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800&q=80',
            'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&q=80',
            'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800&q=80',
        ],
    },
    'System Design Interview Vol. 1': {
        'primary': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1532012197267-da84d127e765?w=800&q=80',
            'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=800&q=80',
            'https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=800&q=80',
        ],
    },
    'Atomic Habits': {
        'primary': 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800&q=80',
            'https://images.unsplash.com/photo-1519682337058-a94d519337bc?w=800&q=80',
            'https://images.unsplash.com/photo-1535905557558-afc4877a26fc?w=800&q=80',
        ],
    },
    'Deep Work': {
        'primary': 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=800&q=80',
        'gallery': [
            'https://images.unsplash.com/photo-1518744386442-2d48ac47a7eb?w=800&q=80',
            'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800&q=80',
            'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&q=80',
        ],
    },
}


def _img(keyword: str, lock: int, size: str = '600/450') -> str:
    w, h = size.split('/')
    kw = keyword.replace(' ', ',')
    return f'https://loremflickr.com/{w}/{h}/{kw}?lock={lock}'


def _primary_image(name: str, keyword: str, lock: int) -> str:
    entry = PRODUCT_IMAGE_LIBRARY.get(name)
    if entry:
        return entry['primary']  # type: ignore[return-value]
    return _img(keyword, lock=lock)


def _gallery_images(name: str, keyword: str, lock_base: int) -> list[str]:
    entry = PRODUCT_IMAGE_LIBRARY.get(name)
    if entry:
        return list(entry['gallery'])  # type: ignore[arg-type]
    return [_img(keyword, lock=lock_base + pos, size='800/600') for pos in range(3)]

def gen_order_id() -> str:
    return f'ORD-{next_id():X}'
CATEGORIES = ['Electronics', 'Clothing', 'Home & Kitchen', 'Sports', 'Books']
PRODUCTS_BY_CAT = {
    'Electronics': [
        ('Wireless Headphones X200', 'Noise-cancelling over-ear headphones, 30h battery', '129.99', 'headphones'),
        ('Smartphone Pulse 5', '6.5" OLED, 128GB, dual camera', '499.00', 'smartphone'),
        ('Laptop ProBook 14', 'Intel i7, 16GB RAM, 512GB SSD', '1199.00', 'laptop'),
        ('4K Action Camera', 'Waterproof, image stabilization', '249.50', 'action,camera'),
        ('Bluetooth Speaker Mini', 'Portable, 12h battery, IPX7', '59.90', 'bluetooth,speaker'),
        ('Smartwatch Aero', 'Heart-rate, GPS, 7-day battery', '199.00', 'smartwatch'),
        ('USB-C Hub 7-in-1', 'HDMI, SD, 100W PD passthrough', '39.99', 'usb,hub'),
    ],
    'Clothing': [
        ("Men's Cotton T-Shirt", 'Soft 100% cotton, regular fit', '19.99', 't-shirt'),
        ("Women's Denim Jacket", 'Classic mid-blue wash', '79.00', 'denim,jacket'),
        ('Running Shoes Velocity', 'Lightweight mesh upper', '89.99', 'running,shoes'),
        ('Wool Beanie', 'Warm winter beanie, one size', '14.50', 'beanie,hat'),
        ('Leather Belt Classic', 'Genuine leather, brass buckle', '34.99', 'leather,belt'),
        ('Hooded Sweatshirt', 'Fleece-lined, kangaroo pocket', '44.90', 'hoodie'),
    ],
    'Home & Kitchen': [
        ('Stainless Steel Frying Pan', 'Non-stick, induction-ready', '49.00', 'frying,pan'),
        ('Espresso Maker Brio', '15-bar pump, milk frother', '189.00', 'espresso,machine'),
        ('Cordless Vacuum Cleaner', 'Cyclone tech, 45min runtime', '229.00', 'vacuum,cleaner'),
        ('LED Desk Lamp', 'Dimmable, USB charging port', '32.99', 'desk,lamp'),
        ('Knife Set 6-piece', 'German steel, wooden block', '69.50', 'kitchen,knife'),
        ('Cotton Bed Sheet Set', 'Queen size, 300 thread count', '54.00', 'bed,sheets'),
    ],
    'Sports': [
        ('Yoga Mat Pro', '6mm thick, anti-slip', '29.99', 'yoga,mat'),
        ('Adjustable Dumbbells 20kg', 'Quick-change weight system', '159.00', 'dumbbells'),
        ('Mountain Bike Helmet', 'MIPS protection, ventilated', '84.00', 'bike,helmet'),
        ('Resistance Bands Set', '5 levels, door anchor included', '21.50', 'resistance,bands'),
        ('Football Size 5', 'FIFA quality, hand-stitched', '27.99', 'football,soccer,ball'),
    ],
    'Books': [
        ('Designing Data-Intensive Applications', 'Martin Kleppmann', '42.00', 'book,programming'),
        ('Clean Code', 'Robert C. Martin', '31.50', 'book,code'),
        ('The Pragmatic Programmer', 'Hunt & Thomas, 20th anniv. ed.', '37.00', 'book,software'),
        ('System Design Interview Vol. 1', 'Alex Xu', '29.99', 'book,system'),
        ('Atomic Habits', 'James Clear', '18.50', 'book,habits'),
        ('Deep Work', 'Cal Newport', '16.99', 'book,focus'),
    ],
}

async def truncate_all(conn) -> None:
    await conn.execute(text('TRUNCATE TABLE messages, conversations, returns, coupon_usages, coupons, notifications, wishlists, product_variants, product_images, order_events, order_items, orders, reviews, flash_sales, settlements, inventory, addresses, products, sellers, categories, users RESTART IDENTITY CASCADE'))

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
        product_keywords: dict[uuid.UUID, str] = {}
        product_idx = 0
        for (cat_name, items) in PRODUCTS_BY_CAT.items():
            for (name, desc, price, keyword) in items:
                product_idx += 1
                slug = slugify(name)
                p = Product(
                    id=uuid.uuid4(),
                    name=name,
                    slug=slug,
                    description=desc,
                    price=Decimal(price),
                    category_id=cats[cat_name].id,
                    image_url=_primary_image(name, keyword, lock=product_idx),
                    is_active=True,
                )
                db.add(p)
                products.append(p)
                product_keywords[p.id] = keyword
        await db.flush()
        for i, p in enumerate(products, start=1):
            qty = random.randint(10, 500)
            db.add(Inventory(id=uuid.uuid4(), product_id=p.id, quantity=qty, reserved=0, warehouse_location=random.choice(['WH-A', 'WH-B', 'WH-C'])))
            kw = product_keywords[p.id]
            gallery_urls = _gallery_images(p.name, kw, lock_base=i * 10)
            for pos, url in enumerate(gallery_urls):
                db.add(ProductImage(
                    id=uuid.uuid4(),
                    product_id=p.id,
                    url=url,
                    alt=f'{p.name} – view {pos + 1}',
                    position=pos,
                ))
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
        for u in users:
            db.add(Address(id=uuid.uuid4(), user_id=u.id, label='Home', recipient_name=u.name, line1=f'{random.randint(1, 120)} {random.choice(home_streets)}', line2=f'Apt {random.randint(1, 90)}', city='Tashkent', state='Tashkent', postal_code=random.choice(tashkent_postal), country='UZ', phone=_uz_phone(), is_default=True))
            if random.random() < 0.5:
                db.add(Address(id=uuid.uuid4(), user_id=u.id, label='Office', recipient_name=u.name, line1=f'{random.randint(1, 60)} {random.choice(office_streets)}', line2=f'Floor {random.randint(2, 12)}', city='Tashkent', state='Tashkent', postal_code=random.choice(tashkent_postal), country='UZ', phone=None, is_default=False))
        coupons_spec = [('WELCOME10', 'percent', Decimal('10'), 'platform', None, 100), ('SAVE5', 'fixed', Decimal('5.00'), 'platform', Decimal('25.00'), 500), ('MEGA20', 'percent', Decimal('20'), 'seller', sellers[0].id, 50)]
        for code, dtype, dvalue, scope, min_or_seller, max_uses in coupons_spec:
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
        shipped_order_id: str | None = None
        shipped_order_user_id: uuid.UUID | None = None
        for n in range(7):
            if n == 0:
                user = users[0]
                final_status = OrderStatus.delivered
            elif n == 1:
                user = users[0]
                final_status = OrderStatus.shipped
            else:
                user = random.choice(users)
                final_status = random.choice(statuses_pipeline)
            chosen = random.sample(products, k=random.randint(1, 3))
            items_data = [(p, random.randint(1, 3)) for p in chosen]
            total = sum((p.price * qty for (p, qty) in items_data))
            uz_cities = [('Tashkent', 'Tashkent', '100000'), ('Samarkand', 'Samarqand', '140100'), ('Bukhara', 'Bukhoro', '200100'), ('Andijan', 'Andijon', '170100'), ('Namangan', 'Namangan', '160100'), ('Fergana', 'Fargona', '150100')]
            uz_streets = ['Amir Temur Avenue', 'Mustaqillik Street', 'Navoi Street', 'Bobur Street', 'Ibn Sino Street', 'Furqat Street']
            city_name, region, postal = random.choice(uz_cities)
            shipping = f'{random.choice(customer_names)}, {random.randint(1, 200)} {random.choice(uz_streets)}, Apt {random.randint(1, 90)}, {city_name}, {region} region, {postal}, Uzbekistan, Tel: +998{random.choice(uz_operator_codes)}{random.randint(1000000, 9999999)}'
            order = Order(id=gen_order_id(), user_id=user.id, status=final_status, total_amount=total, shipping_address=shipping)
            db.add(order)
            await db.flush()
            if n == 0:
                delivered_order_id = order.id
                delivered_order_user_id = user.id
            elif n == 1:
                shipped_order_id = order.id
                shipped_order_user_id = user.id
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
            db.add(Review(id=uuid.uuid4(), user_id=u.id, product_id=p.id, rating=random.randint(2, 5), comment=random.choice(['Great!', 'Solid quality.', 'Recommended.', 'As described.', None])))
        for _ in range(20):
            u = random.choice(users)
            p = random.choice(products)
            if (u.id, p.id) not in seen_pairs:
                seen_pairs.add((u.id, p.id))
                db.add(Review(id=uuid.uuid4(), user_id=u.id, product_id=p.id, rating=2, comment='Looked nothing like the photos — needs moderation.', is_approved=False))
                break
        await db.flush()
        now_dt = datetime.now(timezone.utc)
        flash_specs = [(random.choice(products), -timedelta(minutes=10), timedelta(hours=6), 100), (random.choice(products), -timedelta(minutes=30), timedelta(hours=2), 50), (random.choice(products), -timedelta(minutes=5), timedelta(hours=4), 200)]
        flash_sales: list[FlashSale] = []
        for (product, start_offset, duration, stock) in flash_specs:
            sale = FlashSale(id=uuid.uuid4(), product_id=product.id, sale_price=product.price * Decimal('0.5'), original_price=product.price, start_at=now_dt + start_offset, end_at=now_dt + start_offset + duration, initial_stock=stock, remaining_stock=stock, is_active=True)
            db.add(sale)
            flash_sales.append(sale)
        if delivered_order_id is not None and delivered_order_user_id is not None:
            db.add(Return(id=uuid.uuid4(), order_id=delivered_order_id, user_id=delivered_order_user_id, status='pending', reason='Item arrived with a minor scratch.', refund_amount=None, admin_note=None))
        if shipped_order_id is not None and shipped_order_user_id is not None:
            db.add(Return(id=uuid.uuid4(), order_id=shipped_order_id, user_id=shipped_order_user_id, status='approved', reason='Wrong size, exchange requested.', refund_amount=Decimal('15.00'), admin_note='Approved — refund queued.'))
        wishlist_products = random.sample(products, k=min(3, len(products)))
        for wp in wishlist_products:
            db.add(Wishlist(id=uuid.uuid4(), user_id=users[0].id, product_id=wp.id))
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        db.add(Settlement(id=uuid.uuid4(), seller_id=sellers[0].id, settlement_date=yesterday, gross_revenue=Decimal('250.00'), fees=Decimal('12.50'), net_payout=Decimal('237.50'), order_count=3))
        db.add(Settlement(id=uuid.uuid4(), seller_id=sellers[1].id, settlement_date=yesterday, gross_revenue=Decimal('180.00'), fees=Decimal('9.00'), net_payout=Decimal('171.00'), order_count=2))
        conv = Conversation(id=uuid.uuid4(), buyer_id=users[0].id, seller_id=sellers[0].id)
        db.add(conv)
        await db.flush()
        msg_ts = now - timedelta(hours=2)
        db.add(Message(id=uuid.uuid4(), conversation_id=conv.id, sender_user_id=users[0].id, body='Hi, is this still in stock?', is_read=True, created_at=msg_ts))
        db.add(Message(id=uuid.uuid4(), conversation_id=conv.id, sender_user_id=sellers[0].user_id, body='Yes, plenty in stock. Free shipping over $50.', is_read=True, created_at=msg_ts + timedelta(minutes=12)))
        db.add(Message(id=uuid.uuid4(), conversation_id=conv.id, sender_user_id=users[0].id, body='Great, ordering now!', is_read=False, created_at=msg_ts + timedelta(minutes=20)))
        if users:
            demo_user = users[0]
            notif_specs = [
                ('order_status', 'Welcome to ShopSphere!', 'Browse fresh arrivals from verified sellers.', '/products', False, timedelta(minutes=5)),
                ('promo', 'Flash sale ending soon', 'Up to 50% off — claim before stock runs out.', '/flash-sales', False, timedelta(hours=1)),
            ]
            if delivered_order_id is not None and delivered_order_user_id == demo_user.id:
                notif_specs.append(('order_status', f'Order {delivered_order_id} delivered', 'Leave a review and earn loyalty points.', f'/orders/{delivered_order_id}', True, timedelta(hours=6)))
            for type_, title, body, link, is_read, ago in notif_specs:
                db.add(Notification(id=uuid.uuid4(), user_id=demo_user.id, type=type_, title=title, body=body, link=link, is_read=is_read, created_at=now - ago))
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
