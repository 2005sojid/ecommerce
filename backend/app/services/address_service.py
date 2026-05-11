import uuid
from fastapi import HTTPException, status
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Address]:
    stmt = select(Address).where(Address.user_id == user_id).order_by(Address.is_default.desc(), Address.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_for_user(db: AsyncSession, user_id: uuid.UUID, address_id: uuid.UUID) -> Address:
    stmt = select(Address).where(Address.id == address_id, Address.user_id == user_id)
    addr = (await db.execute(stmt)).scalar_one_or_none()
    if addr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Address not found')
    return addr


async def _count(db: AsyncSession, user_id: uuid.UUID) -> int:
    return int(await db.scalar(select(func.count(Address.id)).where(Address.user_id == user_id)) or 0)


async def _unset_defaults(db: AsyncSession, user_id: uuid.UUID, exclude_id: uuid.UUID | None = None) -> None:
    stmt = update(Address).where(Address.user_id == user_id, Address.is_default == True).values(is_default=False)
    if exclude_id is not None:
        stmt = stmt.where(Address.id != exclude_id)
    await db.execute(stmt)


async def create(db: AsyncSession, user_id: uuid.UUID, payload: AddressCreate) -> Address:
    existing_count = await _count(db, user_id)
    make_default = payload.is_default or existing_count == 0
    if make_default:
        await _unset_defaults(db, user_id)
    data = payload.model_dump()
    data['is_default'] = make_default
    data['country'] = data['country'].upper()
    addr = Address(id=uuid.uuid4(), user_id=user_id, **data)
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return addr


async def update(db: AsyncSession, user_id: uuid.UUID, address_id: uuid.UUID, payload: AddressUpdate) -> Address:
    addr = await get_for_user(db, user_id, address_id)
    changes = payload.model_dump(exclude_unset=True)
    if 'country' in changes and changes['country']:
        changes['country'] = changes['country'].upper()
    if 'is_default' in changes:
        if changes['is_default'] is True:
            await _unset_defaults(db, user_id, exclude_id=address_id)
        elif changes['is_default'] is False:
            total = await _count(db, user_id)
            if total <= 1:
                changes['is_default'] = True
    for k, v in changes.items():
        setattr(addr, k, v)
    await db.commit()
    await db.refresh(addr)
    return addr


async def delete(db: AsyncSession, user_id: uuid.UUID, address_id: uuid.UUID) -> None:
    addr = await get_for_user(db, user_id, address_id)
    await db.execute(delete(Address).where(Address.id == address_id, Address.user_id == user_id))
    await db.commit()
    remaining = await db.scalar(select(func.count(Address.id)).where(Address.user_id == user_id)) or 0
    if remaining > 0:
        has_default = await db.scalar(select(func.count(Address.id)).where(Address.user_id == user_id, Address.is_default == True)) or 0
        if has_default == 0:
            stmt = select(Address).where(Address.user_id == user_id).order_by(Address.created_at.desc()).limit(1)
            newest = (await db.execute(stmt)).scalar_one_or_none()
            if newest is not None:
                newest.is_default = True
                await db.commit()


async def set_default(db: AsyncSession, user_id: uuid.UUID, address_id: uuid.UUID) -> Address:
    addr = await get_for_user(db, user_id, address_id)
    await _unset_defaults(db, user_id, exclude_id=address_id)
    addr.is_default = True
    await db.commit()
    await db.refresh(addr)
    return addr
