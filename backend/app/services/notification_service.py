import asyncio
import json
import logging
from typing import Optional
import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection, AbstractExchange
from app.config import settings
logger = logging.getLogger(__name__)
EXCHANGE_NAME = 'ecommerce'
ORDER_QUEUE = 'order_pipeline'
SEARCH_QUEUE = 'search_sync'
PUBLISH_MAX_ATTEMPTS = 3


class EventBus:

    def __init__(self) -> None:
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.exchange: Optional[AbstractExchange] = None
        self._reconnect_lock = asyncio.Lock()

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=16)
        self.exchange = await self.channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
        order_q = await self.channel.declare_queue(ORDER_QUEUE, durable=True)
        await order_q.bind(self.exchange, routing_key='order.*')
        search_q = await self.channel.declare_queue(SEARCH_QUEUE, durable=True)
        await search_q.bind(self.exchange, routing_key='product.*')
        logger.info('RabbitMQ connected, exchange=%s queues=[%s, %s]', EXCHANGE_NAME, ORDER_QUEUE, SEARCH_QUEUE)

    async def close(self) -> None:
        if self.connection is not None and (not self.connection.is_closed):
            try:
                await self.connection.close()
            except Exception:
                pass

    def _channel_is_dead(self) -> bool:
        try:
            if self.connection is None or self.connection.is_closed:
                return True
            if self.channel is None or self.channel.is_closed:
                return True
        except AttributeError:
            return True
        return False

    async def _force_reconnect(self) -> None:
        async with self._reconnect_lock:
            try:
                if self.connection is not None and not self.connection.is_closed:
                    await self.connection.close()
            except Exception:
                pass
            self.connection = None
            self.channel = None
            self.exchange = None
            await self.connect()

    async def _ensure_connected(self) -> None:
        if not self._channel_is_dead() and self.exchange is not None:
            return
        await self._force_reconnect()

    async def publish(self, routing_key: str, payload: dict) -> None:
        message_body = json.dumps(payload, default=str).encode()
        last_exc: Optional[BaseException] = None
        for attempt in range(1, PUBLISH_MAX_ATTEMPTS + 1):
            try:
                await self._ensure_connected()
                if self.exchange is None:
                    raise RuntimeError('exchange is None after reconnect')
                message = aio_pika.Message(
                    body=message_body,
                    content_type='application/json',
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                )
                await self.exchange.publish(message, routing_key=routing_key)
                if attempt > 1:
                    logger.info('publish recovered on attempt %d (routing_key=%s)', attempt, routing_key)
                return
            except (AttributeError, aio_pika.exceptions.AMQPException, RuntimeError) as exc:
                last_exc = exc
                logger.warning('publish attempt %d/%d failed (%s) — forcing reconnect', attempt, PUBLISH_MAX_ATTEMPTS, exc)
                try:
                    await self._force_reconnect()
                except Exception as reconnect_exc:
                    logger.warning('reconnect attempt %d failed: %s', attempt, reconnect_exc)
                    await asyncio.sleep(0.5 * attempt)
        assert last_exc is not None
        raise last_exc


event_bus = EventBus()

async def publish_event(routing_key: str, payload: dict) -> bool:
    try:
        await event_bus.publish(routing_key, payload)
        return True
    except Exception as exc:
        logger.error('publish_event(%s) failed: %s — pipeline will NOT advance this order', routing_key, exc, exc_info=True)
        return False
