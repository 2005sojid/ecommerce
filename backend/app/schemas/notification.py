import uuid
from datetime import datetime
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    body: str | None
    link: str | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCount(BaseModel):
    count: int
