import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class SettlementOut(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    settlement_date: date
    gross_revenue: Decimal
    fees: Decimal
    net_payout: Decimal
    order_count: int
    created_at: datetime

    class Config:
        from_attributes = True
