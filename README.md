# ShopSphere

A production-shaped multi-vendor marketplace. Three roles share one storefront — **customers** browse, search, wishlist, chat with sellers, claim flash sales and check out atomically against live inventory; **sellers** open a store, upload product images, manage variants, respond to reviews and reconcile payouts; **admins** moderate the catalog, manage coupons, approve returns and watch platform health in Grafana.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async |
| RDBMS | PostgreSQL 16, Alembic |
| Cache / KV / Cart | Redis 7 |
| Search | Meilisearch 1.10 |
| Broker | RabbitMQ 3, aio-pika |
| Object storage | MinIO (S3-compatible, public read on `product-images` bucket) |
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
| `MINIO_ENDPOINT` / `MINIO_PUBLIC_URL` | `minio:9000` (internal) / `http://localhost:9000` (browser) |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | `minioadmin` / `minioadmin` |
| `MINIO_BUCKET` / `MINIO_SECURE` | `product-images` / `false` |
| `ENVIRONMENT` | `development` (backend refuses to boot in any other value if `JWT_SECRET` / `MEILISEARCH_API_KEY` are still the placeholder) |
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
│   ├── services/storage_service.py   ← MinIO wrapper (upload / delete / public_url)
│   ├── telemetry.py · metrics.py · logging_config.py
├── alembic/versions/          001..016
├── seeds/seed.py
├── scripts/benchmark.py
└── tests/

frontend/src/
├── App.tsx · main.tsx · api.ts · useAuth.ts
├── components/
│   ├── ProductCard.tsx   ← shared dark card with SVG-icon fallback + heart
│   └── Carousel.tsx      ← image gallery used on ProductDetail
├── pages/
│   ├── Home · Products · ProductDetail · Cart · Checkout
│   ├── Orders · OrderDetail · FlashSales
│   ├── Login · Register
│   ├── Wishlist · Addresses · Notifications
│   ├── Returns · Chat · SellerStore
│   ├── seller/    SellerRegister · SellerDashboard · SellerProducts (file upload + drag/drop) ·
│   │              SellerOrders · SellerSettings
│   └── admin/     AdminDashboard · AdminCoupons · AdminReturns ·
│                  AdminReviewsModerate · AdminCategories

nginx/  prometheus/  loki/  tempo/  grafana/  promtail/
docker-compose.yml
docs/bpmn.md
```
