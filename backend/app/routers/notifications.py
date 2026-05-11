import uuid
from fastapi import APIRouter, Query, status
from fastapi.responses import Response
from app.deps import CurrentUser, DBSession
from app.schemas.notification import NotificationOut, UnreadCount
from app.services import notification_center

router = APIRouter(prefix='/api/notifications', tags=['Notifications'])


@router.get('')
async def list_notifications(user: CurrentUser, db: DBSession, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100), unread_only: bool = Query(False)) -> dict:
    items, total = await notification_center.list_for_user(db, user.id, page, per_page, only_unread=unread_only)
    return {'items': [NotificationOut.model_validate(i) for i in items], 'total': total, 'page': page, 'per_page': per_page}


@router.get('/unread-count')
async def get_unread_count(user: CurrentUser, db: DBSession) -> UnreadCount:
    count = await notification_center.unread_count(db, user.id)
    return UnreadCount(count=count)


@router.post('/{notification_id}/read', status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(notification_id: uuid.UUID, user: CurrentUser, db: DBSession) -> Response:
    await notification_center.mark_read(db, user.id, notification_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/read-all')
async def mark_all_notifications_read(user: CurrentUser, db: DBSession) -> dict:
    updated = await notification_center.mark_all_read(db, user.id)
    return {'updated': updated}
