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
from app.routers import admin, auth, cart, categories, flash_sales, inventory, orders, products, reviews, ws
from app.services.notification_service import event_bus
from app.services.search_service import search_service
from app.telemetry import setup_telemetry
from app.workers import order_pipeline, search_sync
configure_logging()
logger = logging.getLogger(__name__)

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
    try:
        await event_bus.connect()
        await order_pipeline.run()
        await search_sync.run()
    except Exception as exc:
        logger.warning('RabbitMQ/workers startup failed: %s', exc)
    try:
        daily_sales.start()
    except Exception as exc:
        logger.warning('Scheduler startup failed: %s', exc)
    yield
    daily_sales.shutdown()
    await event_bus.close()
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
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(flash_sales.router)
app.include_router(reviews.router)
app.include_router(admin.router)
app.include_router(ws.router)

@app.get('/api/health', tags=['Health'])
async def health() -> dict:
    return {'status': 'ok'}
