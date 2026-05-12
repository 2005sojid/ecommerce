"""MinIO-backed object storage for product images.

Wraps the synchronous `minio` client in `asyncio.to_thread` so it can be
awaited from FastAPI handlers.
"""
from __future__ import annotations

import asyncio
import io
import json
import logging
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket: Optional[str] = None,
        secure: Optional[bool] = None,
        public_url: Optional[str] = None,
    ) -> None:
        self.endpoint = endpoint or settings.MINIO_ENDPOINT
        self.access_key = access_key or settings.MINIO_ACCESS_KEY
        self.secret_key = secret_key or settings.MINIO_SECRET_KEY
        self.bucket = bucket or settings.MINIO_BUCKET
        self.secure = settings.MINIO_SECURE if secure is None else secure
        self._public_url = (public_url or settings.MINIO_PUBLIC_URL).rstrip('/')
        self._client: Minio | None = None
        self._bucket_ready = False
        self._lock = asyncio.Lock()

    def _get_client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
        return self._client

    def _ensure_bucket_sync(self) -> None:
        client = self._get_client()
        if not client.bucket_exists(self.bucket):
            client.make_bucket(self.bucket)
            policy = {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Effect': 'Allow',
                        'Principal': {'AWS': ['*']},
                        'Action': ['s3:GetObject'],
                        'Resource': [f'arn:aws:s3:::{self.bucket}/*'],
                    }
                ],
            }
            try:
                client.set_bucket_policy(self.bucket, json.dumps(policy))
            except S3Error as e:
                logger.warning('Failed to set bucket policy on %s: %s', self.bucket, e)

    async def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        async with self._lock:
            if self._bucket_ready:
                return
            await asyncio.to_thread(self._ensure_bucket_sync)
            self._bucket_ready = True

    def _put_sync(self, key: str, data: bytes, content_type: str) -> None:
        client = self._get_client()
        client.put_object(
            self.bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        await self._ensure_bucket()
        await asyncio.to_thread(self._put_sync, key, data, content_type)

    def _delete_sync(self, key: str) -> None:
        client = self._get_client()
        client.remove_object(self.bucket, key)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._delete_sync, key)

    def public_url(self, key: str) -> str:
        return f'{self._public_url}/{self.bucket}/{key}'

    def key_from_url(self, url: str) -> str | None:
        """Best-effort: parse the object key off a public URL."""
        prefix = f'{self._public_url}/{self.bucket}/'
        if url.startswith(prefix):
            return url[len(prefix):]
        marker = f'/{self.bucket}/'
        idx = url.find(marker)
        if idx >= 0:
            return url[idx + len(marker):]
        return None


storage_service = StorageService()
