import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderStatus
from app.models.returns import Return
from app.schemas.returns import ReturnCreate, ReturnUpdate
from app.services import notification_center  # noqa: F401


async def create(db: AsyncSession, user_id: uuid.UUID, payload: ReturnCreate) -> Return:
    order = await db.get(Order, payload.order_id)
    if order is None or order.user_id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Order not found or not owned by user')
    if order.status not in (OrderStatus.delivered, OrderStatus.shipped):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Order must be delivered or shipped to request a return')
    existing = await db.scalar(
        select(Return).where(
            Return.order_id == payload.order_id,
            Return.status.in_(('pending', 'approved')),
        )
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f'A {existing.status} return already exists for this order')
    item = Return(id=uuid.uuid4(), order_id=payload.order_id, user_id=user_id, status='pending', reason=payload.reason)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def list_for_user(db: AsyncSession, user_id: uuid.UUID, page: int, per_page: int) -> tuple[list[Return], int]:
    total = await db.scalar(select(func.count(Return.id)).where(Return.user_id == user_id)) or 0
    offset = (page - 1) * per_page
    stmt = select(Return).where(Return.user_id == user_id).order_by(Return.created_at.desc()).limit(per_page).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    return (list(rows), int(total))


async def list_all(db: AsyncSession, page: int, per_page: int, status: str | None = None) -> tuple[list[Return], int]:
    where = []
    if status:
        where.append(Return.status == status)
    total = await db.scalar(select(func.count(Return.id)).where(*where)) or 0
    offset = (page - 1) * per_page
    stmt = select(Return).where(*where).order_by(Return.created_at.desc()).limit(per_page).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    return (list(rows), int(total))


async def update(db: AsyncSession, return_id: uuid.UUID, payload: ReturnUpdate) -> Return:
    item = await db.get(Return, return_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Return not found')
    data = payload.model_dump(exclude_unset=True)
    status_changed = 'status' in data and data['status'] != item.status
    for field, value in data.items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    if status_changed:
        try:
            await notification_center.create(
                db,
                item.user_id,
                'return_update',
                f'Return status: {item.status}',
                body=f'Your return for order {item.order_id} is now {item.status}.',
                link=f'/returns',
            )
        except Exception:
            pass
    return item
