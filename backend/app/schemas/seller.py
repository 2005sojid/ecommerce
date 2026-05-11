from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import ProductBase


class SellerBase(BaseModel):
    store_name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=180)
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    is_verified: bool = False
    is_active: bool = True


class SellerCreate(BaseModel):
    store_name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    user_id: UUID | None = None
    slug: str | None = None
    is_verified: bool = False
    is_active: bool = True


class SellerUpdate(BaseModel):
    store_name: str | None = None
    slug: str | None = None
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    is_verified: bool | None = None
    is_active: bool | None = None


class SellerOut(BaseModel):
    id: UUID
    user_id: UUID
    store_name: str
    slug: str
    description: str | None
    logo_url: str | None
    banner_url: str | None
    is_verified: bool
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SellerProductCreate(ProductBase):
    initial_quantity: int = Field(ge=0, default=0)
