import logging
import uuid
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select

from app.deps import CurrentUser, DBSession
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.seller import Seller
from app.models.user import UserRole
from app.schemas.product_image import ProductImageOut
from app.services.storage_service import storage_service

router = APIRouter(prefix='/api/products', tags=['ProductImages'])

logger = logging.getLogger(__name__)

# 5 MB hard cap
MAX_IMAGE_BYTES = 5 * 1024 * 1024

# Allowed content types and their canonical extension
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
    'image/gif': '.gif',
}


async def _assert_can_edit_product(user, product_id: uuid.UUID, db) -> Product:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Product not found')
    if user.role == UserRole.admin:
        return product
    seller = (await db.execute(select(Seller).where(Seller.user_id == user.id))).scalar_one_or_none()
    if not seller or product.seller_id != seller.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Not allowed to edit this product')
    return product


@router.get('/{product_id}/images', response_model=list[ProductImageOut])
async def list_product_images(product_id: uuid.UUID, db: DBSession) -> list[ProductImageOut]:
    rows = (await db.execute(
        select(ProductImage)
        .where(ProductImage.product_id == product_id)
        .order_by(ProductImage.position.asc(), ProductImage.created_at.asc())
    )).scalars().all()
    return [ProductImageOut.model_validate(r) for r in rows]


@router.post('/{product_id}/images', response_model=ProductImageOut, status_code=status.HTTP_201_CREATED)
async def add_product_image(
    product_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
    alt: str | None = Form(default=None),
    position: int | None = Form(default=None),
) -> ProductImageOut:
    await _assert_can_edit_product(user, product_id, db)

    content_type = (file.content_type or '').lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f'Unsupported content type: {file.content_type}. Allowed: {", ".join(ALLOWED_CONTENT_TYPES)}',
        )

    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f'File too large (max {MAX_IMAGE_BYTES} bytes).',
        )
    if len(data) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, 'Empty file.')

    ext = ALLOWED_CONTENT_TYPES[content_type]
    key = f'{product_id}/{uuid.uuid4().hex}{ext}'

    await storage_service.upload(key, data, content_type)

    img = ProductImage(
        id=uuid.uuid4(),
        product_id=product_id,
        url=storage_service.public_url(key),
        alt=alt,
        position=position if position is not None else 0,
    )
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return ProductImageOut.model_validate(img)


@router.delete('/{product_id}/images/{image_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(product_id: uuid.UUID, image_id: uuid.UUID, user: CurrentUser, db: DBSession) -> Response:
    await _assert_can_edit_product(user, product_id, db)
    img = await db.get(ProductImage, image_id)
    if not img or img.product_id != product_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Image not found')

    key = storage_service.key_from_url(img.url)
    if key:
        try:
            await storage_service.delete(key)
        except Exception as e:  # best-effort
            logger.warning('Failed to delete object %s from storage: %s', key, e)

    await db.delete(img)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
