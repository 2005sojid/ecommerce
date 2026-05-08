import uuid
from decimal import Decimal
from pydantic import BaseModel, Field

class CartItemAdd(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(gt=0)

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)

class CartItemOut(BaseModel):
    product_id: uuid.UUID
    name: str
    price: Decimal
    quantity: int
    line_total: Decimal

class CartOut(BaseModel):
    items: list[CartItemOut]
    total: Decimal
