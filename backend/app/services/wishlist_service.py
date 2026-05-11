import uuid
from fastapi import HTTPException, status
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
from app.models.wishlist import Wishlist


async def add(db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID) -> Wishlist:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    item = Wishlist(id=uuid.uuid4(), user_id=user_id, product_id=product_id)
    db.add(item)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id))
        if existing is None:
            raise HTTPException(status.HTTP_409_CONFLICT, 'Could not add to wishlist')
        return existing
    await db.refresh(item)
    return item


async def remove(db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID) -> bool:
    result = await db.execute(delete(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id))
    await db.commit()
    return (result.rowcount or 0) > 0


async def list_for_user(db: AsyncSession, user_id: uuid.UUID, page: int, per_page: int) -> tuple[list[dict], int]:
    total = await db.scalar(select(func.count(Wishlist.id)).where(Wishlist.user_id == user_id)) or 0
    offset = (page - 1) * per_page
    stmt = select(Wishlist, Product).join(Product, Product.id == Wishlist.product_id).where(Wishlist.user_id == user_id).order_by(Wishlist.created_at.desc()).limit(per_page).offset(offset)
    rows = (await db.execute(stmt)).all()
    items = [{'id': w.id, 'product_id': w.product_id, 'product_name': p.name, 'product_price': p.price, 'product_image_url': p.image_url, 'created_at': w.created_at} for w, p in rows]
    return items, int(total)


async def list_ids(db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    result = await db.execute(select(Wishlist.product_id).where(Wishlist.user_id == user_id))
    return [row[0] for row in result.all()]
