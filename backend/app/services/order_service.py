import random
import string
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.metrics import checkout_duration, order_status_transitions, orders_created
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, OrderStatus
from app.models.order_event import OrderEvent
from app.models.product import Product
from app.routers.ws import broadcast_inventory_change, broadcast_order_status
from app.services.cart_service import CartService
from app.services.notification_service import publish_event

def generate_order_id() -> str:
    ts = datetime.now(timezone.utc).strftime('%y%m%d')
    rnd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f'ORD{ts}{rnd}'[:20]

class OrderService:

    def __init__(self, cart_service: CartService):
        self.cart_service = cart_service

    async def checkout(self, user_id: uuid.UUID, shipping_address: str, db: AsyncSession) -> Order:
        t0 = time.perf_counter()
        cart_items = await self.cart_service.get_raw(user_id)
        if not cart_items:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Cart is empty')
        total = Decimal('0')
        order_items: list[OrderItem] = []
        stock_changes: list[tuple[uuid.UUID, int]] = []
        for (product_id_str, quantity) in cart_items.items():
            product_id = uuid.UUID(product_id_str)
            qty = int(quantity)
            inventory = (await db.execute(select(Inventory).where(Inventory.product_id == product_id).with_for_update())).scalar_one_or_none()
            if inventory is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f'Inventory not found for product {product_id}')
            if inventory.quantity - inventory.reserved < qty:
                raise HTTPException(status.HTTP_409_CONFLICT, f'Insufficient stock for product {product_id}')
            inventory.quantity -= qty
            stock_changes.append((product_id, inventory.quantity))
            product = await db.get(Product, product_id)
            if product is None or not product.is_active:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f'Product {product_id} unavailable')
            line_total = product.price * qty
            total += line_total
            order_items.append(OrderItem(id=uuid.uuid4(), product_id=product_id, quantity=qty, unit_price=product.price))
        order = Order(id=generate_order_id(), user_id=user_id, status=OrderStatus.pending, total_amount=total, shipping_address=shipping_address)
        order.items = order_items
        db.add(order)
        db.add(OrderEvent(id=uuid.uuid4(), order_id=order.id, from_status=None, to_status=OrderStatus.pending.value, event_metadata={'source': 'checkout'}))
        await db.commit()
        await db.refresh(order)
        await self.cart_service.clear(user_id)
        await publish_event('order.created', {'order_id': order.id})
        for (pid, new_qty) in stock_changes:
            await broadcast_inventory_change(pid, new_qty, source='checkout')
        orders_created.inc()
        order_status_transitions.labels(from_status='none', to_status='pending').inc()
        checkout_duration.observe(time.perf_counter() - t0)
        return order

    async def update_status(self, order_id: str, new_status: OrderStatus, reason: str | None, db: AsyncSession) -> Order:
        order = await db.get(Order, order_id)
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, 'Order not found')
        old_status = order.status
        order.status = new_status
        db.add(OrderEvent(id=uuid.uuid4(), order_id=order.id, from_status=old_status.value if old_status else None, to_status=new_status.value, event_metadata={'reason': reason} if reason else None))
        await db.commit()
        await db.refresh(order)
        await publish_event(f'order.{new_status.value}', {'order_id': order.id, 'status': new_status.value})
        await broadcast_order_status(order.id, new_status.value, old_status.value if old_status else None)
        order_status_transitions.labels(from_status=old_status.value if old_status else 'none', to_status=new_status.value).inc()
        return order
