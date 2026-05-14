import uuid
from datetime import datetime, timezone
import redis.asyncio as redis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.metrics import flash_sale_claims, order_status_transitions, orders_created
from app.models.flash_sale import FlashSale
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, OrderStatus
from app.models.order_event import OrderEvent
from app.routers.ws import broadcast_inventory_change
from app.services.notification_service import publish_event
from app.services.order_service import generate_order_id

def stock_key(sale_id: uuid.UUID) -> str:
    return f'flash:{sale_id}:stock'

class FlashSaleService:

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def preload_stock(self, sale: FlashSale) -> None:
        await self.redis.set(stock_key(sale.id), sale.remaining_stock)

    async def _atomic_decrement(self, key: str, sql_remaining: int) -> int:
        """Decrement the Redis counter by 1.

        If the key is missing (e.g., the Redis cache was wiped while the SQL
        row still tracks `remaining_stock`), seed it from SQL atomically via a
        Lua script so the very first claim after a Redis flap doesn't return
        "sold out" for a sale that still has stock in the database.
        Returns the new counter value (-1 if truly sold out)."""
        script = """
        if redis.call('EXISTS', KEYS[1]) == 0 then
            redis.call('SET', KEYS[1], ARGV[1])
        end
        return redis.call('DECRBY', KEYS[1], 1)
        """
        result = await self.redis.eval(script, 1, key, sql_remaining)
        return int(result)

    async def claim(self, sale_id: uuid.UUID, user_id: uuid.UUID, shipping_address: str, db: AsyncSession) -> tuple[Order, int]:
        sale = await db.get(FlashSale, sale_id)
        if sale is None or not sale.is_active:
            raise HTTPException(status.HTTP_404_NOT_FOUND, 'Flash sale not found or inactive')
        now = datetime.now(timezone.utc)
        if not sale.start_at <= now <= sale.end_at:
            raise HTTPException(status.HTTP_409_CONFLICT, 'Flash sale is not running')
        key = stock_key(sale_id)
        remaining = await self._atomic_decrement(key, sale.remaining_stock)
        if remaining < 0:
            await self.redis.incrby(key, 1)
            flash_sale_claims.labels(status='sold_out').inc()
            raise HTTPException(status.HTTP_409_CONFLICT, 'Flash sale sold out')
        inv = (await db.execute(
            select(Inventory).where(Inventory.product_id == sale.product_id).with_for_update()
        )).scalar_one_or_none()
        if inv is None or inv.quantity - inv.reserved < 1:
            await self.redis.incrby(key, 1)
            flash_sale_claims.labels(status='sold_out').inc()
            raise HTTPException(status.HTTP_409_CONFLICT, 'Out of stock')
        inv.quantity -= 1
        order = Order(id=generate_order_id(), user_id=user_id, status=OrderStatus.pending, total_amount=sale.sale_price, shipping_address=shipping_address)
        order.items = [OrderItem(id=uuid.uuid4(), product_id=sale.product_id, quantity=1, unit_price=sale.sale_price)]
        db.add(order)
        db.add(OrderEvent(id=uuid.uuid4(), order_id=order.id, from_status=None, to_status=OrderStatus.pending.value, event_metadata={'source': 'flash_sale', 'sale_id': str(sale_id)}))
        sale.remaining_stock = remaining
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            # Restore the Redis counter — we already decremented it but the SQL claim failed.
            await self.redis.incrby(key, 1)
            flash_sale_claims.labels(status='error').inc()
            raise
        await db.refresh(order)
        await publish_event('order.created', {'order_id': order.id, 'source': 'flash_sale', 'sale_id': str(sale_id)})
        await broadcast_inventory_change(sale.product_id, remaining, source='flash_sale')
        flash_sale_claims.labels(status='success').inc()
        orders_created.inc()
        order_status_transitions.labels(from_status='none', to_status='pending').inc()
        return (order, remaining)
