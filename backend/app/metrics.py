from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

orders_created = Counter('orders_created_total', 'Orders created (checkout)')
flash_sale_claims = Counter('flash_sale_claims_total', 'Flash-sale claim attempts', ['status'])
cache_ops = Counter('cache_ops_total', 'Cache hit/miss by key type', ['op', 'key_pattern'])
checkout_duration = Histogram('checkout_duration_seconds', 'Checkout duration (from request start to commit)', buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0))
order_status_transitions = Counter('order_status_transitions_total', 'Order status transitions', ['from_status', 'to_status'])


def _preinit_label_series() -> None:
    for status in ('success', 'sold_out', 'error', 'rate_limited'):
        flash_sale_claims.labels(status=status)
    for op in ('hit', 'miss', 'invalidate'):
        for key_pattern in ('product', 'categories'):
            cache_ops.labels(op=op, key_pattern=key_pattern)
    transitions = [
        ('none', 'pending'),
        ('pending', 'confirmed'), ('pending', 'cancelled'),
        ('confirmed', 'processing'), ('confirmed', 'cancelled'),
        ('processing', 'packed'), ('processing', 'cancelled'),
        ('packed', 'shipped'), ('packed', 'cancelled'),
        ('shipped', 'delivered'),
    ]
    for from_status, to_status in transitions:
        order_status_transitions.labels(from_status=from_status, to_status=to_status)


def setup_metrics(app) -> None:
    _preinit_label_series()
    Instrumentator(excluded_handlers=['/metrics', '/api/health'], should_group_status_codes=True).instrument(app).expose(app, endpoint='/metrics', include_in_schema=False)
