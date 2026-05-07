# E-Commerce Platform

Distributed e-commerce backend: catalogue with full-text search, Redis cart, atomic flash-sales, event-driven order pipeline, real-time order tracking over WebSocket, daily analytics, full observability stack.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) |
| RDBMS | PostgreSQL 16 (+ Alembic migrations) |
| Cache / KV | Redis 7 (cart, flash-sale stock, response cache) |
| Search | Meilisearch 1.10 (typo-tolerant full-text) |
| Broker | RabbitMQ 3 (aio-pika, order pipeline + product index sync) |
| Gateway / LB | Nginx (round-robin REST, ip_hash WebSocket) |
| Frontend | React 18 + Vite + TypeScript |
| Rate limiter | Token-bucket (in-memory + Redis Lua) — implemented from scratch |
| Observability | OpenTelemetry → Tempo, Prometheus, Loki, Grafana, Promtail |

## Quick start

Requires Docker (Desktop or Engine + compose plugin) and ~2 GB free RAM.

```bash
git clone <repo-url> && cd ecommerce
cp .env.example .env
docker compose up -d --wait
```

That's it — one command. A one-shot `init` service runs Alembic migrations and the (idempotent) seeder before the backend replicas start, and the seeder populates the Meilisearch index, so the stack is fully usable as soon as `up -d --wait` returns. Total time on a clean machine: ~45 seconds.

| Service | URL | Notes |
|---|---|---|
| Frontend | http://localhost/ | login below |
| Swagger UI | http://localhost/api/docs | interactive REST docs |
| Grafana | http://localhost:3000 | `admin` / `admin` |
| RabbitMQ UI | http://localhost:15672 | `ecommerce` / `changeme` |

**Logins** (from the seeder):

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `admin123` |
| Customer | `customer1..4@example.com` | `password123` |

## Deploying to a public VM

Spec requires a publicly-reachable URL. Easiest path:

```bash
# Provision a VM (DigitalOcean, Hetzner, etc) with Docker and ports 80/22 open.
# From your laptop:
scp -r ecommerce root@<droplet-ip>:/root/
scp .env       root@<droplet-ip>:/root/ecommerce/.env

# On the VM:
ssh root@<droplet-ip>
cd /root/ecommerce
docker compose up -d --wait

# Done. Visit http://<droplet-ip>/
```

`.env` is gitignored, so it must be copied separately (use `scp` or paste a fresh one with rotated passwords). Once it's in place, a single `up -d --wait` runs migrations, seeds the catalogue, and indexes Meilisearch — the URL is live in under a minute.

The stack listens on port 80. Visit `http://<your-ip>/`.

### Adding HTTPS later (optional)

If you have a domain (or a free wildcard like `<ip>.nip.io`):

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
# Then uncomment the HTTPS server block at the bottom of nginx/nginx.conf,
# mount /etc/letsencrypt into the nginx container, and `docker compose up -d nginx`.
```

## Common commands

```bash
docker compose ps                                          # status
docker compose logs -f --tail=200                          # tail logs
docker compose exec backend-1 pytest                       # run tests (33)
docker compose exec backend-1 python -m seeds.seed         # idempotent (skips if data exists)
docker compose exec backend-1 python -m seeds.seed --force # wipe + reseed
docker compose down                                        # stop
docker compose down -v                                     # stop and wipe volumes
```

## Environment reference (`.env`)

| Variable | Default | Notes |
|---|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `ecommerce` / `postgres` / `changeme` | DB credentials |
| `DATABASE_URL` | `postgresql+asyncpg://...` | must match the three above |
| `REDIS_URL` | `redis://redis:6379/0` | |
| `RABBITMQ_USER` / `RABBITMQ_PASS` / `RABBITMQ_URL` | `ecommerce` / `changeme` / `amqp://...` | |
| `MEILISEARCH_URL` | `http://meilisearch:7700` | |
| `MEILISEARCH_API_KEY` | `masterKeyDevelopmentOnlyChangeMe` | **must be ≥ 16 bytes** (Meili production-mode requirement) |
| `JWT_SECRET` | `dev-secret-...` | rotate in prod (`openssl rand -hex 32`) |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRY_MINUTES` | `30` | access token lifetime |
| `GRAFANA_USER` / `GRAFANA_PASSWORD` | `admin` / `admin` | |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://tempo:4317` | OTLP gRPC into Tempo |
| `OTEL_SERVICE_NAME` | `ecommerce-backend` | trace/metric label |

## Layout

```
backend/
├── app/
│   ├── main.py                    # FastAPI app + lifespan
│   ├── config.py, database.py, deps.py
│   ├── models/                    # SQLAlchemy models
│   ├── schemas/                   # Pydantic DTOs
│   ├── routers/                   # REST + WebSocket
│   ├── services/                  # business logic, search, notification
│   ├── workers/                   # RabbitMQ consumers (in-process)
│   ├── batch/                     # APScheduler (daily MV refresh)
│   ├── middleware/rate_limit.py
│   ├── from_scratch/rate_limiter.py     # R11: token-bucket from scratch
│   ├── cache/redis_cache.py
│   ├── telemetry.py               # OpenTelemetry
│   ├── metrics.py                 # Prometheus
│   └── logging_config.py          # structlog → JSON
├── alembic/versions/              # 6 migrations
├── seeds/seed.py                  # demo data + Meilisearch reindex
├── scripts/benchmark.py           # R6 cache & index measurements
└── tests/                         # 33 pytest integration tests

frontend/                          # React + Vite SPA
nginx/nginx.conf                   # gateway: REST round-robin + WS ip_hash
prometheus/, loki/, tempo/, grafana/, promtail/
docker-compose.yml                 # the only compose file
docs/bpmn.md                       # BPMN diagrams (Mermaid)
```

## Spec coverage (R1–R13)

| ID | Requirement | Where |
|---|---|---|
| R1 | Business scenario / requirements | `docs/` + report |
| R2 | ER + architecture diagrams | report |
| R3 | RDBMS, migrations, seeder | `alembic/versions/`, `backend/seeds/seed.py` |
| R4 | REST API + Swagger | `backend/app/routers/` → http://localhost/api/docs |
| R5 | Polyglot persistence | Postgres + Redis + Meilisearch |
| R6 | Cache, indexes, MV, measurements | `backend/scripts/benchmark.py` |
| R7 | Non-REST protocol | WebSocket at `/ws/orders/{id}` and `/ws/inventory` |
| R8 | API gateway + LB | `nginx/nginx.conf` (2 backend replicas) |
| R9 | Single docker-compose | `docker-compose.yml` |
| R10 | Stream pipeline + BPMN | RabbitMQ workers + `docs/bpmn.md` |
| R11 | From-scratch component | `backend/app/from_scratch/rate_limiter.py` |
| R12 | Unified observability | OpenTelemetry → Tempo / Loki / Prometheus / Grafana |
| R13 | Documentation | this README, Swagger, [`CHANGELOG.md`](CHANGELOG.md) |

## Tests

```bash
docker compose exec backend-1 pytest
```

33 integration tests against live Postgres/Redis/RabbitMQ/Meilisearch — auth, products, cart, checkout, orders, flash sales, reviews, rate limiter. ~5 seconds.

## Benchmark (for the report)

```bash
docker compose exec backend-1 python -m scripts.benchmark
```

Drops indexes → `EXPLAIN ANALYZE` → restores → repeats → measures cold/warm cache → prints Markdown tables.

## Changes

See [`CHANGELOG.md`](CHANGELOG.md).
