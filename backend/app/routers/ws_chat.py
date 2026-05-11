import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from app.database import async_session
from app.models.conversation import Conversation
from app.models.seller import Seller
from app.models.user import User
from app.routers.ws import manager
from app.services.auth_service import decode_token

logger = logging.getLogger(__name__)
router = APIRouter()


async def _user_from_token(token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get('type') != 'access':
            return None
        sub = payload.get('sub')
        if not sub:
            return None
    except JWTError:
        return None
    async with async_session() as db:
        user = await db.get(User, uuid.UUID(sub))
        return user if user and user.is_active else None


@router.websocket('/ws/chat/{conversation_id}')
async def chat_conversation(websocket: WebSocket, conversation_id: str, token: str | None = Query(default=None)) -> None:
    user = await _user_from_token(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason='Invalid conversation id')
        return
    async with async_session() as db:
        conv = await db.get(Conversation, conv_uuid)
        if conv is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason='Conversation not found')
            return
        seller = await db.get(Seller, conv.seller_id)
        if seller is None or (user.id != conv.buyer_id and user.id != seller.user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason='Forbidden')
            return
    channel = f'chat:{conversation_id}'
    await manager.connect(channel, websocket)
    await websocket.send_json({
        'event': 'subscribed',
        'conversation_id': conversation_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)
