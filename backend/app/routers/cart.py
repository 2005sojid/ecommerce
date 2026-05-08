import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.cache.redis_cache import redis_client
from app.deps import CurrentUser, DBSession
from app.models.inventory import Inventory
from app.models.product import Product
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartOut
from app.services.cart_service import CartService
router = APIRouter(prefix='/api/cart', tags=['Cart'])
_service = CartService(redis_client)

@router.get('', response_model=CartOut)
async def get_cart(user: CurrentUser, db: DBSession) -> CartOut:
    return await _service.get_cart(user.id, db)

@router.post('/items', response_model=CartOut, status_code=status.HTTP_201_CREATED)
async def add_item(payload: CartItemAdd, user: CurrentUser, db: DBSession) -> CartOut:
    product = await db.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    inv = (await db.execute(select(Inventory).where(Inventory.product_id == payload.product_id))).scalar_one_or_none()
    if inv is None or inv.quantity - inv.reserved < payload.quantity:
        raise HTTPException(status.HTTP_409_CONFLICT, 'Insufficient stock')
    await _service.add_item(user.id, payload.product_id, payload.quantity)
    return await _service.get_cart(user.id, db)

@router.patch('/items/{product_id}', response_model=CartOut)
async def update_item(product_id: uuid.UUID, payload: CartItemUpdate, user: CurrentUser, db: DBSession) -> CartOut:
    await _service.update_item(user.id, product_id, payload.quantity)
    return await _service.get_cart(user.id, db)

@router.delete('/items/{product_id}', response_model=CartOut)
async def remove_item(product_id: uuid.UUID, user: CurrentUser, db: DBSession) -> CartOut:
    await _service.remove_item(user.id, product_id)
    return await _service.get_cart(user.id, db)

@router.delete('', status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(user: CurrentUser) -> None:
    await _service.clear(user.id)
