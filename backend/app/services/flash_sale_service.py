import uuid
from datetime import datetime, timezone
import redis.asyncio as redis
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.metrics import flash_sale_claims
from app.models.flash_sale import FlashSale
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

    async def claim(self, sale_id: uuid.UUID, user_id: uuid.UUID, shipping_address: str, db: AsyncSession) -> tuple[Order, int]:
        sale = await db.get(FlashSale, sale_id)
        if sale is None or not sale.is_active:
            raise HTTPException(status.HTTP_404_NOT_FOUND, 'Flash sale not found or inactive')
        now = datetime.now(timezone.utc)
        if not sale.start_at <= now <= sale.end_at:
            raise HTTPException(status.HTTP_409_CONFLICT, 'Flash sale is not running')
        key = stock_key(sale_id)
        remaining = await self.redis.decrby(key, 1)
        if remaining < 0:
            await self.redis.incrby(key, 1)
            flash_sale_claims.labels(status='sold_out').inc()
            raise HTTPException(status.HTTP_409_CONFLICT, 'Flash sale sold out')
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
        return (order, remaining)
