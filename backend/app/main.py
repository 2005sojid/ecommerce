import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.batch import daily_sales
from app.cache.redis_cache import redis_client
from app.database import engine as db_engine
from app.from_scratch.rate_limiter import RedisRateLimiter
from app.logging_config import configure_logging
from app.metrics import setup_metrics
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import admin, auth, cart, categories, flash_sales, inventory, orders, products, product_images, reviews, wishlist, addresses, notifications, sellers, coupons, returns, chat, ws_chat, settlements, ws
from app.services.notification_service import event_bus
from app.services.search_service import search_service
from app.telemetry import setup_telemetry
from app.workers import order_pipeline, search_sync
configure_logging()
logger = logging.getLogger(__name__)

import asyncio as _asyncio
from app.config import settings as _settings

IS_LEADER = _settings.INSTANCE_ID in ('1', '0')

async def _connect_event_bus_with_retry(max_attempts: int = 12, delay: float = 2.0) -> bool:
    for attempt in range(1, max_attempts + 1):
        try:
            await event_bus.connect()
            return True
        except Exception as exc:
            logger.warning('RabbitMQ connect attempt %d/%d failed: %s', attempt, max_attempts, exc)
            await _asyncio.sleep(delay)
    logger.error('RabbitMQ connect: gave up after %d attempts — order pipeline will NOT run', max_attempts)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_client.ping()
    except Exception as exc:
        logger.warning('Redis ping failed: %s', exc)
    try:
        await search_service.init_index()
    except Exception as exc:
        logger.warning('Meilisearch init failed: %s', exc)
    if await _connect_event_bus_with_retry():
        try:
            await order_pipeline.run()
            await search_sync.run()
            logger.info('RabbitMQ workers registered')
        except Exception as exc:
            logger.error('Worker registration failed: %s', exc, exc_info=True)
    try:
        from app.routers.ws import manager as ws_manager
        await ws_manager.start_pubsub(redis_client)
    except Exception as exc:
        logger.warning('ws pubsub start failed: %s', exc)
    if IS_LEADER:
        try:
            from app.batch import abandoned_cart, daily_settlement
            daily_sales.start()
            abandoned_cart.start()
            daily_settlement.start()
            logger.info('Batch schedulers started (leader instance %s)', _settings.INSTANCE_ID)
        except Exception as exc:
            logger.warning('Scheduler startup failed: %s', exc)
    else:
        logger.info('Instance %s is not leader — skipping batch schedulers', _settings.INSTANCE_ID)
    yield
    try:
        from app.routers.ws import manager as ws_manager
        await ws_manager.stop_pubsub()
    except Exception:
        pass
    if IS_LEADER:
        try:
            from app.batch import abandoned_cart as _ac, daily_settlement as _ds
            _ac.shutdown()
            _ds.shutdown()
            daily_sales.shutdown()
        except Exception:
            pass
    try:
        await event_bus.close()
    except Exception:
        pass
    await redis_client.aclose()
    await search_service.close()
app = FastAPI(title='E-Commerce Platform API', description='Real-time inventory e-commerce system with flash sales, order tracking, and analytics.', version='1.0.0', docs_url='/api/docs', redoc_url='/api/redoc', openapi_url='/api/openapi.json', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])
try:
    setup_telemetry(app, db_engine)
except Exception as exc:
    logger.warning('OpenTelemetry init failed: %s', exc)
setup_metrics(app)
app.add_middleware(RateLimitMiddleware, limiter=RedisRateLimiter(redis_client, max_tokens=30, refill_rate=0.5), paths=['/api/flash-sales/', '/api/auth/login'])
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(product_images.router)
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(flash_sales.router)
app.include_router(reviews.router)
app.include_router(wishlist.router)
app.include_router(addresses.router)
app.include_router(notifications.router)
app.include_router(sellers.router)
app.include_router(coupons.router)
app.include_router(returns.router)
app.include_router(chat.router)
app.include_router(ws_chat.router)
app.include_router(settlements.router)
app.include_router(admin.router)
app.include_router(ws.router)

@app.get('/api/health', tags=['Health'])
async def health() -> dict:
    return {'status': 'ok'}
