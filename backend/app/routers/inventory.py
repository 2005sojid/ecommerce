import uuid
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.deps import AdminUser, DBSession
from app.models.inventory import Inventory
from app.routers.ws import broadcast_inventory_change
router = APIRouter(prefix='/api/inventory', tags=['Inventory'])

@router.get('/{product_id}')
async def get_inventory(product_id: uuid.UUID, _: AdminUser, db: DBSession) -> dict:
    inv = (await db.execute(select(Inventory).where(Inventory.product_id == product_id))).scalar_one_or_none()
    if inv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Inventory not found')
    return {'product_id': str(inv.product_id), 'quantity': inv.quantity, 'reserved': inv.reserved, 'available': inv.quantity - inv.reserved, 'warehouse_location': inv.warehouse_location}

@router.patch('/{product_id}')
async def adjust_inventory(product_id: uuid.UUID, delta: int, _: AdminUser, db: DBSession) -> dict:
    inv = (await db.execute(select(Inventory).where(Inventory.product_id == product_id))).scalar_one_or_none()
    if inv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Inventory not found')
    new_qty = inv.quantity + delta
    if new_qty < 0:
        raise HTTPException(status.HTTP_409_CONFLICT, 'Resulting quantity would be negative')
    inv.quantity = new_qty
    await db.commit()
    await broadcast_inventory_change(product_id, inv.quantity, source='admin_adjust')
    return {'product_id': str(product_id), 'quantity': inv.quantity, 'reserved': inv.reserved}
