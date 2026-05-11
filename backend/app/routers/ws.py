import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from app.cache.redis_cache import redis_client
from app.database import async_session
from app.models.order import Order
from app.models.user import User, UserRole
from app.services.auth_service import decode_token
logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis = None
        self._pubsub = None
        self._pubsub_task: asyncio.Task | None = None

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[channel].add(websocket)
        logger.info('ws connected channel=%s total=%d', channel, len(self._connections[channel]))

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        self._connections[channel].discard(websocket)
        if not self._connections[channel]:
            self._connections.pop(channel, None)

    async def _broadcast_local(self, channel: str, message: dict) -> None:
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

    async def broadcast(self, channel: str, message: dict) -> None:
        if self._redis is not None:
            try:
                await self._redis.publish(f'ws:{channel}', json.dumps(message, default=str))
                return
            except Exception as exc:
                logger.warning('ws redis publish failed: %s', exc)
        await self._broadcast_local(channel, message)

    async def _pubsub_loop(self) -> None:
        pubsub = self._redis.pubsub()
        self._pubsub = pubsub
        await pubsub.psubscribe('ws:*')
        try:
            async for msg in pubsub.listen():
                if msg is None or msg.get('type') != 'pmessage':
                    continue
                chan = msg['channel'].decode() if isinstance(msg['channel'], bytes) else msg['channel']
                data = msg['data']
                if isinstance(data, bytes):
                    data = data.decode()
                try:
                    payload = json.loads(data)
                except Exception:
                    continue
                local_chan = chan.removeprefix('ws:')
                await self._broadcast_local(local_chan, payload)
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await pubsub.punsubscribe('ws:*')
                await pubsub.close()
            except Exception:
                pass

    async def start_pubsub(self, redis_client) -> None:
        self._redis = redis_client
        if self._pubsub_task is None or self._pubsub_task.done():
            self._pubsub_task = asyncio.create_task(self._pubsub_loop())

    async def stop_pubsub(self) -> None:
        if self._pubsub_task is not None:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except Exception:
                pass
            self._pubsub_task = None
        if self._pubsub is not None:
            try:
                await self._pubsub.punsubscribe('ws:*')
                await self._pubsub.close()
            except Exception:
                pass
            self._pubsub = None
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

@router.websocket('/ws/user')
async def user_channel(websocket: WebSocket, token: str | None=Query(default=None)) -> None:
    user = await _user_from_token(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    channel = f'user:{user.id}'
    await manager.connect(channel, websocket)
    await websocket.send_json({'event': 'subscribed', 'user_id': str(user.id), 'timestamp': datetime.now(timezone.utc).isoformat()})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)

async def broadcast_user_notification(user_id: uuid.UUID, payload: dict) -> None:
    await manager.broadcast(f'user:{user_id}', payload)
