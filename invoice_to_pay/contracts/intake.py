"""Intake contracts: stored files and upload metadata."""

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from invoice_to_pay.contracts.common import EntityId

Channel = Literal["email", "portal", "scan"]
MimeType = Literal["application/pdf", "image/png", "image/jpeg", "image/tiff"]
MAX_UPLOAD_BYTES = 20_000_000
"""Largest file the program accepts; FileRecord.size_bytes and the upload route share it."""


class FileRecord(BaseModel):
    """One stored file with its provenance."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    entity: EntityId
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$", description="Dedupe key")
    channel: Channel = Field(description="Where it came from")
    sender: str | None = Field(default=None, description="Email sender or portal name")
    object_key: str = Field(description="Key in object storage; starts with entity/")
    mime_type: MimeType
    size_bytes: int = Field(gt=0, le=MAX_UPLOAD_BYTES)
    untrusted_text_id: UUID | None = Field(
        default=None, description="Email body / transcript stored as untrusted text"
    )
    received_at: datetime
    status: Literal["stored", "processing", "done", "held", "rejected"] = "stored"

    @model_validator(mode="after")
    def _key_under_entity(self) -> Self:
        """The object key lives under the record's own entity prefix."""
        if not self.object_key.startswith(f"{self.entity}/"):
            raise ValueError("object_key must start with the record's entity/")
        return self


class UploadMeta(BaseModel):
    """What the caller knows about an incoming file; the entity always comes from the Principal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    channel: Channel
    sender: str | None = None
    untrusted_text_id: UUID | None = None


class UploadResponse(BaseModel):
    """Result of POST /invoices/upload."""

    file_id: UUID
    run_id: UUID | None = Field(default=None, description="Set when a run started")
    duplicate: bool = Field(default=False, description="True if the hash was already stored")
