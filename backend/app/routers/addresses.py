import uuid
from fastapi import APIRouter, status
from fastapi.responses import Response
from app.deps import CurrentUser, DBSession
from app.schemas.address import AddressCreate, AddressUpdate, AddressOut
from app.services import address_service

router = APIRouter(prefix='/api/addresses', tags=['Addresses'])


@router.get('')
async def list_addresses(user: CurrentUser, db: DBSession) -> list[AddressOut]:
    items = await address_service.list_for_user(db, user.id)
    return [AddressOut.model_validate(a) for a in items]


@router.post('', status_code=status.HTTP_201_CREATED)
async def create_address(payload: AddressCreate, user: CurrentUser, db: DBSession) -> AddressOut:
    addr = await address_service.create(db, user.id, payload)
    return AddressOut.model_validate(addr)


@router.get('/{address_id}')
async def get_address(address_id: uuid.UUID, user: CurrentUser, db: DBSession) -> AddressOut:
    addr = await address_service.get_for_user(db, user.id, address_id)
    return AddressOut.model_validate(addr)


@router.patch('/{address_id}')
async def update_address(address_id: uuid.UUID, payload: AddressUpdate, user: CurrentUser, db: DBSession) -> AddressOut:
    addr = await address_service.update(db, user.id, address_id, payload)
    return AddressOut.model_validate(addr)


@router.delete('/{address_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(address_id: uuid.UUID, user: CurrentUser, db: DBSession) -> Response:
    await address_service.delete(db, user.id, address_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/{address_id}/default')
async def set_default_address(address_id: uuid.UUID, user: CurrentUser, db: DBSession) -> AddressOut:
    addr = await address_service.set_default(db, user.id, address_id)
    return AddressOut.model_validate(addr)
