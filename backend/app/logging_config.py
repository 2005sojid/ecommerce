import logging
import sys
import structlog
from opentelemetry import trace
from app.config import settings


def _inject_otel_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span is None:
        return event_dict
    ctx = span.get_span_context()
    if not ctx or not ctx.is_valid:
        return event_dict
    event_dict['trace_id'] = format(ctx.trace_id, '032x')
    event_dict['span_id'] = format(ctx.span_id, '016x')
    return event_dict


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt='iso', utc=True)
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        _inject_otel_context,
        timestamper,
    ]
    structlog.configure(
        processors=shared_processors + [
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    structlog.contextvars.bind_contextvars(service=settings.OTEL_SERVICE_NAME, instance=settings.INSTANCE_ID)


logger = structlog.get_logger()
