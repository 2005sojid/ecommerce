import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from app.from_scratch.rate_limiter import RateLimiter
from app.services.auth_service import decode_token
logger = logging.getLogger(__name__)

def _client_id(request: Request) -> str:
    auth = request.headers.get('authorization') or ''
    if auth.lower().startswith('bearer '):
        try:
            payload = decode_token(auth.split(' ', 1)[1])
            sub = payload.get('sub')
            if sub:
                return f'user:{sub}'
        except JWTError:
            pass
    host = request.client.host if request.client else 'unknown'
    return f'ip:{host}'

class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, limiter: RateLimiter, paths: list[str] | None=None) -> None:
        super().__init__(app)
        self.limiter = limiter
        self.paths = paths or []

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if self.paths and (not any((path.startswith(p) for p in self.paths))):
            return await call_next(request)
        try:
            (allowed, headers) = await self.limiter.allow_request(_client_id(request))
        except Exception as exc:
            logger.warning('rate limiter error, fail-open: %s', exc)
            return await call_next(request)
        if not allowed:
            if path.startswith('/api/flash-sales/'):
                from app.metrics import flash_sale_claims
                flash_sale_claims.labels(status='rate_limited').inc()
            return JSONResponse(status_code=429, content={'detail': 'Too Many Requests'}, headers=headers)
        response = await call_next(request)
        for (k, v) in headers.items():
            response.headers[k] = v
        return response
