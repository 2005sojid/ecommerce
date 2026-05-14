import asyncio
import json
import logging
import uuid
import aio_pika
from sqlalchemy import select
from app.database import async_session
from app.metrics import order_status_transitions
from app.models.order import Order, OrderStatus
from app.models.order_event import OrderEvent
from app.routers.ws import broadcast_order_status
from app.services.notification_service import ORDER_QUEUE, event_bus, publish_event
logger = logging.getLogger(__name__)
NEXT_STAGE: dict[str, tuple[OrderStatus, str, float]] = {
    'order.created': (OrderStatus.confirmed, 'order.confirmed', 2.0),
    'order.confirmed': (OrderStatus.processing, 'order.processing', 0.5),
    'order.processing': (OrderStatus.packed, 'order.packed', 3.0),
    'order.packed': (OrderStatus.shipped, 'order.shipped', 1.0),
    'order.shipped': (OrderStatus.delivered, 'order.delivered', 5.0),
}

async def _advance(order_id: str, new_status: OrderStatus) -> None:
    async with async_session() as db:
        order = await db.get(Order, order_id)
        if order is None:
            logger.warning('Order %s not found, skipping', order_id)
            return
        old_status = order.status
        order.status = new_status
        db.add(OrderEvent(id=uuid.uuid4(), order_id=order.id, from_status=old_status.value if old_status else None, to_status=new_status.value, event_metadata={'source': 'pipeline'}))
        await db.commit()
    logger.info('order %s: %s -> %s', order_id, old_status.value if old_status else None, new_status.value)
    order_status_transitions.labels(from_status=old_status.value if old_status else 'none', to_status=new_status.value).inc()
    await broadcast_order_status(order_id, new_status.value, old_status.value if old_status else None)

async def _handle(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        routing_key = message.routing_key
        try:
            payload = json.loads(message.body)
        except json.JSONDecodeError:
            logger.error('bad json in %s, dropping', routing_key)
            return
        order_id = payload.get('order_id')
        if not order_id or routing_key not in NEXT_STAGE:
            return
        (new_status, next_event, delay) = NEXT_STAGE[routing_key]
        await asyncio.sleep(delay)
        await _advance(order_id, new_status)
        await publish_event(next_event, {'order_id': order_id, 'status': new_status.value})

async def run() -> None:
    assert event_bus.channel is not None, 'EventBus not connected'
    queue = await event_bus.channel.declare_queue(ORDER_QUEUE, durable=True)
    logger.info('order_pipeline worker subscribed to %s', ORDER_QUEUE)
    await queue.consume(_handle)
