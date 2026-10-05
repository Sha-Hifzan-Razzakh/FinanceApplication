"""In-memory fakes for the storage, file-record and event ports."""

from invoice_to_pay.contracts.common import EntityId
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.contracts.intake import FileRecord


class InMemoryStorage:
    """StoragePort fake: a dict of key -> (bytes, content type)."""

    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)

    async def get(self, key: str) -> bytes:
        return self.objects[key][0]

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    async def presign(self, key: str, expires_in: int) -> str:
        return f"memory://{key}?expires_in={expires_in}"


class InMemoryFileRecordStore:
    """FileRecordStore fake keyed by (entity, sha256), first insert wins."""

    def __init__(self) -> None:
        self.records: dict[tuple[str, str], FileRecord] = {}

    async def get_by_hash(self, entity: EntityId, sha256: str) -> FileRecord | None:
        return self.records.get((entity, sha256))

    async def insert(self, record: FileRecord) -> FileRecord:
        return self.records.setdefault((record.entity, record.sha256), record)


class RecordingPublisher:
    """EventPublisher fake that keeps every published event."""

    def __init__(self) -> None:
        self.events: list[InvoiceReceived] = []

    async def publish(self, event: InvoiceReceived) -> None:
        self.events.append(event)
