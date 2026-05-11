import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class UserRole(str, enum.Enum):
    customer = 'customer'
    admin = 'admin'
    seller = 'seller'

class User(Base):
    __tablename__ = 'users'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name='user_role'), default=UserRole.customer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='user', cascade='all, delete-orphan')
