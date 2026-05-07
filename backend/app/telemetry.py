"""OpenTelemetry -- distributed tracing.

Auto-instrumentation:
  - FastAPI: HTTP spans with request_id, route, status_code.
  - SQLAlchemy: span per SQL statement (operation, table, duration).
  - Redis: span per command.
  - aio-pika: span on publish / consume (trace context propagation via RabbitMQ).

Export OTLP/gRPC -> Tempo.
"""
import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings

logger = logging.getLogger(__name__)


def setup_telemetry(app, sa_engine) -> None:
    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.instance.id": settings.INSTANCE_ID,
        }
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=sa_engine.sync_engine)
    RedisInstrumentor().instrument()
    AioPikaInstrumentor().instrument()
    logger.info("OpenTelemetry initialised, exporting to %s", settings.OTEL_EXPORTER_OTLP_ENDPOINT)
