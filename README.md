# ShopSphere

Our project is multi-vendor marketplace. We defined three roles. First, **customers** that can browse, search, wishlist, chat with sellers, claim flash sales and check out atomically against live inventory. Then **sellers** that open a store, upload product images, manage variants, respond to reviews and reconcile payouts. Finally, **admins** moderate the catalog, manage coupons, approve returns and watch platform health in Grafana

## Quickstart

```bash
cp .env.example .env   # Copy example env reference to actual env  
docker compose build   # Builds the Docker images
docker compose up -d   # Starts all the containers in the background
```


| URL | What |
|---|---|
| `http://localhost` | Storefront (React) |
| `http://localhost/api/docs` | Swagger UI |
| `http://localhost/api/redoc` | ReDoc |
| `http://localhost/api/openapi.json` | OpenAPI JSON |
| `http://localhost:3000` | Grafana (default `admin` / `admin`) |
| `http://localhost:9001` | MinIO console (`minioadmin` / `minioadmin`) |
| `http://localhost:15672` | RabbitMQ management (uses `RABBITMQ_USER` / `RABBITMQ_PASS`) |

Seeded accounts:

| Role | Email | Password |
|---|---|---|
| admin | `admin@example.com` | `admin123` |
| customer | `customer1@example.com` … `customer4@example.com` | `password123` |
| seller | `seller1@example.com`, `seller2@example.com` | `seller123` |

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2 |
| RDBMS | PostgreSQL 16, Alembic (asyncpg driver) |
| Cache / KV / Cart | Redis 7 |
| Search | Meilisearch 1.10 |
| Broker | RabbitMQ 3, aio-pika |
| Object storage | MinIO (S3-compatible, public read on `product-images` bucket) |
| Gateway | Nginx (round-robin `/api`, `ip_hash` `/ws`) |
| Frontend | React 18, Vite, TypeScript, React Router 6, Axios |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Batch scheduler | APScheduler (cron + interval) |
| From-scratch #1 | Token-bucket rate limiter (Redis Lua) |
| From-scratch #2 | Snowflake ID generator |
| Observability | OpenTelemetry: Tempo, Prometheus, Loki + Promtail, Grafana |
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
| `ENVIRONMENT` | `development` |
| `INSTANCE_ID` | `0` |
| `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` | `minioadmin` / `minioadmin` |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | `minioadmin` / `minioadmin` |
| `MINIO_ENDPOINT` / `MINIO_PUBLIC_URL` | `minio:9000` / `(empty)` |
| `MINIO_BUCKET` / `MINIO_SECURE` | `product-images` / `false` |
| `BENCH_API_BASE` | `http://localhost` |

## Layout

```
backend/
├── Dockerfile · alembic.ini · requirements.txt · pyproject.toml
├── alembic/
│   ├── env.py
│   └── versions/ 001..016  (users, catalog, orders, reviews+flash, indexes, mv_daily_sales, marketplace, wishlist, notifications, coupons, returns, chat, review depth, product_images, order tracking+variant, settlements)
├── seeds/seed.py
├── scripts/benchmark.py                   
├── tests/                               
└── app/
    ├── main.py · config.py · database.py · deps.py
    ├── logging_config.py · metrics.py · telemetry.py
    ├── middleware/rate_limit.py           
    ├── from_scratch/
    │   ├── rate_limiter.py                
    │   └── snowflake_id.py                
    ├── cache/redis_cache.py              
    ├── models/
    │   ├── user · category · product · inventory · product_variant · product_image
    │   ├── order · order_event · review · review_vote · flash_sale
    │   ├── seller · address · settlement
    │   ├── wishlist · notification
    │   └── coupon · returns · conversation
    ├── schemas/                           
    ├── routers/
    │   ├── auth · products · product_images · categories · cart · orders
    │   ├── inventory · flash_sales · reviews · admin
    │   ├── wishlist · addresses · notifications
    │   ├── sellers · coupons · returns · chat · settlements
    │   └── ws (orders, inventory, user channels) · ws_chat
    ├── services/
    │   ├── auth · cart · order · search · flash_sale · storage 
    │   ├── notification_service           
    │   ├── notification_center        
    │   └── wishlist · address · seller · coupon · returns · chat · review_vote
    ├── workers/
    │   ├── order_pipeline                 
    │   └── search_sync                    
    └── batch/
        ├── daily_sales                    
        ├── daily_settlement               
        └── abandoned_cart                 
        
frontend/
├── Dockerfile · index.html · vite.config.ts · tsconfig.json · package.json · nginx.conf
└── src/
    ├── main.tsx · App.tsx · api.ts · useAuth.ts · index.css
    ├── components/
    │   ├── ProductCard.tsx                
    │   └── Carousel.tsx                   
    └── pages/
        ├── Home · Products · ProductDetail · Cart · Checkout
        ├── Orders · OrderDetail · FlashSales
        ├── Login · Register
        ├── Wishlist · Addresses · Notifications
        ├── Returns · Chat · SellerStore
        ├── seller/ SellerRegister · SellerDashboard · SellerProducts · SellerOrders · SellerSettings
        └── admin/ AdminDashboard · AdminCoupons · AdminOrders · AdminReturns · AdminReviewsModerate · AdminCategories

nginx/nginx.conf 
prometheus/
loki/ · promtail/
tempo/
grafana/provisioning/
├── datasources/datasources.yml
└── dashboards/
    ├── dashboards.yml               
    └── json/ API overview · Business KPIs · Logs & Traces
docker-compose.yml
docs/bpmn.md 
```
