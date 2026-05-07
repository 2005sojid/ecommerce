"""Cron job: daily sales aggregation into a materialised view.

Schedule: 02:00 UTC every day. Uses APScheduler (asyncio).
"""
import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text

from app.database import async_session

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def refresh_daily_sales_mv() -> None:
    """REFRESH MATERIALIZED VIEW mv_daily_sales (CONCURRENTLY)."""
    yesterday = date.today() - timedelta(days=1)
    async with async_session() as db:
        try:
            await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales"))
        except Exception as exc:
            logger.warning("CONCURRENTLY refresh failed (%s), trying plain", exc)
            await db.execute(text("REFRESH MATERIALIZED VIEW mv_daily_sales"))
        await db.commit()
    logger.info("daily_sales mv refreshed for %s", yesterday)


def start() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        refresh_daily_sales_mv,
        trigger="cron",
        hour=2,
        minute=0,
        id="daily_sales_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started: daily_sales_refresh @ 02:00 UTC")


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
