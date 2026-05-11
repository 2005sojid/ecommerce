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
from app.models.product_variant import ProductVariant
from app.models.seller import Seller
from app.routers.ws import broadcast_inventory_change, broadcast_order_status
from app.services import coupon_service, notification_center
from app.services.cart_service import CartService, _parse_field
from app.services.notification_service import publish_event

LOW_STOCK_THRESHOLD = 10

def generate_order_id() -> str:
    ts = datetime.now(timezone.utc).strftime('%y%m%d')
    rnd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f'ORD{ts}{rnd}'[:20]

class OrderService:

    def __init__(self, cart_service: CartService):
        self.cart_service = cart_service

    async def checkout(self, user_id: uuid.UUID, shipping_address: str, db: AsyncSession, coupon_code: str | None = None) -> Order:
        t0 = time.perf_counter()
        cart_items = await self.cart_service.get_raw(user_id)
        if not cart_items:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Cart is empty')
        total = Decimal('0')
        order_items: list[OrderItem] = []
        stock_changes: list[tuple[uuid.UUID, int]] = []
        low_stock_alerts: list[tuple[uuid.UUID, str, int]] = []
        for (field_str, quantity) in cart_items.items():
            try:
                product_id, variant_id = _parse_field(field_str)
            except (ValueError, TypeError):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f'Invalid cart entry: {field_str}')
            qty = int(quantity)
            product = await db.get(Product, product_id)
            if product is None or not product.is_active:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f'Product {product_id} unavailable')
            if variant_id is not None:
                variant = (await db.execute(
                    select(ProductVariant)
                    .where(ProductVariant.id == variant_id)
                    .with_for_update()
                )).scalar_one_or_none()
                if variant is None or variant.product_id != product_id:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, f'Variant {variant_id} not found')
                if variant.stock_quantity - variant.reserved_quantity < qty:
                    raise HTTPException(status.HTTP_409_CONFLICT, f'Insufficient stock for variant {variant_id}')
                variant.stock_quantity -= qty
                remaining = variant.stock_quantity - variant.reserved_quantity
                stock_changes.append((product_id, variant.stock_quantity))
                unit_price = variant.price
                if remaining < LOW_STOCK_THRESHOLD and product.seller_id is not None:
                    seller = await db.get(Seller, product.seller_id)
                    if seller is not None:
                        low_stock_alerts.append((seller.user_id, product.name, remaining))
            else:
                inventory = (await db.execute(
                    select(Inventory).where(Inventory.product_id == product_id).with_for_update()
                )).scalar_one_or_none()
                if inventory is None:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, f'Inventory not found for product {product_id}')
                if inventory.quantity - inventory.reserved < qty:
                    raise HTTPException(status.HTTP_409_CONFLICT, f'Insufficient stock for product {product_id}')
                inventory.quantity -= qty
                remaining = inventory.quantity - inventory.reserved
                stock_changes.append((product_id, inventory.quantity))
                unit_price = product.price
                if remaining < LOW_STOCK_THRESHOLD and product.seller_id is not None:
                    seller = await db.get(Seller, product.seller_id)
                    if seller is not None:
                        low_stock_alerts.append((seller.user_id, product.name, remaining))
            line_total = unit_price * qty
            total += line_total
            order_items.append(OrderItem(
                id=uuid.uuid4(),
                product_id=product_id,
                variant_id=variant_id,
                quantity=qty,
                unit_price=unit_price,
            ))
        coupon_meta: dict | None = None
        applied_coupon_id: uuid.UUID | None = None
        if coupon_code:
            result = await coupon_service.validate(db, user_id, coupon_code, total)
            if not result.valid:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f'Invalid coupon: {result.message}')
            applied_coupon_id = result.coupon_id
            total = total - result.discount_amount
            if total < 0:
                total = Decimal('0')
            coupon_meta = {'coupon_code': coupon_code, 'discount_amount': str(result.discount_amount)}
        order = Order(id=generate_order_id(), user_id=user_id, status=OrderStatus.pending, total_amount=total, shipping_address=shipping_address)
        order.items = order_items
        db.add(order)
        event_meta = {'source': 'checkout'}
        if coupon_meta:
            event_meta.update(coupon_meta)
        db.add(OrderEvent(id=uuid.uuid4(), order_id=order.id, from_status=None, to_status=OrderStatus.pending.value, event_metadata=event_meta))
        await db.commit()
        if applied_coupon_id is not None:
            try:
                await coupon_service.apply(db, user_id, applied_coupon_id, order.id)
            except Exception:
                pass
        await db.refresh(order)
        await self.cart_service.clear(user_id)
        await publish_event('order.created', {'order_id': order.id})
        try:
            await notification_center.create(
                db, user_id,
                type_='order_status',
                title=f'Order {order.id} placed',
                body=f'Total: ${order.total_amount}',
                link=f'/orders/{order.id}',
            )
        except Exception:
            pass
        for (seller_user_id, product_name, remaining) in low_stock_alerts:
            try:
                await notification_center.create(
                    db, seller_user_id,
                    type_='low_stock',
                    title=f'Low stock: {product_name} ({remaining} left)',
                    body=None,
                    link='/seller/products',
                )
            except Exception:
                pass
        for (pid, new_qty) in stock_changes:
            await broadcast_inventory_change(pid, new_qty, source='checkout')
        orders_created.inc()
        order_status_transitions.labels(from_status='none', to_status='pending').inc()
        checkout_duration.observe(time.perf_counter() - t0)
        return order

    async def update_status(self, order_id: str, new_status: OrderStatus, reason: str | None, db: AsyncSession, tracking_number: str | None = None) -> Order:
        order = await db.get(Order, order_id)
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, 'Order not found')
        old_status = order.status
        order.status = new_status
        if tracking_number is not None:
            order.tracking_number = tracking_number
        event_meta: dict | None = None
        if reason or tracking_number is not None:
            event_meta = {}
            if reason:
                event_meta['reason'] = reason
            if tracking_number is not None:
                event_meta['tracking_number'] = tracking_number
        db.add(OrderEvent(id=uuid.uuid4(), order_id=order.id, from_status=old_status.value if old_status else None, to_status=new_status.value, event_metadata=event_meta))
        await db.commit()
        await db.refresh(order)
        await publish_event(f'order.{new_status.value}', {'order_id': order.id, 'status': new_status.value})
        await broadcast_order_status(order.id, new_status.value, old_status.value if old_status else None)
        order_status_transitions.labels(from_status=old_status.value if old_status else 'none', to_status=new_status.value).inc()
        try:
            await notification_center.create(
                db, order.user_id,
                type_='order_status',
                title=f'Order {order.id} is now {new_status.value}',
                body=(reason or None),
                link=f'/orders/{order.id}',
            )
        except Exception:
            pass
        return order
