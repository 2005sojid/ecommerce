from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
orders_created = Counter('orders_created_total', 'Orders created (checkout)')
flash_sale_claims = Counter('flash_sale_claims_total', 'Flash-sale claim attempts', ['status'])
cache_ops = Counter('cache_ops_total', 'Cache hit/miss by key type', ['op', 'key_pattern'])
checkout_duration = Histogram('checkout_duration_seconds', 'Checkout duration (from request start to commit)', buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0))
order_status_transitions = Counter('order_status_transitions_total', 'Order status transitions', ['from_status', 'to_status'])

def setup_metrics(app) -> None:
    Instrumentator(excluded_handlers=['/metrics', '/api/health'], should_group_status_codes=True).instrument(app).expose(app, endpoint='/metrics', include_in_schema=False)
