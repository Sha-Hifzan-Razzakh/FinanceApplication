"""Ports: the Protocols the application depends on; adapters implement them."""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel

from invoice_to_pay.contracts.common import EntityId
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.contracts.intake import FileRecord
from invoice_to_pay.contracts.run import LedgerEntry


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

    async def get(self, entity: EntityId, file_id: UUID) -> FileRecord | None:
        """The entity's record with this id, if any."""
        ...

    async def insert(self, record: FileRecord) -> FileRecord:
        """Insert record; when the hash is already stored, return the existing record."""
        ...


class EventPublisher(Protocol):
    """Hands domain events to their transport."""

    async def publish(self, event: InvoiceReceived) -> None:
        """Publish one event."""
        ...


class DecisionPort(Protocol):
    """Typed decisions without text generation."""

    async def decide[T: BaseModel](self, schema: type[T], payload: str) -> T:
        """Answer the typed question that schema describes about payload."""
        ...


class StructuredOutputError(ValueError):
    """The model's reply could not be read into the requested schema."""


class LLMPort(Protocol):
    """The only way the app reaches a language model."""

    async def structured[T: BaseModel](
        self, prompt_id: str, vars: Mapping[str, Any], schema: type[T]
    ) -> T:
        """Fill prompt_id with vars and return the model's reply as schema.

        Raises StructuredOutputError when the reply does not fit schema.
        """
        ...

    def prompt_version(self, prompt_id: str) -> str:
        """The version of prompt_id that structured() uses; recorded in the ledger."""
        ...

    # TODO(T-305): chat_with_tools once a task defines ToolCall (DEBT-012)


class DocumentLike(Protocol):
    """What the application reads from a document block: its text and metadata."""

    @property
    def text(self) -> str:
        """The block's text."""
        ...

    @property
    def metadata(self) -> Mapping[str, Any]:
        """file_id, pages (1-based) and kind ('text' or 'table')."""
        ...


ReadDocuments = Callable[[FileRecord], Awaitable[Sequence[DocumentLike]]]
"""Layout-aware blocks of a stored file, in reading order (adapters.llamaindex_reader.read_pdf)."""


class RunStore(Protocol):
    """Run rows: at most one run per thread_id (entity:file_id)."""

    async def start(self, entity: EntityId, thread_id: str, goal_type: str) -> tuple[UUID, bool]:
        """Create the running run for thread_id, or return the existing one; bool = created."""
        ...


class LedgerWriter(Protocol):
    """Appends to a run's hash-chained ledger (control.ledger.RunLedger)."""

    async def append(self, run_id: UUID, kind: str, body: Mapping[str, Any]) -> LedgerEntry:
        """Append one entry and return it."""
        ...
