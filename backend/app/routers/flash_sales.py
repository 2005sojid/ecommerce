import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.cache.redis_cache import redis_client
from app.deps import AdminUser, CurrentUser, DBSession
from app.models.flash_sale import FlashSale
from app.schemas.flash_sale import FlashSaleClaimResponse, FlashSaleCreate, FlashSaleOut
from app.schemas.order import CheckoutRequest
from app.services.flash_sale_service import FlashSaleService
router = APIRouter(prefix='/api/flash-sales', tags=['Flash Sales'])
_service = FlashSaleService(redis_client)

@router.post('', response_model=FlashSaleOut, status_code=status.HTTP_201_CREATED)
async def create_flash_sale(payload: FlashSaleCreate, _: AdminUser, db: DBSession) -> FlashSaleOut:
    if payload.end_at <= payload.start_at:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'end_at must be after start_at')
    sale = FlashSale(id=uuid.uuid4(), product_id=payload.product_id, sale_price=payload.sale_price, original_price=payload.original_price, start_at=payload.start_at, end_at=payload.end_at, initial_stock=payload.initial_stock, remaining_stock=payload.initial_stock, is_active=True)
    db.add(sale)
    await db.commit()
    await db.refresh(sale)
    await _service.preload_stock(sale)
    return FlashSaleOut.model_validate(sale)

@router.get('/active', response_model=list[FlashSaleOut])
async def active_flash_sales(db: DBSession) -> list[FlashSaleOut]:
    now = datetime.now(timezone.utc)
    rows = (await db.execute(select(FlashSale).where(FlashSale.is_active.is_(True), FlashSale.start_at <= now, FlashSale.end_at >= now))).scalars().all()
    return [FlashSaleOut.model_validate(s) for s in rows]

@router.post('/{sale_id}/claim', response_model=FlashSaleClaimResponse)
async def claim(sale_id: uuid.UUID, payload: CheckoutRequest, user: CurrentUser, db: DBSession) -> FlashSaleClaimResponse:
    (order, remaining) = await _service.claim(sale_id, user.id, payload.shipping_address, db)
    return FlashSaleClaimResponse(sale_id=sale_id, order_id=order.id, remaining_stock=remaining)
