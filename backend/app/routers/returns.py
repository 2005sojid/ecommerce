import uuid
from fastapi import APIRouter, Query, status
from app.deps import AdminUser, CustomerUser, DBSession
from app.schemas.returns import ReturnCreate, ReturnOut, ReturnUpdate
from app.services import returns_service

router = APIRouter(prefix='/api/returns', tags=['Returns'])


@router.post('', response_model=ReturnOut, status_code=status.HTTP_201_CREATED)
async def create_return(payload: ReturnCreate, user: CustomerUser, db: DBSession) -> ReturnOut:
    item = await returns_service.create(db, user.id, payload)
    return ReturnOut.model_validate(item)


@router.get('')
async def list_my_returns(user: CustomerUser, db: DBSession, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)) -> dict:
    items, total = await returns_service.list_for_user(db, user.id, page, per_page)
    return {'items': [ReturnOut.model_validate(i) for i in items], 'total': total, 'page': page, 'per_page': per_page}


@router.get('/admin')
async def admin_list_returns(_: AdminUser, db: DBSession, page: int = Query(1, ge=1), per_page: int = Query(50, ge=1, le=200), status: str | None = None) -> dict:
    items, total = await returns_service.list_all(db, page, per_page, status=status)
    return {'items': [ReturnOut.model_validate(i) for i in items], 'total': total, 'page': page, 'per_page': per_page}


@router.patch('/admin/{return_id}', response_model=ReturnOut)
async def admin_update_return(return_id: uuid.UUID, payload: ReturnUpdate, _: AdminUser, db: DBSession) -> ReturnOut:
    item = await returns_service.update(db, return_id, payload)
    return ReturnOut.model_validate(item)
