import logging
import uuid
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.cache.redis_cache import redis_client
from app.database import async_session
from app.services import notification_center

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def run() -> None:
    try:
        async for key in redis_client.scan_iter(match='cart:*', count=200):
            try:
                key_str = key.decode() if isinstance(key, bytes) else key
                suffix = key_str.split(':', 1)[1] if ':' in key_str else ''
                if not suffix:
                    continue
                try:
                    user_uuid = uuid.UUID(suffix)
                except (ValueError, TypeError):
                    continue
                item_count = await redis_client.hlen(key_str)
                if not item_count:
                    continue
                sentinel_key = f'notif_sent:abandoned_cart:{user_uuid}'
                if await redis_client.exists(sentinel_key):
                    continue
                async with async_session() as db:
                    await notification_center.create(
                        db,
                        user_uuid,
                        type_='abandoned_cart',
                        title='Items waiting in your cart',
                        body='Complete your purchase before they sell out.',
                        link='/cart',
                    )
                await redis_client.set(sentinel_key, '1', ex=86400)
            except Exception as exc:
                logger.warning('abandoned_cart: failed for key=%s: %s', key, exc)
    except Exception as exc:
        logger.warning('abandoned_cart scan failed: %s', exc)


def start() -> None:
    if scheduler.running:
        return
    scheduler.add_job(run, trigger='interval', hours=1, id='abandoned_cart_run', replace_existing=True)
    scheduler.start()
    logger.info('APScheduler started: abandoned_cart hourly')


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
