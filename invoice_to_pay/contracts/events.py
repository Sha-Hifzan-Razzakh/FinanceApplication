"""Domain events (Events sheet)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from invoice_to_pay.contracts.common import EntityId


class InvoiceReceived(BaseModel):
    """A new file is stored and ready for a run."""

    model_config = ConfigDict(frozen=True)

    event_id: UUID
    entity: EntityId
    file_id: UUID
    sha256: str
    channel: str
    occurred_at: datetime
