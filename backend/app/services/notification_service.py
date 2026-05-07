"""RabbitMQ publisher (topic exchange `ecommerce`) for order.* and product.*
events.

Queues are declared here (durable) and bound to the exchange:
  - order_pipeline   <- order.*
  - search_sync      <- product.*

When RabbitMQ is unavailable, publish_event degrades to a no-op + warning
so that tests / development do not fail.
"""
import json
import logging
from typing import Optional

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractExchange

from app.config import settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "ecommerce"
ORDER_QUEUE = "order_pipeline"
SEARCH_QUEUE = "search_sync"


class EventBus:
    def __init__(self) -> None:
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchange: Optional[AbstractExchange] = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=16)

        self.exchange = await self.channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )

        order_q = await self.channel.declare_queue(ORDER_QUEUE, durable=True)
        await order_q.bind(self.exchange, routing_key="order.*")

        search_q = await self.channel.declare_queue(SEARCH_QUEUE, durable=True)
        await search_q.bind(self.exchange, routing_key="product.*")

        logger.info("RabbitMQ connected, exchange=%s queues=[%s, %s]", EXCHANGE_NAME, ORDER_QUEUE, SEARCH_QUEUE)

    async def close(self) -> None:
        if self.connection is not None and not self.connection.is_closed:
            await self.connection.close()

    async def publish(self, routing_key: str, payload: dict) -> None:
        if self.exchange is None:
            logger.warning("EventBus not connected, dropping event %s", routing_key)
            return
        message = aio_pika.Message(
            body=json.dumps(payload, default=str).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self.exchange.publish(message, routing_key=routing_key)


event_bus = EventBus()


async def publish_event(routing_key: str, payload: dict) -> None:
    """Backwards-compatible helper: used from routers."""
    try:
        await event_bus.publish(routing_key, payload)
    except Exception as exc:
        logger.warning("publish_event(%s) failed: %s", routing_key, exc)
