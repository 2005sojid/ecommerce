"""Structured JSON logging (structlog) -> stdout -> Promtail -> Loki."""
import logging
import sys

import structlog

from app.config import settings


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # stdlib logging also in JSON
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

    # Don't be noisy with uvicorn access -- it's already in nginx access logs.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    structlog.contextvars.bind_contextvars(
        service=settings.OTEL_SERVICE_NAME, instance=settings.INSTANCE_ID
    )


logger = structlog.get_logger()
