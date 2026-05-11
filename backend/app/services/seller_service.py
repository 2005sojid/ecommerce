import re
import secrets
import uuid
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.seller import Seller
from app.models.user import User, UserRole
from app.schemas.seller import SellerCreate, SellerUpdate


def _slugify(text: str) -> str:
    text = (text or '').strip().lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text or 'store'


async def _unique_slug(db: AsyncSession, base: str) -> str:
    slug = base[:170] or 'store'
    existing = (await db.execute(select(Seller).where(Seller.slug == slug))).scalar_one_or_none()
    if existing is None:
        return slug
    for _ in range(5):
        candidate = f'{slug}-{secrets.token_hex(3)}'
        existing = (await db.execute(select(Seller).where(Seller.slug == candidate))).scalar_one_or_none()
        if existing is None:
            return candidate
    return f'{slug}-{secrets.token_hex(6)}'


async def register_seller(db: AsyncSession, user: User, payload: SellerCreate) -> Seller:
    existing = (await db.execute(select(Seller).where(Seller.user_id == user.id))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, 'Seller profile already exists')
    base_slug = _slugify(payload.slug or payload.store_name)
    slug = await _unique_slug(db, base_slug)
    seller = Seller(
        id=uuid.uuid4(),
        user_id=user.id,
        store_name=payload.store_name,
        slug=slug,
        description=payload.description,
        logo_url=payload.logo_url,
        banner_url=payload.banner_url,
        is_verified=False,
        is_active=True,
    )
    db.add(seller)
    db_user = await db.get(User, user.id)
    if db_user is not None:
        db_user.role = UserRole.seller
    await db.commit()
    await db.refresh(seller)
    return seller


async def get_by_slug(db: AsyncSession, slug: str) -> Seller | None:
    stmt = select(Seller).where(Seller.slug == slug)
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_profile(db: AsyncSession, seller: Seller, payload: SellerUpdate) -> Seller:
    changes = payload.model_dump(exclude_unset=True)
    if 'slug' in changes and changes['slug']:
        new_slug = _slugify(changes['slug'])
        if new_slug != seller.slug:
            existing = (await db.execute(select(Seller).where(Seller.slug == new_slug, Seller.id != seller.id))).scalar_one_or_none()
            if existing is not None:
                raise HTTPException(status.HTTP_409_CONFLICT, 'Slug already in use')
            changes['slug'] = new_slug
        else:
            changes.pop('slug')
    for k, v in changes.items():
        setattr(seller, k, v)
    await db.commit()
    await db.refresh(seller)
    return seller


async def list_seller_products(db: AsyncSession, seller_id: uuid.UUID, page: int, per_page: int) -> tuple[list[Product], int]:
    where = Product.seller_id == seller_id
    total = int((await db.execute(select(func.count()).select_from(Product).where(where))).scalar_one() or 0)
    rows = (await db.execute(
        select(Product).where(where).order_by(Product.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )).scalars().all()
    return list(rows), total


async def list_active_seller_products(db: AsyncSession, seller_id: uuid.UUID, page: int, per_page: int) -> tuple[list[Product], int]:
    where = (Product.seller_id == seller_id) & (Product.is_active.is_(True))
    total = int((await db.execute(select(func.count()).select_from(Product).where(where))).scalar_one() or 0)
    rows = (await db.execute(
        select(Product).where(where).order_by(Product.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )).scalars().all()
    return list(rows), total


async def seller_analytics(db: AsyncSession, seller_id: uuid.UUID) -> dict:
    revenue_stmt = select(func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0)).join(
        Product, Product.id == OrderItem.product_id
    ).where(Product.seller_id == seller_id)
    revenue_total = (await db.execute(revenue_stmt)).scalar_one() or 0

    orders_stmt = select(func.count(func.distinct(OrderItem.order_id))).join(
        Product, Product.id == OrderItem.product_id
    ).where(Product.seller_id == seller_id)
    orders_count = int((await db.execute(orders_stmt)).scalar_one() or 0)

    products_count = int((await db.execute(
        select(func.count()).select_from(Product).where(Product.seller_id == seller_id)
    )).scalar_one() or 0)

    top_stmt = select(
        Product.id, Product.name,
        func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0).label('revenue'),
        func.coalesce(func.sum(OrderItem.quantity), 0).label('units'),
    ).join(OrderItem, OrderItem.product_id == Product.id).where(
        Product.seller_id == seller_id
    ).group_by(Product.id, Product.name).order_by(func.sum(OrderItem.unit_price * OrderItem.quantity).desc()).limit(5)
    top_rows = (await db.execute(top_stmt)).all()
    top_products = [
        {
            'product_id': str(r[0]),
            'name': r[1],
            'revenue': float(r[2] or 0),
            'units_sold': int(r[3] or 0),
        }
        for r in top_rows
    ]
    return {
        'revenue_total': float(revenue_total or 0),
        'orders_count': orders_count,
        'products_count': products_count,
        'top_products': top_products,
    }


async def list_seller_orders(db: AsyncSession, seller_id: uuid.UUID, page: int, per_page: int) -> tuple[list[Order], int]:
    base = select(Order).join(OrderItem, OrderItem.order_id == Order.id).join(
        Product, Product.id == OrderItem.product_id
    ).where(Product.seller_id == seller_id).group_by(Order.id)
    total = int((await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one() or 0)
    rows = (await db.execute(
        base.order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )).scalars().all()
    return list(rows), total


async def create_seller_product(db: AsyncSession, seller: Seller, payload) -> Product:
    product = Product(
        id=uuid.uuid4(),
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        price=payload.price,
        category_id=payload.category_id,
        image_url=payload.image_url,
        is_active=payload.is_active,
        seller_id=seller.id,
    )
    db.add(product)
    qty = int(getattr(payload, 'initial_quantity', 0) or 0)
    db.add(Inventory(id=uuid.uuid4(), product_id=product.id, quantity=qty, reserved=0))
    sku = f'SKU-{str(product.id).replace("-", "")}'
    db.add(ProductVariant(
        id=uuid.uuid4(),
        product_id=product.id,
        sku=sku,
        variant_name='Default',
        attributes=None,
        price=Decimal(str(payload.price)),
        stock_quantity=qty,
        reserved_quantity=0,
        is_active=True,
    ))
    await db.commit()
    await db.refresh(product)
    return product
