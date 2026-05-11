from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from app.deps import CurrentUser, DBSession
from app.models.seller import Seller
from app.models.settlement import Settlement
from app.models.user import UserRole
from app.schemas.settlement import SettlementOut


async def get_current_seller(user: CurrentUser, db: DBSession) -> Seller:
    if user.role != UserRole.seller:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Seller role required')
    seller = (await db.execute(select(Seller).where(Seller.user_id == user.id))).scalar_one_or_none()
    if seller is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Seller profile not found')
    return seller


SellerUser = Annotated[Seller, Depends(get_current_seller)]

router = APIRouter(prefix='/api/settlements', tags=['Settlements'])


@router.get('/me', response_model=list[SettlementOut])
async def my_settlements(
    seller: SellerUser,
    db: DBSession,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[SettlementOut]:
    offset = (page - 1) * per_page
    stmt = (
        select(Settlement)
        .where(Settlement.seller_id == seller.id)
        .order_by(Settlement.settlement_date.desc())
        .limit(per_page)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [SettlementOut.model_validate(r) for r in rows]
