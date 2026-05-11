import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class CouponBase(BaseModel):
    code: str
    discount_type: str  # 'percent' | 'fixed'
    discount_value: Decimal
    scope: str = 'platform'  # 'platform' | 'seller'
    seller_id: uuid.UUID | None = None
    min_order_amount: Decimal | None = None
    max_uses: int | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool = True


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    code: str | None = None
    discount_type: str | None = None
    discount_value: Decimal | None = None
    scope: str | None = None
    seller_id: uuid.UUID | None = None
    min_order_amount: Decimal | None = None
    max_uses: int | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    is_active: bool | None = None


class CouponOut(CouponBase):
    id: uuid.UUID
    used_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CouponValidate(BaseModel):
    code: str
    order_total: Decimal


class CouponValidationResult(BaseModel):
    valid: bool
    coupon_id: uuid.UUID | None = None
    discount_amount: Decimal = Decimal('0')
    message: str
