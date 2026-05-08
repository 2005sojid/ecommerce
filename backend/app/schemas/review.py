import uuid
from datetime import datetime
from pydantic import BaseModel, Field

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

    class Config:
        from_attributes = True
