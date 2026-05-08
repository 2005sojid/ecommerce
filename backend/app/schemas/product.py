import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=280)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    category_id: uuid.UUID
    image_url: str | None = None
    is_active: bool = True

class ProductCreate(ProductBase):
    initial_quantity: int = Field(ge=0, default=0)

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    category_id: uuid.UUID | None = None
    image_url: str | None = None
    is_active: bool | None = None

class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    price: Decimal
    category_id: uuid.UUID
    image_url: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProductDetail(ProductOut):
    available_quantity: int = 0
    average_rating: float | None = None
    reviews_count: int = 0
