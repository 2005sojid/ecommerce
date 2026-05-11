from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class VariantBase(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    variant_name: str = Field(min_length=1, max_length=150)
    attributes: dict[str, Any] | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock_quantity: int = Field(ge=0, default=0)
    is_active: bool = True

class VariantCreate(VariantBase):
    pass

class VariantUpdate(BaseModel):
    sku: str | None = None
    variant_name: str | None = None
    attributes: dict[str, Any] | None = None
    price: Decimal | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

class VariantOut(VariantBase):
    id: UUID
    product_id: UUID
    reserved_quantity: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
