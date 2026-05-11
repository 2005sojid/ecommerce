import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.coupon import Coupon, CouponUsage
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponValidationResult


async def validate(db: AsyncSession, user_id: uuid.UUID, code: str, order_total: Decimal) -> CouponValidationResult:
    stmt = select(Coupon).where(func.lower(Coupon.code) == code.strip().lower())
    coupon = await db.scalar(stmt)
    if coupon is None:
        return CouponValidationResult(valid=False, message='Coupon not found')
    if not coupon.is_active:
        return CouponValidationResult(valid=False, message='Coupon is not active')
    now = datetime.now(timezone.utc)
    if coupon.valid_from is not None and now < coupon.valid_from:
        return CouponValidationResult(valid=False, message='Coupon is not yet valid')
    if coupon.valid_to is not None and now > coupon.valid_to:
        return CouponValidationResult(valid=False, message='Coupon has expired')
    if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
        return CouponValidationResult(valid=False, message='Coupon usage limit reached')
    if coupon.min_order_amount is not None and order_total < coupon.min_order_amount:
        return CouponValidationResult(valid=False, message=f'Order total must be at least {coupon.min_order_amount}')
    if coupon.discount_type == 'percent':
        discount = (order_total * coupon.discount_value / Decimal('100')).quantize(Decimal('0.01'))
        if discount > order_total:
            discount = order_total
    elif coupon.discount_type == 'fixed':
        discount = min(coupon.discount_value, order_total)
    else:
        return CouponValidationResult(valid=False, message='Invalid coupon discount type')
    return CouponValidationResult(valid=True, coupon_id=coupon.id, discount_amount=discount, message='Coupon applied')


async def apply(db: AsyncSession, user_id: uuid.UUID, coupon_id: uuid.UUID, order_id: str) -> CouponUsage:
    coupon = await db.get(Coupon, coupon_id)
    if coupon is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Coupon not found')
    usage = CouponUsage(id=uuid.uuid4(), coupon_id=coupon_id, user_id=user_id, order_id=order_id)
    db.add(usage)
    coupon.used_count = (coupon.used_count or 0) + 1
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, 'Coupon already used for this order')
    await db.refresh(usage)
    return usage


async def list_all(db: AsyncSession, page: int, per_page: int) -> tuple[list[Coupon], int]:
    total = await db.scalar(select(func.count(Coupon.id))) or 0
    offset = (page - 1) * per_page
    stmt = select(Coupon).order_by(Coupon.created_at.desc()).limit(per_page).offset(offset)
    items = list((await db.scalars(stmt)).all())
    return items, int(total)


async def create(db: AsyncSession, payload: CouponCreate) -> Coupon:
    coupon = Coupon(
        id=uuid.uuid4(),
        code=payload.code.strip(),
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        scope=payload.scope,
        seller_id=payload.seller_id,
        min_order_amount=payload.min_order_amount,
        max_uses=payload.max_uses,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        is_active=payload.is_active,
    )
    db.add(coupon)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, 'Coupon code already exists')
    await db.refresh(coupon)
    return coupon


async def update(db: AsyncSession, coupon_id: uuid.UUID, payload: CouponUpdate) -> Coupon:
    coupon = await db.get(Coupon, coupon_id)
    if coupon is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Coupon not found')
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(coupon, k, v)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, 'Coupon code already exists')
    await db.refresh(coupon)
    return coupon


async def delete_coupon(db: AsyncSession, coupon_id: uuid.UUID) -> bool:
    result = await db.execute(delete(Coupon).where(Coupon.id == coupon_id))
    await db.commit()
    return (result.rowcount or 0) > 0
