"""CS-020 handle_invoice_received and its Arq job."""

from datetime import UTC, datetime
from typing import Any

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from invoice_to_pay.application.context import current_principal
from invoice_to_pay.contracts.common import Principal, uuid7
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.contracts.intake import UploadMeta
from invoice_to_pay.files.service import FileService
from invoice_to_pay.observability.tracing import inject_trace
from invoice_to_pay.workers.intake import (
    IntakeDeps,
    handle_invoice_received,
    invoice_received_job,
)
from tests.fakes.documents import OTHER_PDF, PDF
from tests.fakes.files import InMemoryFileRecordStore, InMemoryStorage, RecordingPublisher
from tests.fakes.runs import InMemoryRunStore, RecordingLedger

UPLOADER = Principal(subject="u-clerk-1", kind="user", entity="meridian-supply")
AGENT_SUBJECT = "agent:itp-test"


class _World:
    def __init__(self) -> None:
        self.records = InMemoryFileRecordStore()
        self.published = RecordingPublisher()
        self.files = FileService(
            storage=InMemoryStorage(), records=self.records, events=self.published
        )
        self.runs = InMemoryRunStore()
        self.ledger = RecordingLedger()
        self.deps = IntakeDeps(
            files=self.records, runs=self.runs, ledger=self.ledger, agent_subject=AGENT_SUBJECT
        )

    async def upload(self, data: bytes = PDF) -> InvoiceReceived:
        await self.files.put(data, UploadMeta(channel="scan"), UPLOADER)
        return self.published.events[-1]


@pytest.fixture
def world() -> _World:
    return _World()


async def test_cs020_event_starts_a_run(world: _World, spans: InMemorySpanExporter) -> None:
    evt = await world.upload()
    await handle_invoice_received(evt, world.deps)
    (run,) = world.runs.runs.values()
    assert run["entity"] == "meridian-supply"
    assert f"meridian-supply:{evt.file_id}" in world.runs.runs


async def test_done_when_redelivered_job_does_not_start_a_second_run(
    world: _World, spans: InMemorySpanExporter
) -> None:
    """Done when: a redelivered job does not start a second run."""
    evt = await world.upload()
    await handle_invoice_received(evt, world.deps)
    await handle_invoice_received(evt, world.deps)
    assert len(world.runs.runs) == 1
    assert len(world.ledger.entries) == 1


async def test_cs020_duplicate_upload_event_does_not_start_a_second_run(
    world: _World, spans: InMemorySpanExporter
) -> None:
    first = await world.upload()
    again = await world.upload()  # same bytes: FileService re-emits for the first record
    assert again.event_id != first.event_id and again.file_id == first.file_id
    await handle_invoice_received(first, world.deps)
    await handle_invoice_received(again, world.deps)
    assert len(world.runs.runs) == 1


async def test_cs020_different_files_get_different_runs(
    world: _World, spans: InMemorySpanExporter
) -> None:
    await handle_invoice_received(await world.upload(PDF), world.deps)
    await handle_invoice_received(await world.upload(OTHER_PDF), world.deps)
    assert len(world.runs.runs) == 2


async def test_cs020_runs_as_the_agent_for_the_event_entity(
    world: _World, spans: InMemorySpanExporter, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[Principal] = []

    async def spy(file: Any, p: Principal, **kwargs: Any) -> Any:
        seen.append(p)
        assert current_principal.get() == p
        return uuid7()

    monkeypatch.setattr("invoice_to_pay.workers.intake.start_settle_run", spy)
    await handle_invoice_received(await world.upload(), world.deps)
    (p,) = seen
    assert (p.subject, p.kind, p.entity) == (AGENT_SUBJECT, "agent", "meridian-supply")
    with pytest.raises(LookupError):
        current_principal.get()


async def test_cs020_event_for_unknown_file_starts_nothing(
    world: _World, spans: InMemorySpanExporter
) -> None:
    evt = InvoiceReceived(
        event_id=uuid7(),
        entity="meridian-supply",
        file_id=uuid7(),
        sha256="d" * 64,
        channel="scan",
        occurred_at=datetime.now(UTC),
    )
    await handle_invoice_received(evt, world.deps)
    assert world.runs.runs == {}


async def test_cs020_event_cannot_reach_another_entitys_file(
    world: _World, spans: InMemorySpanExporter
) -> None:
    evt = await world.upload()
    forged = evt.model_copy(update={"entity": "meridian-projects"})
    await handle_invoice_received(forged, world.deps)
    assert world.runs.runs == {}


async def test_cs020_job_validates_payload_and_continues_the_upload_trace(
    world: _World, spans: InMemorySpanExporter
) -> None:
    evt = await world.upload()
    with trace.get_tracer("test").start_as_current_span("POST /invoices/upload") as upload:
        carrier = inject_trace()
    await invoice_received_job({"intake": world.deps}, evt.model_dump(mode="json"), carrier)
    (run_span,) = [s for s in spans.get_finished_spans() if s.name == "run"]
    assert run_span.context.trace_id == upload.get_span_context().trace_id
    assert len(world.runs.runs) == 1


async def test_cs020_job_rejects_a_malformed_payload(world: _World) -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        await invoice_received_job({"intake": world.deps}, {"file_id": "nope"}, None)
