"""FileRecordStore on Postgres (itp.file_records)."""

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Uuid, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from invoice_to_pay.application.ports import FileRecordStore
from invoice_to_pay.contracts.common import EntityId
from invoice_to_pay.contracts.intake import FileRecord

metadata = MetaData(schema="itp")

file_records = Table(
    "file_records",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("entity", String, nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("channel", String, nullable=False),
    Column("sender", String),
    Column("object_key", String, nullable=False),
    Column("mime_type", String, nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("untrusted_text_id", Uuid),
    Column("received_at", DateTime(timezone=True), nullable=False),
    Column("status", String, nullable=False),
)


class SqlFileRecordStore(FileRecordStore):
    """FileRecord persistence; UNIQUE(entity, sha256) makes the first insert win."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def get_by_hash(self, entity: EntityId, sha256: str) -> FileRecord | None:
        """The entity's record for this hash, if stored."""
        async with self._sessions() as session:
            row = (
                (
                    await session.execute(
                        select(file_records).where(
                            file_records.c.entity == entity, file_records.c.sha256 == sha256
                        )
                    )
                )
                .mappings()
                .first()
            )
        return None if row is None else FileRecord.model_validate(dict(row))

    async def insert(self, record: FileRecord) -> FileRecord:
        """Insert record; when the hash is already stored, return the existing record."""
        async with self._sessions() as session, session.begin():
            inserted = (
                await session.execute(
                    insert(file_records)
                    .values(**record.model_dump())
                    .on_conflict_do_nothing(index_elements=["entity", "sha256"])
                    .returning(file_records.c.id)
                )
            ).first()
        if inserted is not None:
            return record
        existing = await self.get_by_hash(record.entity, record.sha256)
        if existing is None:  # pragma: no cover - conflict implies a row
            raise RuntimeError("file_records conflict without an existing row")
        return existing
