import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class FlashSaleCreate(BaseModel):
    product_id: uuid.UUID
    sale_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    original_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    start_at: datetime
    end_at: datetime
    initial_stock: int = Field(gt=0)


class FlashSaleOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    sale_price: Decimal
    original_price: Decimal
    start_at: datetime
    end_at: datetime
    initial_stock: int
    remaining_stock: int
    is_active: bool

    class Config:
        from_attributes = True


class FlashSaleClaimResponse(BaseModel):
    sale_id: uuid.UUID
    order_id: str
    remaining_stock: int
