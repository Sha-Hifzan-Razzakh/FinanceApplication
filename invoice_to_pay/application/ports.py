"""Ports: the Protocols the application depends on; adapters implement them."""

from typing import Protocol

from invoice_to_pay.contracts.common import EntityId
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.contracts.intake import FileRecord


class StoragePort(Protocol):
    """put/get/delete/presign bytes."""

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        """Store bytes under key (overwrites)."""
        ...

    async def get(self, key: str) -> bytes:
        """Return the bytes under key; KeyError when absent."""
        ...

    async def delete(self, key: str) -> None:
        """Remove the object under key."""
        ...

    async def presign(self, key: str, expires_in: int) -> str:
        """Time-limited download URL for key."""
        ...


class FileRecordStore(Protocol):
    """Persistence for FileRecord, unique per (entity, sha256)."""

    async def get_by_hash(self, entity: EntityId, sha256: str) -> FileRecord | None:
        """The entity's record for this hash, if stored."""
        ...

    async def insert(self, record: FileRecord) -> FileRecord:
        """Insert record; when the hash is already stored, return the existing record."""
        ...


class EventPublisher(Protocol):
    """Hands domain events to their transport."""

    async def publish(self, event: InvoiceReceived) -> None:
        """Publish one event."""
        ...


# TODO(T-108): Arq-backed EventPublisher adapter.
