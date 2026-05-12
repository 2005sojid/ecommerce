import uuid
from fastapi import APIRouter, Query, status
from fastapi.responses import Response
from app.deps import CustomerUser, DBSession
from app.schemas.wishlist import WishlistAdd, WishlistItemOut
from app.services import wishlist_service

router = APIRouter(prefix='/api/wishlist', tags=['Wishlist'])


@router.post('', status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(payload: WishlistAdd, user: CustomerUser, db: DBSession) -> dict:
    await wishlist_service.add(db, user.id, payload.product_id)
    return {'ok': True, 'product_id': str(payload.product_id)}


@router.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(product_id: uuid.UUID, user: CustomerUser, db: DBSession) -> Response:
    await wishlist_service.remove(db, user.id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('')
async def list_wishlist(user: CustomerUser, db: DBSession, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)) -> dict:
    items, total = await wishlist_service.list_for_user(db, user.id, page, per_page)
    return {'items': [WishlistItemOut.model_validate(i) for i in items], 'total': total, 'page': page, 'per_page': per_page}


@router.get('/ids')
async def list_wishlist_ids(user: CustomerUser, db: DBSession) -> list[uuid.UUID]:
    return await wishlist_service.list_ids(db, user.id)
