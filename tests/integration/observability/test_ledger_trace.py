"""Ledger entries written inside a run carry the run's trace id."""

from uuid import uuid4

from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from sqlalchemy.ext.asyncio import async_sessionmaker

from invoice_to_pay.application.context import current_principal
from invoice_to_pay.contracts.common import Principal
from invoice_to_pay.control.ledger import RunLedger
from invoice_to_pay.observability.tracing import current_trace_id, run_span


async def test_ledger_entry_carries_run_trace_id(
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    spans: InMemorySpanExporter,
) -> None:
    ledger = RunLedger(sessions, trace_id=current_trace_id)
    token = current_principal.set(Principal(subject="a", kind="agent", entity="meridian-supply"))
    try:
        with run_span(uuid4()) as span:
            entry = await ledger.append(uuid4(), "decision", {"doc_type": "invoice"})
    finally:
        current_principal.reset(token)
    assert entry.trace_id == format(span.get_span_context().trace_id, "032x")
