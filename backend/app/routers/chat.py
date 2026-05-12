import uuid
from fastapi import APIRouter, Query, status
from app.deps import CurrentUser, CustomerUser, DBSession
from app.schemas.chat import ConversationOut, MessageOut, SendMessage, StartConversation
from app.services import chat_service

router = APIRouter(prefix='/api/chat', tags=['Chat'])


@router.post('/conversations', status_code=status.HTTP_201_CREATED, response_model=ConversationOut)
async def start_conversation(payload: StartConversation, user: CustomerUser, db: DBSession) -> ConversationOut:
    conv = await chat_service.get_or_create_conversation(db, user.id, payload.seller_id)
    convs = await chat_service.list_conversations_for_user(db, user.id)
    for c in convs:
        if c.id == conv.id:
            return c
    return ConversationOut(
        id=conv.id,
        buyer_id=conv.buyer_id,
        seller_id=conv.seller_id,
        created_at=conv.created_at,
    )


@router.get('/conversations', response_model=list[ConversationOut])
async def list_conversations(user: CurrentUser, db: DBSession) -> list[ConversationOut]:
    return await chat_service.list_conversations_for_user(db, user.id)


@router.get('/conversations/{conversation_id}/messages')
async def list_messages(conversation_id: uuid.UUID, user: CurrentUser, db: DBSession, page: int = Query(1, ge=1), per_page: int = Query(50, ge=1, le=200)) -> dict:
    items, total = await chat_service.list_messages(db, conversation_id, user.id, page, per_page)
    return {'items': [MessageOut.model_validate(m) for m in items], 'total': total, 'page': page, 'per_page': per_page}


@router.post('/conversations/{conversation_id}/messages', status_code=status.HTTP_201_CREATED, response_model=MessageOut)
async def send_message(conversation_id: uuid.UUID, payload: SendMessage, user: CurrentUser, db: DBSession) -> MessageOut:
    msg = await chat_service.send_message(db, conversation_id, user.id, payload.body)
    return MessageOut.model_validate(msg)
