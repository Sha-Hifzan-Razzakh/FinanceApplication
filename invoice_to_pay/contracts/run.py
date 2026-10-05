"""Run and control records."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LedgerEntry(BaseModel):
    """One hash-chained ledger row."""

    model_config = ConfigDict(frozen=True)

    run_id: UUID
    seq: int = Field(ge=1)
    kind: str = Field(description="e.g. decision, action, observation, approval")
    body: dict[str, Any]
    prev_hash: str | None
    hash: str = Field(description="sha256(prev_hash + canonical row)")
    trace_id: str
    at: datetime
