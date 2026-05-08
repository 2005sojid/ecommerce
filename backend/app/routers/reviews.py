import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.cache.redis_cache import cache_delete
from app.deps import CurrentUser, DBSession
from app.models.product import Product
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewOut
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
