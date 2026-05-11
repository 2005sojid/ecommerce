import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ReviewCreate(BaseModel):
    product_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = None

class ReviewOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    rating: int
    comment: str | None
    created_at: datetime
    is_approved: bool
    seller_response: str | None = None
    seller_response_at: datetime | None = None
    helpful_count: int = 0
    verified_purchase: bool = False

    class Config:
        from_attributes = True


class ReviewRespond(BaseModel):
    response: str


class ReviewModerate(BaseModel):
    is_approved: bool


class ReviewVoteIn(BaseModel):
    vote: int

    @field_validator('vote')
    @classmethod
    def _check_vote(cls, v: int) -> int:
        if v not in (-1, 1):
            raise ValueError('vote must be -1 or 1')
        return v
