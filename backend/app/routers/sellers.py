import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from app.deps import CurrentUser, DBSession
from app.models.product import Product
from app.models.seller import Seller
from app.models.user import UserRole
from app.schemas.common import Page
from app.schemas.product import ProductOut, ProductUpdate
from app.schemas.seller import SellerCreate, SellerOut, SellerProductCreate, SellerUpdate
from app.services import seller_service


async def get_current_seller(user: CurrentUser, db: DBSession) -> Seller:
    if user.role != UserRole.seller:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Seller role required')
    seller = (await db.execute(select(Seller).where(Seller.user_id == user.id))).scalar_one_or_none()
    if seller is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Seller profile not found')
    return seller


SellerUser = Annotated[Seller, Depends(get_current_seller)]

router = APIRouter(prefix='/api/sellers', tags=['Sellers'])


@router.post('/register', response_model=SellerOut, status_code=status.HTTP_201_CREATED)
async def register(payload: SellerCreate, user: CurrentUser, db: DBSession) -> SellerOut:
    seller = await seller_service.register_seller(db, user, payload)
    return SellerOut.model_validate(seller)


@router.get('/me', response_model=SellerOut)
async def get_me(seller: SellerUser) -> SellerOut:
    return SellerOut.model_validate(seller)


@router.patch('/me', response_model=SellerOut)
async def update_me(payload: SellerUpdate, seller: SellerUser, db: DBSession) -> SellerOut:
    updated = await seller_service.update_profile(db, seller, payload)
    return SellerOut.model_validate(updated)


@router.get('/me/products', response_model=Page[ProductOut])
async def my_products(
    seller: SellerUser,
    db: DBSession,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[ProductOut]:
    items, total = await seller_service.list_seller_products(db, seller.id, page, per_page)
    return Page[ProductOut](items=[ProductOut.model_validate(p) for p in items], total=total, page=page, per_page=per_page)


@router.post('/me/products', response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_my_product(payload: SellerProductCreate, seller: SellerUser, db: DBSession) -> ProductOut:
    product = await seller_service.create_seller_product(db, seller, payload)
    return ProductOut.model_validate(product)


@router.patch('/me/products/{product_id}', response_model=ProductOut)
async def update_my_product(product_id: uuid.UUID, payload: ProductUpdate, seller: SellerUser, db: DBSession) -> ProductOut:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    if product.seller_id != seller.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Not your product')
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return ProductOut.model_validate(product)


@router.delete('/me/products/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_product(product_id: uuid.UUID, seller: SellerUser, db: DBSession) -> Response:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    if product.seller_id != seller.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Not your product')
    product.is_active = False
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/me/orders')
async def my_orders(
    seller: SellerUser,
    db: DBSession,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, Any]:
    items, total = await seller_service.list_seller_orders(db, seller.id, page, per_page)
    return {
        'items': [
            {
                'id': o.id,
                'status': o.status.value if hasattr(o.status, 'value') else str(o.status),
                'total_amount': float(o.total_amount),
                'created_at': o.created_at.isoformat() if o.created_at else None,
            }
            for o in items
        ],
        'total': total,
        'page': page,
        'per_page': per_page,
    }


@router.get('/me/analytics')
async def my_analytics(seller: SellerUser, db: DBSession) -> dict[str, Any]:
    return await seller_service.seller_analytics(db, seller.id)


@router.get('/{slug}', response_model=SellerOut)
async def get_public_seller(slug: str, db: DBSession) -> SellerOut:
    seller = await seller_service.get_by_slug(db, slug)
    if seller is None or not seller.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Seller not found')
    return SellerOut.model_validate(seller)


@router.get('/{slug}/products', response_model=Page[ProductOut])
async def public_seller_products(
    slug: str,
    db: DBSession,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[ProductOut]:
    seller = await seller_service.get_by_slug(db, slug)
    if seller is None or not seller.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Seller not found')
    items, total = await seller_service.list_active_seller_products(db, seller.id, page, per_page)
    return Page[ProductOut](items=[ProductOut.model_validate(p) for p in items], total=total, page=page, per_page=per_page)
