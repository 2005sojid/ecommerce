import uuid
from fastapi import HTTPException, status
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.review import Review
from app.models.review_vote import ReviewVote


async def _recompute_helpful(db: AsyncSession, review: Review, review_id: uuid.UUID) -> int:
    count = await db.scalar(select(func.count()).select_from(ReviewVote).where(ReviewVote.review_id == review_id, ReviewVote.vote == 1)) or 0
    review.helpful_count = int(count)
    return int(count)


async def upsert_vote(db: AsyncSession, user_id: uuid.UUID, review_id: uuid.UUID, vote: int) -> int:
    if vote not in (-1, 1):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'vote must be -1 or 1')
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Review not found')
    rv = ReviewVote(id=uuid.uuid4(), review_id=review_id, user_id=user_id, vote=vote)
    db.add(rv)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        review = await db.get(Review, review_id)
        existing = await db.scalar(select(ReviewVote).where(ReviewVote.review_id == review_id, ReviewVote.user_id == user_id))
        if existing is None:
            raise HTTPException(status.HTTP_409_CONFLICT, 'Could not record vote')
        existing.vote = vote
        await db.flush()
    new_count = await _recompute_helpful(db, review, review_id)
    await db.commit()
    return new_count


async def remove_vote(db: AsyncSession, user_id: uuid.UUID, review_id: uuid.UUID) -> int:
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Review not found')
    await db.execute(delete(ReviewVote).where(ReviewVote.review_id == review_id, ReviewVote.user_id == user_id))
    new_count = await _recompute_helpful(db, review, review_id)
    await db.commit()
    return new_count
