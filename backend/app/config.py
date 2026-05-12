import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = 'postgresql+asyncpg://postgres:postgres@postgres:5432/ecommerce'
    REDIS_URL: str = 'redis://redis:6379/0'
    RABBITMQ_URL: str = 'amqp://guest:guest@rabbitmq:5672/'
    MEILISEARCH_URL: str = 'http://meilisearch:7700'
    MEILISEARCH_API_KEY: str = 'masterKeyDevelopmentOnlyChangeMe'
    JWT_SECRET: str = 'change-me-in-production'
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRY_MINUTES: int = 30
    OTEL_EXPORTER_OTLP_ENDPOINT: str = 'http://tempo:4317'
    OTEL_SERVICE_NAME: str = 'ecommerce-backend'
    INSTANCE_ID: str = '0'
    ENVIRONMENT: str = 'development'

    # MinIO / object storage
    MINIO_ENDPOINT: str = 'minio:9000'
    MINIO_ACCESS_KEY: str = 'minioadmin'
    MINIO_SECRET_KEY: str = 'minioadmin'
    MINIO_BUCKET: str = 'product-images'
    MINIO_PUBLIC_URL: str = 'http://localhost:9000'
    MINIO_SECURE: bool = False

    class Config:
        env_file = '.env'

settings = Settings()

# Fail fast in production if placeholder secrets weren't overridden.
if settings.ENVIRONMENT.lower() not in ('development', 'dev', 'test', 'testing'):
    if settings.JWT_SECRET == 'change-me-in-production':
        raise RuntimeError('Refusing to start: JWT_SECRET is still the default placeholder. Set it in .env.')
    if settings.MEILISEARCH_API_KEY == 'masterKeyDevelopmentOnlyChangeMe':
        raise RuntimeError('Refusing to start: MEILISEARCH_API_KEY is still the development placeholder. Set it in .env.')
