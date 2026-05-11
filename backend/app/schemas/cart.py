import uuid
from decimal import Decimal
from pydantic import BaseModel, Field

class CartItemAdd(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)
    variant_id: uuid.UUID | None = None

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)

class CartItemOut(BaseModel):
    product_id: uuid.UUID
    name: str
    price: Decimal
    quantity: int
    line_total: Decimal
    variant_id: uuid.UUID | None = None
    variant_name: str | None = None
    variant_sku: str | None = None

class CartOut(BaseModel):
    items: list[CartItemOut]
    total: Decimal
