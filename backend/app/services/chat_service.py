import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Message
from app.models.seller import Seller
from app.models.user import User
from app.routers.ws import broadcast_user_notification, manager as ws_manager
from app.schemas.chat import ConversationOut


async def get_or_create_conversation(db: AsyncSession, buyer_id: uuid.UUID, seller_id: uuid.UUID) -> Conversation:
    seller = await db.get(Seller, seller_id)
    if seller is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Seller not found')
    existing = await db.scalar(select(Conversation).where(Conversation.buyer_id == buyer_id, Conversation.seller_id == seller_id))
    if existing is not None:
        return existing
    conv = Conversation(id=uuid.uuid4(), buyer_id=buyer_id, seller_id=seller_id)
    db.add(conv)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing = await db.scalar(select(Conversation).where(Conversation.buyer_id == buyer_id, Conversation.seller_id == seller_id))
        if existing is None:
            raise HTTPException(status.HTTP_409_CONFLICT, 'Could not create conversation')
        return existing
    await db.refresh(conv)
    return conv


async def _membership(db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID) -> tuple[Conversation, Seller]:
    conv = await db.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Conversation not found')
    seller = await db.get(Seller, conv.seller_id)
    if seller is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Seller not found')
    if user_id != conv.buyer_id and user_id != seller.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Not a member of this conversation')
    return conv, seller


async def list_conversations_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[ConversationOut]:
    stmt = (
        select(Conversation, Seller, User)
        .join(Seller, Seller.id == Conversation.seller_id)
        .join(User, User.id == Conversation.buyer_id)
        .where(or_(Conversation.buyer_id == user_id, Seller.user_id == user_id))
        .order_by(func.coalesce(Conversation.updated_at, Conversation.created_at).desc())
    )
    rows = (await db.execute(stmt)).all()
    out: list[ConversationOut] = []
    for conv, seller, buyer in rows:
        last_msg_row = (await db.execute(
            select(Message.body, Message.created_at)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )).first()
        last_body = last_msg_row[0] if last_msg_row else None
        last_at = last_msg_row[1] if last_msg_row else None
        unread = await db.scalar(
            select(func.count(Message.id))
            .where(Message.conversation_id == conv.id, Message.sender_user_id != user_id, Message.is_read == False)
        ) or 0
        out.append(ConversationOut(
            id=conv.id,
            buyer_id=conv.buyer_id,
            seller_id=conv.seller_id,
            seller_store_name=seller.store_name,
            buyer_name=buyer.name,
            last_message=last_body,
            last_message_at=last_at,
            unread_count=int(unread),
            created_at=conv.created_at,
        ))
    return out


async def list_messages(db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID, page: int, per_page: int) -> tuple[list[Message], int]:
    await _membership(db, conversation_id, user_id)
    await db.execute(
        update(Message)
        .where(Message.conversation_id == conversation_id, Message.sender_user_id != user_id, Message.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    total = await db.scalar(select(func.count(Message.id)).where(Message.conversation_id == conversation_id)) or 0
    offset = (page - 1) * per_page
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(per_page)
        .offset(offset)
    )
    items = list((await db.scalars(stmt)).all())
    return items, int(total)


async def send_message(db: AsyncSession, conversation_id: uuid.UUID, sender_user_id: uuid.UUID, body: str) -> Message:
    conv, seller = await _membership(db, conversation_id, sender_user_id)
    msg = Message(id=uuid.uuid4(), conversation_id=conversation_id, sender_user_id=sender_user_id, body=body, is_read=False)
    db.add(msg)
    await db.execute(update(Conversation).where(Conversation.id == conversation_id).values(updated_at=func.now()))
    await db.commit()
    await db.refresh(msg)
    other_user_id = seller.user_id if sender_user_id == conv.buyer_id else conv.buyer_id
    payload = {
        'event': 'new_message',
        'id': str(msg.id),
        'conversation_id': str(conversation_id),
        'body': body,
        'sender_user_id': str(sender_user_id),
        'is_read': False,
        'created_at': msg.created_at.isoformat() if msg.created_at else datetime.now(timezone.utc).isoformat(),
    }
    await ws_manager.broadcast(f'chat:{conversation_id}', payload)
    await broadcast_user_notification(other_user_id, payload)
    return msg
