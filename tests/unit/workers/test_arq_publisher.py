"""ArqEventPublisher: InvoiceReceived onto the job queue with the caller's trace."""

from datetime import UTC, datetime
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from invoice_to_pay.adapters.arq_events import INVOICE_RECEIVED_JOB, ArqEventPublisher
from invoice_to_pay.contracts.common import uuid7
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.workers.intake import invoice_received_job


class _FakePool:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.closed = False

    async def enqueue_job(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))

    async def aclose(self) -> None:
        self.closed = True


def _event() -> InvoiceReceived:
    return InvoiceReceived(
        event_id=uuid7(),
        entity="meridian-supply",
        file_id=uuid7(),
        sha256="e" * 64,
        channel="scan",
        occurred_at=datetime.now(UTC),
    )


def test_job_name_matches_the_worker_function() -> None:
    assert invoice_received_job.__name__ == INVOICE_RECEIVED_JOB


async def test_publish_enqueues_event_json_with_trace_and_event_job_id(
    spans: InMemorySpanExporter,
) -> None:
    pool = _FakePool()
    publisher = ArqEventPublisher("redis://unused:6379/0", pool=pool)
    evt = _event()
    with trace.get_tracer("test").start_as_current_span("upload") as span:
        await publisher.publish(evt)
    ((name, args, kwargs),) = pool.calls
    assert name == INVOICE_RECEIVED_JOB
    assert args[0] == evt.model_dump(mode="json")
    assert format(span.get_span_context().trace_id, "032x") in args[1]["traceparent"]
    assert kwargs == {"_job_id": f"invoice-received:{evt.event_id}"}


async def test_close_closes_the_pool() -> None:
    pool = _FakePool()
    publisher = ArqEventPublisher("redis://unused:6379/0", pool=pool)
    await publisher.close()
    assert pool.closed
