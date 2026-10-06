"""Traces and trace-aware logs: one root span per run, trace id on every log line."""

import logging
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import structlog
from opentelemetry import context, propagate, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.trace import Span

from invoice_to_pay.application.context import current_principal
from invoice_to_pay.config.settings import Settings

SERVICE_NAME = "invoice-to-pay"

_provider: TracerProvider | None = None
_tracer = trace.get_tracer("invoice_to_pay")


def exporter_for(settings: Settings) -> SpanExporter | None:
    """OTLP exporter when an endpoint is configured; spans stay in-process otherwise."""
    if settings.otel_endpoint is None:
        return None
    return OTLPSpanExporter(endpoint=str(settings.otel_endpoint))


def setup_tracing(settings: Settings) -> TracerProvider:
    """OTLP exporter and resource attributes; model spans come from adapters/langchain_llm.py."""
    global _provider
    if _provider is not None:
        return _provider
    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    exporter = exporter_for(settings)
    if exporter is not None:
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _provider = provider
    return provider


@contextmanager
def run_span(run_id: UUID) -> Iterator[Span]:
    """Root span per run with run.id and entity attributes."""
    principal = current_principal.get()
    attributes = {"run.id": str(run_id), "entity": principal.entity}
    with (
        _tracer.start_as_current_span("run", attributes=attributes) as span,
        structlog.contextvars.bound_contextvars(run_id=str(run_id), entity=principal.entity),
    ):
        yield span


def inject_trace() -> dict[str, str]:
    """W3C trace context of the active span, to carry across the job queue."""
    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    return carrier


@contextmanager
def attached_trace(carrier: dict[str, str]) -> Iterator[None]:
    """Continue the trace a job's publisher carried (no-op for an empty carrier)."""
    token = context.attach(propagate.extract(carrier))
    try:
        yield
    finally:
        context.detach(token)


def current_trace_id() -> str:
    """Hex trace id of the active span, or '' outside a span; feeds ledger entries."""
    ctx = trace.get_current_span().get_span_context()
    return format(ctx.trace_id, "032x") if ctx.is_valid else ""


def _add_trace_ids(
    logger: Any, method: str, event: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    ctx = trace.get_current_span().get_span_context()
    if ctx.is_valid:
        event["trace_id"] = format(ctx.trace_id, "032x")
        event["span_id"] = format(ctx.span_id, "016x")
    return event


def setup_logging() -> None:
    """JSON logs with run_id, entity and trace_id on every line (C-09)."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_trace_ids,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
