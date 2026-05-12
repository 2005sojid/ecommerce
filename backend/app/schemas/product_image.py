import uuid
from datetime import datetime
from pydantic import BaseModel


class ProductImageOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    url: str
    alt: str | None
    position: int
    created_at: datetime

    class Config:
        from_attributes = True
