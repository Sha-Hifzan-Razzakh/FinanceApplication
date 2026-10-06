"""SqlRunStore against Postgres (itp.runs)."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from invoice_to_pay.adapters.sql_runs import SqlRunStore


async def test_start_creates_one_running_run_per_thread(
    engine: AsyncEngine,
    sessions: async_sessionmaker,  # type: ignore[type-arg]
) -> None:
    store = SqlRunStore(sessions)
    thread_id = f"meridian-supply:{uuid4()}"
    first, created = await store.start("meridian-supply", thread_id, "ap.settle_invoice")
    again, created_again = await store.start("meridian-supply", thread_id, "ap.settle_invoice")
    assert (created, created_again) == (True, False)
    assert again == first
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT entity, status, terminal, started_at FROM itp.runs WHERE id = :id"),
                {"id": first},
            )
        ).one()
    assert (row.entity, row.status, row.terminal) == ("meridian-supply", "running", None)
    assert row.started_at.tzinfo is not None


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE itp.runs SET status = 'sleeping' WHERE id = :id",
        "UPDATE itp.runs SET terminal = 'Exploded', status = 'finished' WHERE id = :id",
        "UPDATE itp.runs SET status = 'finished' WHERE id = :id",
        "UPDATE itp.runs SET terminal = 'Succeeded' WHERE id = :id",
    ],
)
async def test_status_and_terminal_vocabulary_is_enforced(
    engine: AsyncEngine,
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    sql: str,
) -> None:
    run_id, _ = await SqlRunStore(sessions).start(
        "meridian-supply", f"meridian-supply:{uuid4()}", "ap.settle_invoice"
    )
    with pytest.raises(IntegrityError):
        async with engine.begin() as conn:
            await conn.execute(text(sql), {"id": run_id})


async def test_finished_with_terminal_is_allowed(
    engine: AsyncEngine,
    sessions: async_sessionmaker,  # type: ignore[type-arg]
) -> None:
    run_id, _ = await SqlRunStore(sessions).start(
        "meridian-supply", f"meridian-supply:{uuid4()}", "ap.settle_invoice"
    )
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE itp.runs SET status = 'finished', terminal = 'Held', "
                "finished_at = now() WHERE id = :id"
            ),
            {"id": run_id},
        )
