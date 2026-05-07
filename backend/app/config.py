from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/ecommerce"
    REDIS_URL: str = "redis://redis:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    MEILISEARCH_URL: str = "http://meilisearch:7700"
    MEILISEARCH_API_KEY: str = "masterKeyDevelopmentOnlyChangeMe"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 30

    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://tempo:4317"
    OTEL_SERVICE_NAME: str = "ecommerce-backend"
    INSTANCE_ID: str = "0"

    class Config:
        env_file = ".env"


settings = Settings()
