from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Query
from sqlalchemy import select, func, text
from app.deps import AdminUser, DBSession
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.services.search_service import search_service
router = APIRouter(prefix='/api/admin', tags=['Admin'])

@router.get('/analytics/daily')
async def daily_sales(target_date: Annotated[date, Query(alias='date')], _: AdminUser, db: DBSession) -> dict:
    mv_row = None
    try:
        mv_row = (await db.execute(text('SELECT order_count, total_revenue, unique_customers FROM mv_daily_sales WHERE sale_date = :d'), {'d': target_date})).first()
    except Exception:
        await db.rollback()
    if mv_row is not None:
        return {'date': target_date.isoformat(), 'order_count': int(mv_row[0]), 'total_revenue': str(mv_row[1]), 'unique_customers': int(mv_row[2]), 'source': 'materialized_view'}
    start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    where = (Order.created_at >= start) & (Order.created_at < end) & (Order.status != OrderStatus.cancelled)
    row = (await db.execute(select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0), func.count(func.distinct(Order.user_id))).where(where))).one()
    return {'date': target_date.isoformat(), 'order_count': int(row[0]), 'total_revenue': str(row[1]), 'unique_customers': int(row[2]), 'source': 'on_demand'}

@router.post('/analytics/refresh')
async def refresh_daily_sales(_: AdminUser, db: DBSession) -> dict:
    try:
        await db.execute(text('REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales'))
    except Exception:
        await db.rollback()
        await db.execute(text('REFRESH MATERIALIZED VIEW mv_daily_sales'))
    await db.commit()
    return {'status': 'refreshed'}

@router.get('/analytics/top-products')
async def top_products(_: AdminUser, db: DBSession, days: Annotated[int, Query(ge=1, le=365)]=30, limit: Annotated[int, Query(ge=1, le=100)]=10) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (await db.execute(select(OrderItem.product_id, Product.name, func.sum(OrderItem.quantity).label('units_sold'), func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')).join(Order, Order.id == OrderItem.order_id).join(Product, Product.id == OrderItem.product_id).where(Order.created_at >= since, Order.status != OrderStatus.cancelled).group_by(OrderItem.product_id, Product.name).order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc()).limit(limit))).all()
    return [{'product_id': str(r.product_id), 'name': r.name, 'units_sold': int(r.units_sold), 'revenue': str(r.revenue)} for r in rows]

@router.post('/search/reindex')
async def reindex_search(_: AdminUser, db: DBSession) -> dict:
    count = await search_service.reindex_all(db)
    return {'indexed': count}

@router.get('/inventory/low-stock')
async def low_stock(_: AdminUser, db: DBSession, threshold: Annotated[int, Query(ge=0)]=10) -> list[dict]:
    rows = (await db.execute(select(Inventory, Product.name).join(Product, Product.id == Inventory.product_id).where(Inventory.quantity - Inventory.reserved < threshold).order_by(Inventory.quantity.asc()))).all()
    return [{'product_id': str(inv.product_id), 'name': name, 'quantity': inv.quantity, 'reserved': inv.reserved, 'available': inv.quantity - inv.reserved} for (inv, name) in rows]
