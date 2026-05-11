import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text
from app.database import async_session

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def run() -> None:
    target_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    query = text(
        """
        SELECT s.id AS seller_id,
               COALESCE(SUM(oi.unit_price * oi.quantity), 0) AS gross,
               COUNT(DISTINCT o.id) AS order_count
        FROM sellers s
        LEFT JOIN products p ON p.seller_id = s.id
        LEFT JOIN order_items oi ON oi.product_id = p.id
        LEFT JOIN orders o ON o.id = oi.order_id
            AND DATE(o.created_at) = :d
            AND o.status IN ('delivered', 'shipped')
        GROUP BY s.id
        """
    )
    upsert = text(
        """
        INSERT INTO settlements (id, seller_id, settlement_date, gross_revenue, fees, net_payout, order_count)
        VALUES (:id, :seller_id, :settlement_date, :gross, :fees, :net, :order_count)
        ON CONFLICT ON CONSTRAINT uq_settlement_seller_date DO UPDATE SET
            gross_revenue = EXCLUDED.gross_revenue,
            fees = EXCLUDED.fees,
            net_payout = EXCLUDED.net_payout,
            order_count = EXCLUDED.order_count
        """
    )
    async with async_session() as db:
        try:
            rows = (await db.execute(query, {'d': target_date})).all()
            for row in rows:
                gross = Decimal(row.gross or 0)
                fees = (gross * Decimal('0.05')).quantize(Decimal('0.01'))
                net = (gross - fees).quantize(Decimal('0.01'))
                await db.execute(upsert, {
                    'id': uuid.uuid4(),
                    'seller_id': row.seller_id,
                    'settlement_date': target_date,
                    'gross': gross,
                    'fees': fees,
                    'net': net,
                    'order_count': int(row.order_count or 0),
                })
            await db.commit()
            logger.info('daily_settlement: processed %d sellers for %s', len(rows), target_date)
        except Exception as exc:
            await db.rollback()
            logger.warning('daily_settlement run failed: %s', exc)


def start() -> None:
    if scheduler.running:
        return
    scheduler.add_job(run, trigger='cron', hour=2, minute=0, id='daily_settlement', replace_existing=True)
    scheduler.start()
    logger.info('APScheduler started: daily_settlement @ 02:00 UTC')


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
