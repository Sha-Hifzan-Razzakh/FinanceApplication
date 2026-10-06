"""CS-021 start_settle_run."""

from datetime import UTC, datetime

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from invoice_to_pay.application.use_cases.settle_invoice import GOAL_TYPE, start_settle_run
from invoice_to_pay.contracts.common import Principal, uuid7
from invoice_to_pay.contracts.intake import FileRecord
from invoice_to_pay.control.errors import DomainError
from invoice_to_pay.observability.tracing import current_trace_id
from tests.fakes.runs import InMemoryRunStore, RecordingLedger

AGENT = Principal(subject="agent:invoice-to-pay", kind="agent", entity="meridian-supply")
SHA = "c" * 64


def _file(entity: str = "meridian-supply") -> FileRecord:
    return FileRecord.model_validate(
        {
            "id": uuid7(),
            "entity": entity,
            "sha256": SHA,
            "channel": "scan",
            "object_key": f"{entity}/{SHA}",
            "mime_type": "application/pdf",
            "size_bytes": 70,
            "received_at": datetime.now(UTC),
        }
    )


async def test_cs021_creates_one_run_with_entity_file_thread_id(
    spans: InMemorySpanExporter,
) -> None:
    runs, ledger, file = InMemoryRunStore(), RecordingLedger(), _file()
    run_id = await start_settle_run(file, AGENT, runs=runs, ledger=ledger)
    thread_id = f"meridian-supply:{file.id}"
    assert runs.runs[thread_id]["id"] == run_id
    assert runs.runs[thread_id]["goal_type"] == GOAL_TYPE == "ap.settle_invoice"
    assert runs.runs[thread_id]["status"] == "running"


async def test_cs021_opens_the_ledger_inside_the_run_span(spans: InMemorySpanExporter) -> None:
    runs, file = InMemoryRunStore(), _file()
    ledger = RecordingLedger(trace_id=current_trace_id)
    run_id = await start_settle_run(file, AGENT, runs=runs, ledger=ledger)
    (entry,) = ledger.entries
    assert (entry.run_id, entry.seq, entry.kind) == (run_id, 1, "received")
    assert entry.body["file_id"] == str(file.id)
    assert entry.body["sha256"] == SHA
    assert entry.body["thread_id"] == f"meridian-supply:{file.id}"
    (span,) = [s for s in spans.get_finished_spans() if s.name == "run"]
    assert span.attributes is not None and span.attributes["run.id"] == str(run_id)
    assert entry.trace_id == format(span.context.trace_id, "032x")


async def test_cs021_second_start_returns_the_same_run_without_reopening(
    spans: InMemorySpanExporter,
) -> None:
    runs, ledger, file = InMemoryRunStore(), RecordingLedger(), _file()
    first = await start_settle_run(file, AGENT, runs=runs, ledger=ledger)
    second = await start_settle_run(file, AGENT, runs=runs, ledger=ledger)
    assert first == second
    assert len(runs.runs) == 1
    assert len(ledger.entries) == 1


async def test_cs021_refuses_a_file_of_another_entity(spans: InMemorySpanExporter) -> None:
    runs, ledger = InMemoryRunStore(), RecordingLedger()
    with pytest.raises(DomainError):
        await start_settle_run(_file("meridian-projects"), AGENT, runs=runs, ledger=ledger)
    assert runs.runs == {}
