# BPMN -- Event Pipeline (R10)

Below are textual descriptions of the three required diagrams (Mermaid flowchart). For the report they are imported into bpmn.io / draw.io and exported as PNG/SVG.

---

## BPMN 1 -- Order Fulfilment Pipeline

```mermaid
flowchart LR
    Start([Start: Order Placed]) --> VP[Verify Payment]
    VP --> G1{Payment OK?}
    G1 -- No --> Cancel[Cancel Order]
    Cancel --> EndCancel([End: Cancelled])
    G1 -- Yes --> Confirm[Confirm Order<br/>status=confirmed]
    Confirm --> Process[Process & Pack<br/>status=processing->packed]
    Process --> Ship[Ship<br/>status=shipped]
    Ship --> Deliver[Deliver<br/>status=delivered]
    Deliver --> EndOk([End: Complete])

    Process -. boundary error .-> StockErr[Insufficient Stock]
    StockErr --> Cancel
```

Each transition inserts a row into `order_events` (audit trail) and publishes an event to the RabbitMQ topic `order.*`. The consumer is `app/workers/order_pipeline.py`.

---

## BPMN 2 -- Daily Sales Batch

```mermaid
flowchart LR
    Timer([Timer: 02:00 UTC daily]) --> Q[Query yesterday's orders<br/>status <> cancelled]
    Q --> Agg[Aggregate metrics<br/>order_count, revenue, unique_customers]
    Agg --> R[REFRESH MATERIALIZED VIEW<br/>mv_daily_sales CONCURRENTLY]
    R --> Log[Log results]
    Log --> End([End])
```

Implementation: `app/batch/daily_sales.py` (APScheduler cron `hour=2`).

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
