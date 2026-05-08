import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from app.database import async_session
from app.models.order import Order
from app.models.user import User, UserRole
from app.services.auth_service import decode_token
logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[channel].add(websocket)
        logger.info('ws connected channel=%s total=%d', channel, len(self._connections[channel]))

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        self._connections[channel].discard(websocket)
        if not self._connections[channel]:
            self._connections.pop(channel, None)

    async def broadcast(self, channel: str, message: dict) -> None:
        sockets = list(self._connections.get(channel, ()))
        if not sockets:
            return
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(channel, ws)
manager = ConnectionManager()

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

@router.websocket('/ws/orders/{order_id}')
async def order_tracking(websocket: WebSocket, order_id: str, token: str | None=Query(default=None)) -> None:
    user = await _user_from_token(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    async with async_session() as db:
        order = await db.get(Order, order_id)
    if order is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason='Order not found')
        return
    if order.user_id != user.id and user.role != UserRole.admin:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason='Forbidden')
        return
    channel = f'order:{order_id}'
    await manager.connect(channel, websocket)
    await websocket.send_json({'event': 'subscribed', 'order_id': order_id, 'current_status': order.status.value, 'timestamp': datetime.now(timezone.utc).isoformat()})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)

@router.websocket('/ws/inventory')
async def inventory_dashboard(websocket: WebSocket, token: str | None=Query(default=None)) -> None:
    user = await _user_from_token(token)
    if user is None or user.role != UserRole.admin:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    channel = 'inventory'
    await manager.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)

async def broadcast_order_status(order_id: str, new_status: str, from_status: str | None=None) -> None:
    await manager.broadcast(f'order:{order_id}', {'event': 'status_changed', 'order_id': order_id, 'from_status': from_status, 'new_status': new_status, 'timestamp': datetime.now(timezone.utc).isoformat()})

async def broadcast_inventory_change(product_id: uuid.UUID, new_quantity: int, source: str='checkout') -> None:
    await manager.broadcast('inventory', {'event': 'stock_changed', 'product_id': str(product_id), 'new_quantity': new_quantity, 'source': source, 'timestamp': datetime.now(timezone.utc).isoformat()})
