import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_user_id: uuid.UUID
    body: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    id: uuid.UUID
    buyer_id: uuid.UUID
    seller_id: uuid.UUID
    seller_store_name: str | None = None
    buyer_name: str | None = None
    last_message: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StartConversation(BaseModel):
    seller_id: uuid.UUID


class SendMessage(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
