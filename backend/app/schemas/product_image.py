import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ProductImageOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    url: str
    alt: str | None
    position: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductImageCreate(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    alt: str | None = None
    position: int = 0
