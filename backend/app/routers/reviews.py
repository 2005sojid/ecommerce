import uuid
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.cache.redis_cache import cache_delete
from app.deps import AdminUser, CurrentUser, DBSession
from app.models.product import Product
from app.models.review import Review
from app.models.seller import Seller
from app.models.user import UserRole
from app.schemas.common import Page
from app.schemas.review import ReviewCreate, ReviewModerate, ReviewOut, ReviewRespond, ReviewVoteIn
from app.services import review_vote_service
router = APIRouter(prefix='/api/reviews', tags=['Reviews'])

@router.post('', response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(payload: ReviewCreate, user: CurrentUser, db: DBSession) -> ReviewOut:
    product = await db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    review = Review(id=uuid.uuid4(), user_id=user.id, product_id=payload.product_id, rating=payload.rating, comment=payload.comment)
    db.add(review)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, 'You already reviewed this product')
    await db.refresh(review)
    await cache_delete(f'product:{payload.product_id}', f'product:{payload.product_id}:avg_rating')
    return ReviewOut.model_validate(review)


@router.post('/{review_id}/vote')
async def vote_review(review_id: uuid.UUID, payload: ReviewVoteIn, user: CurrentUser, db: DBSession) -> dict:
    helpful_count = await review_vote_service.upsert_vote(db, user.id, review_id, payload.vote)
    return {'helpful_count': helpful_count}


@router.delete('/{review_id}/vote')
async def unvote_review(review_id: uuid.UUID, user: CurrentUser, db: DBSession) -> dict:
    helpful_count = await review_vote_service.remove_vote(db, user.id, review_id)
    return {'helpful_count': helpful_count}


@router.post('/{review_id}/respond', response_model=ReviewOut)
async def respond_review(review_id: uuid.UUID, payload: ReviewRespond, user: CurrentUser, db: DBSession) -> ReviewOut:
    if user.role != UserRole.seller:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Seller privileges required')
    seller = (await db.execute(select(Seller).where(Seller.user_id == user.id))).scalar_one_or_none()
    if seller is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Seller profile not found')
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Review not found')
    product = await db.get(Product, review.product_id)
    if product is None or product.seller_id != seller.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'You do not own this product')
    review.seller_response = payload.response
    review.seller_response_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(review)
    return ReviewOut.model_validate(review)


@router.get('/admin', response_model=Page[ReviewOut])
async def admin_list_reviews(_: AdminUser, db: DBSession, page: Annotated[int, Query(ge=1)] = 1, per_page: Annotated[int, Query(ge=1, le=100)] = 50, approved: bool | None = None) -> Page[ReviewOut]:
    conditions = []
    if approved is not None:
        conditions.append(Review.is_approved.is_(approved))
    stmt_count = select(func.count()).select_from(Review)
    stmt = select(Review)
    if conditions:
        for c in conditions:
            stmt_count = stmt_count.where(c)
            stmt = stmt.where(c)
    total = (await db.execute(stmt_count)).scalar_one()
    stmt = stmt.order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()
    return Page[ReviewOut](items=[ReviewOut.model_validate(r) for r in rows], total=total, page=page, per_page=per_page)


@router.patch('/admin/{review_id}', response_model=ReviewOut)
async def admin_moderate_review(review_id: uuid.UUID, payload: ReviewModerate, _: AdminUser, db: DBSession) -> ReviewOut:
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Review not found')
    review.is_approved = payload.is_approved
    await db.commit()
    await db.refresh(review)
    await cache_delete(f'product:{review.product_id}', f'product:{review.product_id}:avg_rating')
    return ReviewOut.model_validate(review)
