"""File service: store each file once per entity and announce it."""

import hashlib
from datetime import UTC, datetime
from typing import get_args
from uuid import UUID

import magic

from invoice_to_pay.application.ports import EventPublisher, FileRecordStore, StoragePort
from invoice_to_pay.contracts.common import Principal, uuid7
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.contracts.intake import FileRecord, MimeType, UploadMeta

ALLOWED_MIME_TYPES: frozenset[str] = frozenset(get_args(MimeType))


def sniff_mime(data: bytes) -> str:
    """MIME type read from the bytes themselves (libmagic), never from the client's claim."""
    mime: str = magic.from_buffer(data, mime=True)
    return mime


class FileService:
    """Stores bytes by sha256 under an entity-prefixed key and writes a FileRecord."""

    def __init__(
        self, *, storage: StoragePort, records: FileRecordStore, events: EventPublisher
    ) -> None:
        self._storage = storage
        self._records = records
        self._events = events

    async def put(self, data: bytes, meta: UploadMeta, p: Principal) -> tuple[FileRecord, bool]:
        """sha256, sniff mime, dedupe, store, write FileRecord, emit InvoiceReceived.

        Returns the stored record and whether the hash was already stored for the entity.
        """
        sha = hashlib.sha256(data).hexdigest()
        existing = await self._records.get_by_hash(p.entity, sha)
        if existing is not None:
            await self._emit(existing)
            return existing, True

        # Validating the record first refuses unsupported or oversized files before storing.
        record = FileRecord.model_validate(
            {
                "id": uuid7(),
                "entity": p.entity,
                "sha256": sha,
                "channel": meta.channel,
                "sender": meta.sender,
                "object_key": f"{p.entity}/{sha}",
                "mime_type": sniff_mime(data),
                "size_bytes": len(data),
                "untrusted_text_id": meta.untrusted_text_id,
                "received_at": datetime.now(UTC),
            }
        )
        await self._storage.put(record.object_key, data, record.mime_type)
        stored = await self._records.insert(record)
        await self._emit(stored)
        return stored, stored.id != record.id

    async def get(self, file_id: UUID, p: Principal) -> FileRecord | None:
        """The caller's entity's record with this id; another entity's file reads as absent."""
        return await self._records.get(p.entity, file_id)

    async def _emit(self, record: FileRecord) -> None:
        await self._events.publish(
            InvoiceReceived(
                event_id=uuid7(),
                entity=record.entity,
                file_id=record.id,
                sha256=record.sha256,
                channel=record.channel,
                occurred_at=datetime.now(UTC),
            )
        )
