# Multi-Vendor E-Commerce Marketplace

A distributed marketplace platform with multiple sellers, real-time inventory, flash sales, atomic checkout with coupons, buyer↔seller chat, in-app notifications, returns/refunds, multi-image product galleries, per-variant pricing and stock, daily seller settlements, cross-replica WebSocket delivery via Redis pub/sub, and a full observability stack.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async |
| RDBMS | PostgreSQL 16, Alembic |
| Cache / KV / Cart | Redis 7 |
| Search | Meilisearch 1.10 |
| Broker | RabbitMQ 3, aio-pika |
| Gateway | Nginx |
| Frontend | React 18, Vite, TypeScript |
| From-scratch #1 | Token-bucket rate limiter (Redis Lua) |
| From-scratch #2 | Snowflake ID generator |
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
| `INSTANCE_ID` | `1` |
| `GRAFANA_USER` / `GRAFANA_PASSWORD` | `admin` / `admin` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://tempo:4317` |
| `OTEL_SERVICE_NAME` | `ecommerce-backend` |

## Layout

```
backend/
├── app/
│   ├── main.py
│   ├── config.py · database.py · deps.py
│   ├── models/
│   │   ├── user · category · product · inventory · product_variant · product_image
│   │   ├── order · order_event · review · review_vote · flash_sale
│   │   ├── seller · address · settlement
│   │   ├── wishlist · notification
│   │   ├── coupon · returns · conversation
│   ├── schemas/
│   ├── routers/
│   │   ├── auth · products · product_images · categories · cart · orders
│   │   ├── inventory · flash_sales · reviews · admin
│   │   ├── wishlist · addresses · notifications
│   │   ├── sellers · coupons · returns · chat · settlements
│   │   ├── ws · ws_chat
│   ├── services/
│   │   ├── auth · cart · order · search · flash_sale
│   │   ├── notification_service (RabbitMQ event bus)
│   │   ├── notification_center (in-app notifications)
│   │   ├── wishlist · address · seller · coupon · returns · chat · review_vote
│   ├── workers/
│   │   ├── order_pipeline · search_sync
│   ├── batch/
│   │   ├── daily_sales · daily_settlement · abandoned_cart
│   ├── middleware/rate_limit.py
│   ├── from_scratch/
│   │   ├── rate_limiter.py
│   │   └── snowflake_id.py
│   ├── cache/redis_cache.py
│   ├── telemetry.py · metrics.py · logging_config.py
├── alembic/versions/          001..016
├── seeds/seed.py
├── scripts/benchmark.py
└── tests/

frontend/src/
├── App.tsx · main.tsx · api.ts · useAuth.ts
├── pages/
│   ├── Home · Products · ProductDetail · Cart · Checkout
│   ├── Orders · OrderDetail · FlashSales
│   ├── Login · Register
│   ├── Wishlist · Addresses · Notifications
│   ├── Returns · Chat · SellerStore
│   ├── seller/    SellerRegister · SellerDashboard · SellerProducts ·
│   │              SellerOrders · SellerSettings
│   └── admin/     AdminDashboard · AdminCoupons · AdminReturns ·
│                  AdminReviewsModerate · AdminCategories

nginx/  prometheus/  loki/  tempo/  grafana/  promtail/
docker-compose.yml
docs/bpmn.md
```
