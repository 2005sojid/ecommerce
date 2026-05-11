import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.order import OrderStatus

class CheckoutRequest(BaseModel):
    shipping_address: str = Field(min_length=5)
    coupon_code: str | None = None

class OrderItemOut(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    variant_id: uuid.UUID | None = None
    variant_name: str | None = None

    class Config:
        from_attributes = True

class OrderEventOut(BaseModel):
    from_status: str | None
    to_status: str
    event_metadata: dict | None = None
    timestamp: datetime

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: str
    user_id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    shipping_address: str
    created_at: datetime
    tracking_number: str | None = None

    class Config:
        from_attributes = True

class OrderDetail(OrderOut):
    items: list[OrderItemOut] = []
    events: list[OrderEventOut] = []

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    reason: str | None = None
    tracking_number: str | None = None
