from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class AddressBase(BaseModel):
    label: str | None = Field(default=None, max_length=50)
    recipient_name: str = Field(min_length=1, max_length=150)
    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=2, max_length=2)
    phone: str | None = Field(default=None, max_length=30)
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    label: str | None = None
    recipient_name: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    phone: str | None = None
    is_default: bool | None = None

class AddressOut(AddressBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
