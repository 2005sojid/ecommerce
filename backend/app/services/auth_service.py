from datetime import datetime, timedelta, timezone
from typing import Literal
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
REFRESH_EXPIRY_DAYS = 7

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def _create_token(sub: str, kind: Literal['access', 'refresh'], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {'sub': sub, 'type': kind, 'iat': int(now.timestamp()), 'exp': int((now + expires_delta).timestamp())}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_access_token(user_id: str) -> str:
    return _create_token(user_id, 'access', timedelta(minutes=settings.JWT_EXPIRY_MINUTES))

def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id, 'refresh', timedelta(days=REFRESH_EXPIRY_DAYS))

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
