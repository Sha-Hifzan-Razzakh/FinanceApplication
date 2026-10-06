"""RunStore on Postgres (itp.runs)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, MetaData, String, Table, Uuid, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from invoice_to_pay.application.ports import RunStore
from invoice_to_pay.contracts.common import EntityId, uuid7

metadata = MetaData(schema="itp")

runs = Table(
    "runs",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("entity", String, nullable=False),
    Column("thread_id", String, nullable=False, unique=True),
    Column("goal_type", String, nullable=False),
    Column("status", String, nullable=False),
    Column("terminal", String),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True)),
)


class SqlRunStore(RunStore):
    """One run per thread_id; UNIQUE(thread_id) makes the first start win."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def start(self, entity: EntityId, thread_id: str, goal_type: str) -> tuple[UUID, bool]:
        """Create the running run for thread_id, or return the existing one; bool = created."""
        candidate = uuid7()
        async with self._sessions() as session, session.begin():
            inserted = (
                await session.execute(
                    insert(runs)
                    .values(
                        id=candidate,
                        entity=entity,
                        thread_id=thread_id,
                        goal_type=goal_type,
                        status="running",
                        started_at=datetime.now(UTC),
                    )
                    .on_conflict_do_nothing(index_elements=["thread_id"])
                    .returning(runs.c.id)
                )
            ).scalar_one_or_none()
            if inserted is not None:
                return inserted, True
            existing = (
                await session.execute(select(runs.c.id).where(runs.c.thread_id == thread_id))
            ).scalar_one()
        return existing, False
