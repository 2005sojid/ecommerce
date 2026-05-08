import logging
import uuid
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, and_
from app.cache.redis_cache import cache_delete, cache_get, cache_set
from app.deps import AdminUser, DBSession
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.review import Review
from app.schemas.common import Page
from app.schemas.product import ProductCreate, ProductDetail, ProductOut, ProductUpdate
from app.schemas.review import ReviewOut
from app.services.notification_service import publish_event
from app.services.search_service import search_service
logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/products', tags=['Products'])

async def _search_via_meili(db: DBSession, query: str, page: int, per_page: int, category_id: uuid.UUID | None, min_price: Decimal | None, max_price: Decimal | None, sort_by: str, sort_order: str) -> Page[ProductOut]:
    res = await search_service.search(query=query, category_id=category_id, min_price=float(min_price) if min_price is not None else None, max_price=float(max_price) if max_price is not None else None, page=page, per_page=per_page, sort_by=sort_by if sort_by in ('price', 'created_at') else None, sort_order=sort_order)
    ids = [uuid.UUID(h['id']) for h in res['hits']]
    if not ids:
        return Page[ProductOut](items=[], total=res['estimated_total_hits'], page=page, per_page=per_page)
    rows = (await db.execute(select(Product).where(Product.id.in_(ids)))).scalars().all()
    by_id = {p.id: p for p in rows}
    ordered = [by_id[i] for i in ids if i in by_id]
    return Page[ProductOut](items=[ProductOut.model_validate(p) for p in ordered], total=res['estimated_total_hits'], page=page, per_page=per_page)

@router.get('', response_model=Page[ProductOut])
async def list_products(db: DBSession, page: Annotated[int, Query(ge=1)]=1, per_page: Annotated[int, Query(ge=1, le=100)]=20, category_id: uuid.UUID | None=None, min_price: Decimal | None=None, max_price: Decimal | None=None, search: str | None=None, sort_by: Annotated[str, Query(pattern='^(price|created_at|name)$')]='created_at', sort_order: Annotated[str, Query(pattern='^(asc|desc)$')]='desc') -> Page[ProductOut]:
    if search:
        try:
            return await _search_via_meili(db, search, page, per_page, category_id, min_price, max_price, sort_by, sort_order)
        except Exception as exc:
            logger.warning('Meilisearch search failed, falling back to SQL: %s', exc)
    conditions = [Product.is_active.is_(True)]
    if category_id is not None:
        conditions.append(Product.category_id == category_id)
    if min_price is not None:
        conditions.append(Product.price >= min_price)
    if max_price is not None:
        conditions.append(Product.price <= max_price)
    if search:
        like = f'%{search}%'
        conditions.append(Product.name.ilike(like) | Product.description.ilike(like))
    where = and_(*conditions)
    total = (await db.execute(select(func.count()).select_from(Product).where(where))).scalar_one()
    sort_col = {'price': Product.price, 'created_at': Product.created_at, 'name': Product.name}[sort_by]
    sort_col = sort_col.asc() if sort_order == 'asc' else sort_col.desc()
    rows = (await db.execute(select(Product).where(where).order_by(sort_col).offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return Page[ProductOut](items=[ProductOut.model_validate(p) for p in rows], total=total, page=page, per_page=per_page)

@router.get('/{product_id}', response_model=ProductDetail)
async def get_product(product_id: uuid.UUID, db: DBSession) -> ProductDetail:
    cache_key = f'product:{product_id}'
    cached_payload = await cache_get(cache_key)
    if cached_payload is not None:
        return ProductDetail.model_validate(cached_payload)
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    inv = (await db.execute(select(Inventory).where(Inventory.product_id == product_id))).scalar_one_or_none()
    available = inv.quantity - inv.reserved if inv else 0
    rating_key = f'product:{product_id}:avg_rating'
    rating_payload = await cache_get(rating_key)
    if rating_payload is None:
        rating_row = (await db.execute(select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product_id))).one()
        rating_payload = {'avg': float(rating_row[0]) if rating_row[0] is not None else None, 'count': int(rating_row[1] or 0)}
        await cache_set(rating_key, rating_payload, ttl=600)
    detail = ProductDetail.model_validate(product)
    detail.available_quantity = max(available, 0)
    detail.average_rating = rating_payload['avg']
    detail.reviews_count = rating_payload['count']
    await cache_set(cache_key, detail.model_dump(mode='json'), ttl=300)
    return detail

@router.post('', response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, _: AdminUser, db: DBSession) -> ProductOut:
    product = Product(id=uuid.uuid4(), name=payload.name, slug=payload.slug, description=payload.description, price=payload.price, category_id=payload.category_id, image_url=payload.image_url, is_active=payload.is_active)
    db.add(product)
    db.add(Inventory(id=uuid.uuid4(), product_id=product.id, quantity=payload.initial_quantity, reserved=0))
    await db.commit()
    await db.refresh(product)
    await publish_event('product.created', {'product_id': str(product.id)})
    return ProductOut.model_validate(product)

@router.put('/{product_id}', response_model=ProductOut)
async def update_product(product_id: uuid.UUID, payload: ProductUpdate, _: AdminUser, db: DBSession) -> ProductOut:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    for (field, value) in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    await cache_delete(f'product:{product.id}')
    await publish_event('product.updated', {'product_id': str(product.id)})
    return ProductOut.model_validate(product)

@router.delete('/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: uuid.UUID, _: AdminUser, db: DBSession) -> None:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    product.is_active = False
    await db.commit()
    await cache_delete(f'product:{product_id}', f'product:{product_id}:avg_rating')
    await publish_event('product.deleted', {'product_id': str(product_id)})

@router.get('/{product_id}/reviews', response_model=Page[ReviewOut])
async def list_product_reviews(product_id: uuid.UUID, db: DBSession, page: Annotated[int, Query(ge=1)]=1, per_page: Annotated[int, Query(ge=1, le=100)]=20) -> Page[ReviewOut]:
    where = Review.product_id == product_id
    total = (await db.execute(select(func.count()).select_from(Review).where(where))).scalar_one()
    rows = (await db.execute(select(Review).where(where).order_by(Review.created_at.desc()).offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return Page[ReviewOut](items=[ReviewOut.model_validate(r) for r in rows], total=total, page=page, per_page=per_page)
