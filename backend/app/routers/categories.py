import uuid
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func
from app.cache.redis_cache import cache_delete, cache_get, cache_set
from app.deps import AdminUser, DBSession
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryNode, CategoryOut
from app.schemas.common import Page
from app.schemas.product import ProductOut
CATEGORIES_TREE_KEY = 'categories:tree'
CATEGORIES_TREE_TTL = 30 * 60
router = APIRouter(prefix='/api/categories', tags=['Categories'])

def _build_tree(categories: list[Category]) -> list[CategoryNode]:
    by_id: dict[uuid.UUID, CategoryNode] = {c.id: CategoryNode(id=c.id, name=c.name, slug=c.slug, parent_id=c.parent_id) for c in categories}
    roots: list[CategoryNode] = []
    for c in categories:
        node = by_id[c.id]
        if c.parent_id and c.parent_id in by_id:
            by_id[c.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots

@router.get('', response_model=list[CategoryNode])
async def list_categories(db: DBSession) -> list[CategoryNode]:
    cached_payload = await cache_get(CATEGORIES_TREE_KEY)
    if cached_payload is not None:
        return [CategoryNode.model_validate(node) for node in cached_payload]
    rows = (await db.execute(select(Category).order_by(Category.name))).scalars().all()
    tree = _build_tree(list(rows))
    await cache_set(CATEGORIES_TREE_KEY, [n.model_dump(mode='json') for n in tree], ttl=CATEGORIES_TREE_TTL)
    return tree

@router.get('/{category_id}/products', response_model=Page[ProductOut])
async def category_products(category_id: uuid.UUID, db: DBSession, page: Annotated[int, Query(ge=1)]=1, per_page: Annotated[int, Query(ge=1, le=100)]=20) -> Page[ProductOut]:
    where = (Product.category_id == category_id) & Product.is_active.is_(True)
    total = (await db.execute(select(func.count()).select_from(Product).where(where))).scalar_one()
    rows = (await db.execute(select(Product).where(where).order_by(Product.created_at.desc()).offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return Page[ProductOut](items=[ProductOut.model_validate(p) for p in rows], total=total, page=page, per_page=per_page)

@router.post('', response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, _: AdminUser, db: DBSession) -> CategoryOut:
    existing = (await db.execute(select(Category).where(Category.slug == payload.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, 'Category slug already exists')
    cat = Category(id=uuid.uuid4(), name=payload.name, slug=payload.slug, parent_id=payload.parent_id)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    await cache_delete(CATEGORIES_TREE_KEY)
    return CategoryOut.model_validate(cat)
