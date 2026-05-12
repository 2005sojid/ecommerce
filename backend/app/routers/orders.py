from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.cache.redis_cache import redis_client
from app.deps import AdminUser, CurrentUser, CustomerUser, DBSession
from app.models.order import Order
from app.models.order_event import OrderEvent
from app.models.product import Product
from app.models.user import UserRole
from app.schemas.common import Page
from app.schemas.order import CheckoutRequest, OrderDetail, OrderEventOut, OrderOut, OrderStatusUpdate
from app.services.cart_service import CartService
from app.services.order_service import OrderService
router = APIRouter(prefix='/api/orders', tags=['Orders'])
_order_service = OrderService(CartService(redis_client))

@router.post('', response_model=OrderDetail, status_code=status.HTTP_201_CREATED)
async def checkout(payload: CheckoutRequest, user: CustomerUser, db: DBSession) -> OrderDetail:
    order = await _order_service.checkout(user.id, payload.shipping_address, db, coupon_code=payload.coupon_code)
    full = (await db.execute(select(Order).where(Order.id == order.id).options(selectinload(Order.items), selectinload(Order.events)))).scalar_one()
    return OrderDetail.model_validate(full)

@router.get('', response_model=Page[OrderOut])
async def list_my_orders(user: CustomerUser, db: DBSession, page: Annotated[int, Query(ge=1)]=1, per_page: Annotated[int, Query(ge=1, le=100)]=20) -> Page[OrderOut]:
    where = Order.user_id == user.id
    total = (await db.execute(select(func.count()).select_from(Order).where(where))).scalar_one()
    rows = (await db.execute(select(Order).where(where).order_by(Order.created_at.desc()).offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return Page[OrderOut](items=[OrderOut.model_validate(o) for o in rows], total=total, page=page, per_page=per_page)

@router.get('/{order_id}', response_model=OrderDetail)
async def get_order(order_id: str, user: CurrentUser, db: DBSession) -> OrderDetail:
    order = (await db.execute(select(Order).where(Order.id == order_id).options(selectinload(Order.items), selectinload(Order.events)))).scalar_one_or_none()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Order not found')
    if order.user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Not your order')
    detail = OrderDetail.model_validate(order)
    product_ids = {it.product_id for it in detail.items}
    if product_ids:
        rows = (await db.execute(select(Product.id, Product.name, Product.image_url).where(Product.id.in_(product_ids)))).all()
        by_id = {pid: (pname, pimg) for pid, pname, pimg in rows}
        for it in detail.items:
            info = by_id.get(it.product_id)
            if info is not None:
                it.product_name, it.product_image_url = info
    return detail

@router.patch('/{order_id}/status', response_model=OrderOut)
async def update_status(order_id: str, payload: OrderStatusUpdate, _: AdminUser, db: DBSession) -> OrderOut:
    order = await _order_service.update_status(order_id, payload.status, payload.reason, db, tracking_number=payload.tracking_number)
    return OrderOut.model_validate(order)

@router.get('/{order_id}/events', response_model=list[OrderEventOut])
async def order_events(order_id: str, user: CurrentUser, db: DBSession) -> list[OrderEventOut]:
    order = await db.get(Order, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Order not found')
    if order.user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Not your order')
    events = (await db.execute(select(OrderEvent).where(OrderEvent.order_id == order_id).order_by(OrderEvent.timestamp.asc()))).scalars().all()
    return [OrderEventOut.model_validate(e) for e in events]
