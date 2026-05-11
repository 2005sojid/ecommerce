import uuid
from decimal import Decimal
import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.schemas.cart import CartItemOut, CartOut
CART_TTL_SECONDS = 30 * 24 * 3600

def _key(user_id: uuid.UUID) -> str:
    return f'cart:{user_id}'

def _field(product_id: uuid.UUID, variant_id: uuid.UUID | None) -> str:
    if variant_id is not None:
        return f'{product_id}:{variant_id}'
    return f'{product_id}:'

def _parse_field(field: str) -> tuple[uuid.UUID, uuid.UUID | None]:
    if ':' in field:
        pid_str, vid_str = field.split(':', 1)
    else:
        pid_str, vid_str = field, ''
    pid = uuid.UUID(pid_str)
    vid = uuid.UUID(vid_str) if vid_str else None
    return pid, vid

class CartService:

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get_raw(self, user_id: uuid.UUID) -> dict[str, int]:
        items = await self.redis.hgetall(_key(user_id))
        return {field: int(qty) for (field, qty) in items.items()}

    async def get_cart(self, user_id: uuid.UUID, db: AsyncSession) -> CartOut:
        raw = await self.get_raw(user_id)
        if not raw:
            return CartOut(items=[], total=Decimal('0'))
        parsed: list[tuple[str, uuid.UUID, uuid.UUID | None, int]] = []
        product_ids: set[uuid.UUID] = set()
        variant_ids: set[uuid.UUID] = set()
        for field, qty in raw.items():
            try:
                pid, vid = _parse_field(field)
            except (ValueError, TypeError):
                continue
            parsed.append((field, pid, vid, qty))
            product_ids.add(pid)
            if vid is not None:
                variant_ids.add(vid)
        products_by_id: dict[uuid.UUID, Product] = {}
        if product_ids:
            rows = (await db.execute(select(Product).where(Product.id.in_(product_ids)))).scalars().all()
            products_by_id = {p.id: p for p in rows}
        variants_by_id: dict[uuid.UUID, ProductVariant] = {}
        if variant_ids:
            vrows = (await db.execute(select(ProductVariant).where(ProductVariant.id.in_(variant_ids)))).scalars().all()
            variants_by_id = {v.id: v for v in vrows}
        items: list[CartItemOut] = []
        total = Decimal('0')
        for (_field_str, pid, vid, qty) in parsed:
            p = products_by_id.get(pid)
            if not p:
                continue
            variant: ProductVariant | None = None
            if vid is not None:
                variant = variants_by_id.get(vid)
                if variant is None:
                    continue
            unit_price = variant.price if variant is not None else p.price
            line = unit_price * qty
            total += line
            items.append(CartItemOut(
                product_id=p.id,
                name=p.name,
                price=unit_price,
                quantity=qty,
                line_total=line,
                variant_id=variant.id if variant is not None else None,
                variant_name=variant.variant_name if variant is not None else None,
                variant_sku=variant.sku if variant is not None else None,
            ))
        return CartOut(items=items, total=total)

    async def add_item(self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int, variant_id: uuid.UUID | None = None) -> None:
        key = _key(user_id)
        await self.redis.hset(key, _field(product_id, variant_id), quantity)
        await self.redis.expire(key, CART_TTL_SECONDS)

    async def update_item(self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int, variant_id: uuid.UUID | None = None) -> None:
        if quantity == 0:
            await self.remove_item(user_id, product_id, variant_id)
            return
        await self.add_item(user_id, product_id, quantity, variant_id)

    async def remove_item(self, user_id: uuid.UUID, product_id: uuid.UUID, variant_id: uuid.UUID | None = None) -> None:
        await self.redis.hdel(_key(user_id), _field(product_id, variant_id))

    async def clear(self, user_id: uuid.UUID) -> None:
        await self.redis.delete(_key(user_id))
