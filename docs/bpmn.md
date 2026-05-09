# BPMN -- Event Pipeline (R10)

Below are textual descriptions of the three required diagrams (Mermaid flowchart). For the report they are imported into bpmn.io / draw.io and exported as PNG/SVG.

---

## BPMN 1 -- Order Fulfilment Pipeline

```mermaid
flowchart LR
    Start([Start: order.created]) --> Confirm[Advance: confirmed<br/>delay 2.0s]
    Confirm --> Process[Advance: processing<br/>delay 0.5s]
    Process --> Pack[Advance: packed<br/>delay 3.0s]
    Pack --> Ship[Advance: shipped<br/>delay 1.0s]
    Ship --> EndOk([End: shipped])
```

Stock is decremented synchronously at checkout (`order_service.checkout`); insufficient stock raises HTTP 409 before any event is published, so the pipeline has no cancel branch. Each transition writes a row to `order_events`, broadcasts the new status over WebSocket, and republishes the next routing key on the `ecommerce` exchange. Consumer: `app/workers/order_pipeline.py` (`NEXT_STAGE` map). `shipped` is terminal — there is no `delivered` stage in the running code.

---

## BPMN 2 -- Daily Sales Batch

```mermaid
flowchart LR
    Timer([Timer: cron 02:00 daily]) --> Refresh[REFRESH MATERIALIZED VIEW<br/>CONCURRENTLY mv_daily_sales]
    Refresh --> G1{Concurrent refresh OK?}
    G1 -- Yes --> Commit[Commit]
    G1 -- No --> Plain[REFRESH MATERIALIZED VIEW<br/>mv_daily_sales]
    Plain --> Commit
    Commit --> Log[Log refreshed date]
    Log --> End([End])
```

Aggregation (`order_count`, `total_revenue`, `unique_customers`, filtered to `status <> 'cancelled'`) lives in the materialized view itself, defined in `alembic/versions/006_mv_daily_sales.py`. The scheduled job only refreshes the view; it does not query or aggregate orders directly. Implementation: `app/batch/daily_sales.py` (APScheduler cron `hour=2, minute=0`).

---

## BPMN 3 -- Search Index Sync

```mermaid
flowchart LR
    Msg([Message: product.created /<br/> product.updated / product.deleted]) --> Route{Routing key}
    Route -- created/updated --> Fetch[Fetch product + category from PG]
    Fetch --> Doc[Transform to search document]
    Doc --> Upsert[Upsert in Meilisearch]
    Upsert --> End1([End])
    Route -- deleted --> Remove[Delete document by id]
    Remove --> End2([End])
```

Implementation: `app/workers/search_sync.py`. Queue `search_sync` is bound to exchange `ecommerce` by routing key `product.*`.
