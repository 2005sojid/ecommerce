import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Coupon(Base):
    __tablename__ = 'coupons'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default='platform')
    seller_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('sellers.id', ondelete='SET NULL'), nullable=True, index=True)
    min_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CouponUsage(Base):
    __tablename__ = 'coupon_usages'
    __table_args__ = (UniqueConstraint('coupon_id', 'user_id', 'order_id', name='uq_coupon_usage'),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coupon_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('coupons.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    order_id: Mapped[str | None] = mapped_column(String(20), ForeignKey('orders.id', ondelete='SET NULL'), nullable=True, index=True)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
