import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any
from sqlalchemy import String, Numeric, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ProductVariant(Base):
    __tablename__ = 'product_variants'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    variant_name: Mapped[str] = mapped_column(String(150), nullable=False)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    product = relationship('Product', back_populates='variants')
