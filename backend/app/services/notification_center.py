import uuid
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification


async def create(db: AsyncSession, user_id: uuid.UUID, type_: str, title: str, body: str | None = None, link: str | None = None) -> Notification:
    item = Notification(id=uuid.uuid4(), user_id=user_id, type=type_, title=title, body=body, link=link, is_read=False)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    try:
        from app.routers.ws import broadcast_user_notification
        await broadcast_user_notification(user_id, {
            'event': 'notification',
            'id': str(item.id),
            'type': item.type,
            'title': item.title,
            'body': item.body,
            'link': item.link,
            'is_read': item.is_read,
            'created_at': item.created_at.isoformat() if item.created_at else None,
        })
    except Exception:
        pass
    return item


async def list_for_user(db: AsyncSession, user_id: uuid.UUID, page: int, per_page: int, only_unread: bool = False) -> tuple[list[Notification], int]:
    base_where = [Notification.user_id == user_id]
    if only_unread:
        base_where.append(Notification.is_read == False)
    total = await db.scalar(select(func.count(Notification.id)).where(*base_where)) or 0
    offset = (page - 1) * per_page
    stmt = select(Notification).where(*base_where).order_by(Notification.created_at.desc()).limit(per_page).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows), int(total)


async def mark_read(db: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
    item = await db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id))
    if item is None:
        return False
    if not item.is_read:
        item.is_read = True
        await db.commit()
    return True


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(update(Notification).where(Notification.user_id == user_id, Notification.is_read == False).values(is_read=True))
    await db.commit()
    return int(result.rowcount or 0)


async def unread_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    total = await db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user_id, Notification.is_read == False))
    return int(total or 0)
