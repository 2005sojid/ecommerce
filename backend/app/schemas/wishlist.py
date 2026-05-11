import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

class WishlistAdd(BaseModel):
    product_id: uuid.UUID

class WishlistItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    product_price: Decimal
    product_image_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True
