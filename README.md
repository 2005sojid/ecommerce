# E-Commerce Platform

Distributed e-commerce backend: catalogue with full-text search, Redis cart, atomic flash-sales, event-driven order pipeline, real-time order tracking over WebSocket, daily analytics, full observability stack.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async |
| RDBMS | PostgreSQL 16, Alembic |
| Cache / KV | Redis 7 |
| Search | Meilisearch 1.10 |
| Broker | RabbitMQ 3, aio-pika |
| Gateway | Nginx |
| Frontend | React 18, Vite, TypeScript |
| From-scratch | Token-bucket rate limiter (Redis Lua) |
| Observability | OpenTelemetry, Tempo, Prometheus, Loki, Grafana, Promtail |
| Orchestration | Docker Compose |

## Environment reference (`.env`)

| Variable | Default |
|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `ecommerce` / `postgres` / `changeme` |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:changeme@postgres:5432/ecommerce` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `RABBITMQ_USER` / `RABBITMQ_PASS` / `RABBITMQ_URL` | `ecommerce` / `changeme` / `amqp://ecommerce:changeme@rabbitmq:5672/` |
| `MEILISEARCH_URL` | `http://meilisearch:7700` |
| `MEILISEARCH_API_KEY` | `masterKeyDevelopmentOnlyChangeMe` |
| `JWT_SECRET` | `dev-secret-please-change-in-production-use-openssl-rand-hex-32` |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRY_MINUTES` | `30` |
| `GRAFANA_USER` / `GRAFANA_PASSWORD` | `admin` / `admin` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://tempo:4317` |
| `OTEL_SERVICE_NAME` | `ecommerce-backend` |

## Layout

```
backend/
├── app/
│   ├── main.py
│   ├── config.py, database.py, deps.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   ├── workers/
│   ├── batch/
│   ├── middleware/rate_limit.py
│   ├── from_scratch/rate_limiter.py
│   ├── cache/redis_cache.py
│   ├── telemetry.py
│   ├── metrics.py
│   └── logging_config.py
├── alembic/versions/
├── seeds/seed.py
├── scripts/benchmark.py
└── tests/

frontend/
nginx/nginx.conf
prometheus/, loki/, tempo/, grafana/, promtail/
docker-compose.yml
docs/bpmn.md
```
