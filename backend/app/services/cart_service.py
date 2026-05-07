import uuid
from decimal import Decimal

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.cart import CartItemOut, CartOut

CART_TTL_SECONDS = 7 * 24 * 3600


def _key(user_id: uuid.UUID) -> str:
    return f"cart:{user_id}"


class CartService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get_raw(self, user_id: uuid.UUID) -> dict[str, int]:
        items = await self.redis.hgetall(_key(user_id))
        return {pid: int(qty) for pid, qty in items.items()}

    async def get_cart(self, user_id: uuid.UUID, db: AsyncSession) -> CartOut:
        raw = await self.get_raw(user_id)
        if not raw:
            return CartOut(items=[], total=Decimal("0"))

        product_ids = [uuid.UUID(pid) for pid in raw.keys()]
        rows = (
            await db.execute(select(Product).where(Product.id.in_(product_ids)))
        ).scalars().all()
        by_id = {p.id: p for p in rows}

        items: list[CartItemOut] = []
        total = Decimal("0")
        for pid_str, qty in raw.items():
            p = by_id.get(uuid.UUID(pid_str))
            if not p:
                continue
            line = p.price * qty
            total += line
            items.append(
                CartItemOut(
                    product_id=p.id,
                    name=p.name,
                    price=p.price,
                    quantity=qty,
                    line_total=line,
                )
            )
        return CartOut(items=items, total=total)

    async def add_item(self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> None:
        key = _key(user_id)
        await self.redis.hset(key, str(product_id), quantity)
        await self.redis.expire(key, CART_TTL_SECONDS)

    async def update_item(self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int) -> None:
        if quantity == 0:
            await self.remove_item(user_id, product_id)
            return
        await self.add_item(user_id, product_id, quantity)

    async def remove_item(self, user_id: uuid.UUID, product_id: uuid.UUID) -> None:
        await self.redis.hdel(_key(user_id), str(product_id))

    async def clear(self, user_id: uuid.UUID) -> None:
        await self.redis.delete(_key(user_id))
