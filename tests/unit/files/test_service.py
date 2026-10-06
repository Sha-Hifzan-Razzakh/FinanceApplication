"""CS-018 FileService.put. TS-04 lives here."""

import hashlib

import pytest
from pydantic import ValidationError

from invoice_to_pay.contracts.common import Principal
from invoice_to_pay.contracts.intake import UploadMeta
from invoice_to_pay.files.service import FileService
from tests.fakes.documents import OTHER_PDF, PDF, PNG, TEXT
from tests.fakes.files import InMemoryFileRecordStore, InMemoryStorage, RecordingPublisher

SUPPLY = Principal(subject="u-clerk-1", kind="user", entity="meridian-supply")
PROJECTS = Principal(subject="u-pm-1", kind="user", entity="meridian-projects")
SCAN = UploadMeta(channel="scan")


@pytest.fixture
def storage() -> InMemoryStorage:
    return InMemoryStorage()


@pytest.fixture
def records() -> InMemoryFileRecordStore:
    return InMemoryFileRecordStore()


@pytest.fixture
def events() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture
def service(
    storage: InMemoryStorage, records: InMemoryFileRecordStore, events: RecordingPublisher
) -> FileService:
    return FileService(storage=storage, records=records, events=events)


async def test_ts04_same_file_stored_once(
    service: FileService, storage: InMemoryStorage, records: InMemoryFileRecordStore
) -> None:
    """TS-04: the same bytes twice give one FileRecord, duplicate=True the second time."""
    first, first_dup = await service.put(PDF, SCAN, SUPPLY)
    second, second_dup = await service.put(PDF, UploadMeta(channel="email"), SUPPLY)
    assert (first_dup, second_dup) == (False, True)
    assert second == first
    assert len(records.records) == 1
    assert len(storage.objects) == 1


async def test_cs018_record_carries_provenance(service: FileService) -> None:
    meta = UploadMeta(channel="portal", sender="Gulf Steel portal")
    record, _ = await service.put(PDF, meta, SUPPLY)
    sha = hashlib.sha256(PDF).hexdigest()
    assert record.entity == "meridian-supply"
    assert record.sha256 == sha
    assert record.object_key == f"meridian-supply/{sha}"
    assert record.mime_type == "application/pdf"
    assert record.size_bytes == len(PDF)
    assert record.channel == "portal"
    assert record.sender == "Gulf Steel portal"
    assert record.status == "stored"
    assert record.id.version == 7
    assert record.received_at.tzinfo is not None


async def test_cs018_bytes_are_stored_under_the_entity_key(
    service: FileService, storage: InMemoryStorage
) -> None:
    record, _ = await service.put(PNG, SCAN, SUPPLY)
    assert storage.objects[record.object_key] == (PNG, "image/png")


async def test_cs018_emits_invoice_received(
    service: FileService, events: RecordingPublisher
) -> None:
    record, _ = await service.put(PDF, SCAN, SUPPLY)
    (evt,) = events.events
    assert (evt.entity, evt.file_id, evt.sha256, evt.channel) == (
        "meridian-supply",
        record.id,
        record.sha256,
        "scan",
    )
    assert evt.occurred_at.tzinfo is not None


async def test_cs018_duplicate_emits_again_for_the_first_record(
    service: FileService, events: RecordingPublisher
) -> None:
    record, _ = await service.put(PDF, SCAN, SUPPLY)
    await service.put(PDF, SCAN, SUPPLY)
    assert [e.file_id for e in events.events] == [record.id, record.id]
    assert events.events[0].event_id != events.events[1].event_id


async def test_cs018_different_bytes_are_different_files(service: FileService) -> None:
    a, _ = await service.put(PDF, SCAN, SUPPLY)
    b, dup = await service.put(OTHER_PDF, SCAN, SUPPLY)
    assert a.id != b.id
    assert dup is False


async def test_cs018_dedupe_is_per_entity(
    service: FileService, records: InMemoryFileRecordStore
) -> None:
    supply, _ = await service.put(PDF, SCAN, SUPPLY)
    projects, dup = await service.put(PDF, SCAN, PROJECTS)
    assert dup is False
    assert projects.id != supply.id
    assert projects.object_key.startswith("meridian-projects/")
    assert len(records.records) == 2


async def test_cs018_lost_insert_race_returns_the_winner(
    service: FileService, records: InMemoryFileRecordStore
) -> None:
    winner, _ = await service.put(PDF, SCAN, SUPPLY)

    async def no_hit(entity: str, sha256: str) -> None:
        return None

    records.get_by_hash = no_hit  # type: ignore[method-assign]  # simulate the race window
    record, dup = await service.put(PDF, SCAN, SUPPLY)
    assert dup is True
    assert record == winner


@pytest.mark.parametrize("data", [TEXT, b""])
async def test_cs018_unsupported_or_empty_file_is_refused_before_storing(
    service: FileService,
    storage: InMemoryStorage,
    events: RecordingPublisher,
    data: bytes,
) -> None:
    with pytest.raises(ValidationError):
        await service.put(data, SCAN, SUPPLY)
    assert storage.objects == {}
    assert events.events == []


async def test_get_returns_own_entity_record_only(service: FileService) -> None:
    record, _ = await service.put(PDF, SCAN, SUPPLY)
    assert await service.get(record.id, SUPPLY) == record
    assert await service.get(record.id, PROJECTS) is None


def test_sniff_mime_reads_the_bytes() -> None:
    from invoice_to_pay.files.service import sniff_mime

    assert sniff_mime(PDF) == "application/pdf"
    assert sniff_mime(PNG) == "image/png"
    assert sniff_mime(TEXT) == "text/plain"
