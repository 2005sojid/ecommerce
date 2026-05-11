import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Settlement(Base):
    __tablename__ = 'settlements'
    __table_args__ = (
        UniqueConstraint('seller_id', 'settlement_date', name='uq_settlement_seller_date'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False, index=True)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    gross_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    fees: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    net_payout: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    order_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
