import uuid
from fastapi import APIRouter, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from app.deps import CurrentUser, DBSession
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, RegisterResponse, TokenPair, UserOut
from app.services.auth_service import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
router = APIRouter(prefix='/api/auth', tags=['Auth'])

@router.post('/register', response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DBSession) -> RegisterResponse:
    existing = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, 'Email already registered')
    user = User(id=uuid.uuid4(), email=payload.email, password_hash=hash_password(payload.password), name=payload.name, role=UserRole.customer, is_active=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    tokens = TokenPair(access_token=create_access_token(str(user.id)), refresh_token=create_refresh_token(str(user.id)))
    return RegisterResponse(user=UserOut.model_validate(user), tokens=tokens)

@router.post('/login', response_model=TokenPair)
async def login(payload: LoginRequest, db: DBSession) -> TokenPair:
    user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid email or password')
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'User is disabled')
    return TokenPair(access_token=create_access_token(str(user.id)), refresh_token=create_refresh_token(str(user.id)))

@router.post('/refresh', response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DBSession) -> TokenPair:
    try:
        data = decode_token(payload.refresh_token)
        if data.get('type') != 'refresh':
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid token type')
        user_id = data.get('sub')
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Invalid refresh token')
    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'User not found or inactive')
    return TokenPair(access_token=create_access_token(str(user.id)), refresh_token=create_refresh_token(str(user.id)))

@router.get('/me', response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
