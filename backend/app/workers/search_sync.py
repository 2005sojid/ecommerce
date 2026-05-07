"""Search index sync (consumer queue `search_sync`).

product.created / product.updated -> fetch from PG -> upsert into Meilisearch
product.deleted                   -> delete document from Meilisearch
"""
import json
import logging
import uuid

import aio_pika

from app.database import async_session
from app.models.product import Product
from app.services.notification_service import SEARCH_QUEUE, event_bus
from app.services.search_service import fetch_category_name, search_service

logger = logging.getLogger(__name__)


async def _handle(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        routing_key = message.routing_key
        try:
            payload = json.loads(message.body)
        except json.JSONDecodeError:
            logger.error("bad json in %s", routing_key)
            return

        product_id_raw = payload.get("product_id")
        if not product_id_raw:
            return
        product_id = uuid.UUID(product_id_raw)

        try:
            if routing_key == "product.deleted":
                await search_service.delete_product(product_id)
                logger.info("search: deleted %s", product_id)
                return

            async with async_session() as db:
                product = await db.get(Product, product_id)
                if product is None:
                    logger.warning("product %s not found", product_id)
                    return
                cat_name = await fetch_category_name(db, product.category_id)
            await search_service.index_product(product, cat_name)
            logger.info("search: indexed %s (%s)", product_id, routing_key)
        except Exception as exc:
            logger.exception("search sync failed for %s: %s", product_id, exc)


async def run() -> None:
    assert event_bus.channel is not None, "EventBus not connected"
    queue = await event_bus.channel.declare_queue(SEARCH_QUEUE, durable=True)
    logger.info("search_sync worker subscribed to %s", SEARCH_QUEUE)
    await queue.consume(_handle)
