"""CS-011..013 RunLedger against Postgres."""

import asyncio
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from invoice_to_pay.control.ledger import RunLedger


async def _append_five(ledger: RunLedger, run_id: UUID) -> None:
    for i in range(5):
        await ledger.append(run_id, "decision", {"step": i})


async def _tamper(engine: AsyncEngine, sql: str, run_id: UUID) -> None:
    """Edit rows the way someone with direct database access would: around the trigger."""
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE itp.run_ledger DISABLE TRIGGER USER"))
        await conn.execute(text(sql), {"run_id": run_id})
        await conn.execute(text("ALTER TABLE itp.run_ledger ENABLE TRIGGER USER"))


async def test_cs012_append_persists_a_linked_chain(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    ledger = RunLedger(sessions, trace_id=lambda: "trace-abc")
    run_id = uuid4()
    first = await ledger.append(run_id, "decision", {"doc_type": "invoice"})
    second = await ledger.append(run_id, "action", {"tool": "get_vendor"})
    assert (first.seq, second.seq) == (1, 2)
    assert second.prev_hash == first.hash
    assert second.trace_id == "trace-abc"
    assert second.at.tzinfo is not None


async def test_cs012_runs_have_independent_chains(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    ledger = RunLedger(sessions, trace_id=lambda: "")
    a, b = uuid4(), uuid4()
    await ledger.append(a, "decision", {})
    first_b = await ledger.append(b, "decision", {})
    assert first_b.seq == 1
    assert first_b.prev_hash is None


async def test_cs012_concurrent_appends_keep_one_chain(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    ledger = RunLedger(sessions, trace_id=lambda: "")
    run_id = uuid4()
    entries = await asyncio.gather(*(ledger.append(run_id, "action", {"n": i}) for i in range(10)))
    assert sorted(e.seq for e in entries) == list(range(1, 11))
    assert await ledger.verify_chain(run_id) is True


async def test_cs013_untouched_chain_verifies(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    ledger = RunLedger(sessions, trace_id=lambda: "")
    run_id = uuid4()
    await _append_five(ledger, run_id)
    assert await ledger.verify_chain(run_id) is True


@pytest.mark.parametrize(
    "sql",
    [
        pytest.param(
            """UPDATE itp.run_ledger SET body = '{"step": 99}'
               WHERE run_id = :run_id AND seq = 3""",
            id="body",
        ),
        pytest.param(
            "UPDATE itp.run_ledger SET kind = 'approval' WHERE run_id = :run_id AND seq = 2",
            id="kind",
        ),
        pytest.param(
            "UPDATE itp.run_ledger SET at = at + interval '1 hour' "
            "WHERE run_id = :run_id AND seq = 4",
            id="at",
        ),
        pytest.param(
            "UPDATE itp.run_ledger SET trace_id = 'x' WHERE run_id = :run_id AND seq = 1",
            id="trace_id",
        ),
        pytest.param(
            "DELETE FROM itp.run_ledger WHERE run_id = :run_id AND seq = 2",
            id="delete-middle-row",
        ),
    ],
)
async def test_cs013_editing_any_row_fails_verification(
    engine: AsyncEngine,
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    sql: str,
) -> None:
    ledger = RunLedger(sessions, trace_id=lambda: "")
    run_id = uuid4()
    await _append_five(ledger, run_id)
    await _tamper(engine, sql, run_id)
    assert await ledger.verify_chain(run_id) is False


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE itp.run_ledger SET kind = 'x' WHERE run_id = :run_id",
        "DELETE FROM itp.run_ledger WHERE run_id = :run_id",
    ],
)
async def test_run_ledger_table_is_append_only(
    engine: AsyncEngine,
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    sql: str,
) -> None:
    run_id = uuid4()
    await RunLedger(sessions, trace_id=lambda: "").append(run_id, "decision", {})
    with pytest.raises(DBAPIError, match="append-only"):
        async with engine.begin() as conn:
            await conn.execute(text(sql), {"run_id": run_id})
