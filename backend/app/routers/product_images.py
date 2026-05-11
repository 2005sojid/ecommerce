import uuid
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from app.deps import CurrentUser, DBSession
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.seller import Seller
from app.models.user import UserRole
from app.schemas.product_image import ProductImageCreate, ProductImageOut

router = APIRouter(prefix='/api/products', tags=['ProductImages'])


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
async def add_product_image(product_id: uuid.UUID, payload: ProductImageCreate, user: CurrentUser, db: DBSession) -> ProductImageOut:
    await _assert_can_edit_product(user, product_id, db)
    img = ProductImage(id=uuid.uuid4(), product_id=product_id, url=payload.url, alt=payload.alt, position=payload.position)
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
    await db.delete(img)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
