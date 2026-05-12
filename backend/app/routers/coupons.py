import uuid
from fastapi import APIRouter, Query, status
from fastapi.responses import Response
from app.deps import AdminUser, CustomerUser, DBSession
from app.schemas.coupon import CouponCreate, CouponOut, CouponUpdate, CouponValidate, CouponValidationResult
from app.services import coupon_service

router = APIRouter(prefix='/api/coupons', tags=['Coupons'])


@router.post('/validate')
async def validate_coupon(payload: CouponValidate, user: CustomerUser, db: DBSession) -> CouponValidationResult:
    return await coupon_service.validate(db, user.id, payload.code, payload.order_total)


@router.get('')
async def list_coupons(_: AdminUser, db: DBSession, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)) -> dict:
    items, total = await coupon_service.list_all(db, page, per_page)
    return {'items': [CouponOut.model_validate(c) for c in items], 'total': total, 'page': page, 'per_page': per_page}


@router.post('', status_code=status.HTTP_201_CREATED)
async def create_coupon(payload: CouponCreate, _: AdminUser, db: DBSession) -> CouponOut:
    coupon = await coupon_service.create(db, payload)
    return CouponOut.model_validate(coupon)


@router.patch('/{coupon_id}')
async def update_coupon(coupon_id: uuid.UUID, payload: CouponUpdate, _: AdminUser, db: DBSession) -> CouponOut:
    coupon = await coupon_service.update(db, coupon_id, payload)
    return CouponOut.model_validate(coupon)


@router.delete('/{coupon_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_coupon(coupon_id: uuid.UUID, _: AdminUser, db: DBSession) -> Response:
    await coupon_service.delete_coupon(db, coupon_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
