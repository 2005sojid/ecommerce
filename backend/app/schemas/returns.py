import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class ReturnCreate(BaseModel):
    order_id: str
    reason: str


class ReturnUpdate(BaseModel):
    status: str | None = None
    refund_amount: Decimal | None = None
    admin_note: str | None = None


class ReturnOut(BaseModel):
    id: uuid.UUID
    order_id: str
    user_id: uuid.UUID
    status: str
    reason: str
    refund_amount: Decimal | None
    admin_note: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
