import logging
import uuid
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.errors import MeilisearchApiError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import settings
from app.models.category import Category
from app.models.product import Product
logger = logging.getLogger(__name__)
INDEX_NAME = 'products'

def _to_doc(product: Product, category_name: str | None=None) -> dict:
    return {'id': str(product.id), 'name': product.name, 'slug': product.slug, 'description': product.description or '', 'price': float(product.price), 'category_id': str(product.category_id), 'category_name': category_name or '', 'image_url': product.image_url, 'is_active': product.is_active, 'created_at': int(product.created_at.timestamp()) if product.created_at else 0}

class SearchService:

    def __init__(self) -> None:
        self.client = AsyncClient(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)

    @property
    def index(self):
        return self.client.index(INDEX_NAME)

    async def init_index(self) -> None:
        try:
            await self.client.create_index(INDEX_NAME, primary_key='id')
        except MeilisearchApiError as exc:
            if 'index_already_exists' not in str(exc):
                logger.warning('create_index failed: %s', exc)
        await self.index.update_searchable_attributes(['name', 'description', 'category_name'])
        await self.index.update_filterable_attributes(['category_id', 'price', 'is_active'])
        await self.index.update_sortable_attributes(['price', 'created_at'])

    async def index_product(self, product: Product, category_name: str | None=None) -> None:
        await self.index.add_documents([_to_doc(product, category_name)])

    async def delete_product(self, product_id: uuid.UUID) -> None:
        await self.index.delete_document(str(product_id))

    async def search(self, query: str, category_id: uuid.UUID | None=None, min_price: float | None=None, max_price: float | None=None, page: int=1, per_page: int=20, sort_by: str | None=None, sort_order: str='desc') -> dict:
        filters: list[str] = ['is_active = true']
        if category_id is not None:
            filters.append(f'category_id = "{category_id}"')
        if min_price is not None:
            filters.append(f'price >= {min_price}')
        if max_price is not None:
            filters.append(f'price <= {max_price}')
        sort = None
        if sort_by in ('price', 'created_at'):
            sort = [f'{sort_by}:{sort_order}']
        result = await self.index.search(query, filter=' AND '.join(filters) if filters else None, offset=(page - 1) * per_page, limit=per_page, sort=sort)
        return {'hits': result.hits, 'estimated_total_hits': result.estimated_total_hits or 0}

    async def reindex_all(self, db: AsyncSession) -> int:
        rows = (await db.execute(select(Product).options(selectinload(Product.category)))).scalars().all()
        if not rows:
            return 0
        docs = [_to_doc(p, p.category.name if p.category else None) for p in rows]
        await self.index.add_documents(docs)
        return len(docs)

    async def close(self) -> None:
        await self.client.aclose()
search_service = SearchService()

async def fetch_category_name(db: AsyncSession, category_id: uuid.UUID) -> str | None:
    cat = await db.get(Category, category_id)
    return cat.name if cat else None
