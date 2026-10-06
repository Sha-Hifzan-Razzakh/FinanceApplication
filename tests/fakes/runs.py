"""In-memory fakes for the run store and the ledger writer."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from invoice_to_pay.contracts.common import EntityId, uuid7
from invoice_to_pay.contracts.run import LedgerEntry
from invoice_to_pay.control.ledger import next_entry


class InMemoryRunStore:
    """RunStore fake: one run per thread_id, first start wins."""

    def __init__(self) -> None:
        self.runs: dict[str, dict[str, Any]] = {}

    async def start(self, entity: EntityId, thread_id: str, goal_type: str) -> tuple[UUID, bool]:
        if thread_id in self.runs:
            return self.runs[thread_id]["id"], False
        run_id = uuid7()
        self.runs[thread_id] = {
            "id": run_id,
            "entity": entity,
            "goal_type": goal_type,
            "status": "running",
        }
        return run_id, True


class RecordingLedger:
    """LedgerWriter fake that chains entries in memory and records the trace id it saw."""

    def __init__(self, trace_id: Any = lambda: "") -> None:
        self.entries: list[LedgerEntry] = []
        self._trace_id = trace_id

    async def append(self, run_id: UUID, kind: str, body: Mapping[str, Any]) -> LedgerEntry:
        prev = next((e for e in reversed(self.entries) if e.run_id == run_id), None)
        entry = next_entry(
            prev,
            run_id=run_id,
            kind=kind,
            body=body,
            trace_id=self._trace_id(),
            at=datetime.now(UTC),
        )
        self.entries.append(entry)
        return entry
