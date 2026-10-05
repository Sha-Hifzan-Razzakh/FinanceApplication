"""Append-only, hash-chained run ledger (audit trail)."""

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic_core import to_jsonable_python
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Uuid,
    insert,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from invoice_to_pay.contracts.run import LedgerEntry

metadata = MetaData(schema="itp")

run_ledger = Table(
    "run_ledger",
    metadata,
    Column("run_id", Uuid, primary_key=True),
    Column("seq", Integer, primary_key=True),
    Column("kind", String, nullable=False),
    Column("body", JSONB, nullable=False),
    Column("prev_hash", String(64)),
    Column("hash", String(64), nullable=False),
    Column("trace_id", String, nullable=False),
    Column("at", DateTime(timezone=True), nullable=False),
)


def entry_hash(
    prev_hash: str | None,
    run_id: UUID,
    seq: int,
    kind: str,
    body: Mapping[str, Any],
    trace_id: str,
    at: datetime,
) -> str:
    """sha256 of the previous hash followed by the canonical JSON of every other column."""
    canonical = json.dumps(
        {
            "run_id": str(run_id),
            "seq": seq,
            "kind": kind,
            "body": body,
            "trace_id": trace_id,
            "at": at.astimezone(UTC).isoformat(),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(((prev_hash or "") + canonical).encode()).hexdigest()


def next_entry(
    prev: LedgerEntry | None,
    *,
    run_id: UUID,
    kind: str,
    body: Mapping[str, Any],
    trace_id: str,
    at: datetime,
) -> LedgerEntry:
    """Build the entry that follows prev (or starts the chain), with its hash."""
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("ledger time must be timezone-aware")
    clean: dict[str, Any] = to_jsonable_python(dict(body))
    seq = 1 if prev is None else prev.seq + 1
    prev_hash = None if prev is None else prev.hash
    return LedgerEntry(
        run_id=run_id,
        seq=seq,
        kind=kind,
        body=clean,
        prev_hash=prev_hash,
        hash=entry_hash(prev_hash, run_id, seq, kind, clean, trace_id, at),
        trace_id=trace_id,
        at=at,
    )


def verify_entries(entries: Sequence[LedgerEntry]) -> bool:
    """True when entries form one unbroken chain from seq 1 with every hash recomputing."""
    prev_hash: str | None = None
    run_id = entries[0].run_id if entries else None
    for expected_seq, e in enumerate(entries, start=1):
        if e.run_id != run_id or e.seq != expected_seq or e.prev_hash != prev_hash:
            return False
        if e.hash != entry_hash(e.prev_hash, e.run_id, e.seq, e.kind, e.body, e.trace_id, e.at):
            return False
        prev_hash = e.hash
    return True


def _no_trace() -> str:
    return ""


class RunLedger:
    """Append-only hash-chained ledger per run."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        trace_id: Callable[[], str] = _no_trace,  # TODO(T-105): current OpenTelemetry trace id
    ) -> None:
        self._sessions = sessions
        self._trace_id = trace_id

    async def append(self, run_id: UUID, kind: str, body: Mapping[str, Any]) -> LedgerEntry:
        """Hash body with previous hash and insert."""
        async with self._sessions() as session, session.begin():
            # Serialise appends per run so two writers never claim the same seq.
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                {"key": str(run_id)},
            )
            last = await session.execute(
                select(run_ledger)
                .where(run_ledger.c.run_id == run_id)
                .order_by(run_ledger.c.seq.desc())
                .limit(1)
            )
            row = last.mappings().first()
            prev = None if row is None else LedgerEntry.model_validate(dict(row))
            entry = next_entry(
                prev,
                run_id=run_id,
                kind=kind,
                body=body,
                trace_id=self._trace_id(),
                at=datetime.now(UTC),
            )
            await session.execute(insert(run_ledger).values(**entry.model_dump()))
        return entry

    async def verify_chain(self, run_id: UUID) -> bool:
        """Recompute every hash; detect edits."""
        async with self._sessions() as session:
            result = await session.execute(
                select(run_ledger).where(run_ledger.c.run_id == run_id).order_by(run_ledger.c.seq)
            )
            entries = [LedgerEntry.model_validate(dict(r)) for r in result.mappings()]
        return verify_entries(entries)
