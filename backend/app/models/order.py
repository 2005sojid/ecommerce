import enum
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Text, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class OrderStatus(str, enum.Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    processing = 'processing'
    packed = 'packed'
    shipped = 'shipped'
    delivered = 'delivered'
    cancelled = 'cancelled'

class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus, name='order_status'), default=OrderStatus.pending, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    events = relationship('OrderEvent', back_populates='order', cascade='all, delete-orphan')

class OrderItem(Base):
    __tablename__ = 'order_items'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[str] = mapped_column(String(20), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='order_items')
