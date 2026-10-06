"""SqlFileRecordStore against Postgres (file_records)."""

import hashlib
import os
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from invoice_to_pay.adapters.sql_file_records import SqlFileRecordStore
from invoice_to_pay.contracts.common import EntityId, uuid7
from invoice_to_pay.contracts.intake import FileRecord


def _record(entity: EntityId, sha: str, **overrides: object) -> FileRecord:
    fields: dict[str, object] = {
        "id": uuid7(),
        "entity": entity,
        "sha256": sha,
        "channel": "email",
        "sender": "ap@gulfsteel.example",
        "object_key": f"{entity}/{sha}",
        "mime_type": "application/pdf",
        "size_bytes": 2048,
        "received_at": datetime.now(UTC),
    }
    fields.update(overrides)
    return FileRecord.model_validate(fields)


@pytest.fixture
def sha() -> str:
    return hashlib.sha256(os.urandom(16)).hexdigest()


async def test_insert_then_get_by_hash_round_trips(
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    sha: str,
) -> None:
    store = SqlFileRecordStore(sessions)
    record = _record("meridian-supply", sha)
    assert await store.insert(record) == record
    assert await store.get_by_hash("meridian-supply", sha) == record


async def test_second_insert_of_same_hash_returns_the_first(
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    sha: str,
) -> None:
    store = SqlFileRecordStore(sessions)
    first = await store.insert(_record("meridian-supply", sha))
    again = await store.insert(_record("meridian-supply", sha, channel="portal"))
    assert again == first


async def test_hash_lookup_is_scoped_to_the_entity(
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    sha: str,
) -> None:
    store = SqlFileRecordStore(sessions)
    await store.insert(_record("meridian-supply", sha))
    assert await store.get_by_hash("meridian-projects", sha) is None
    projects = await store.insert(_record("meridian-projects", sha))
    assert projects.entity == "meridian-projects"
    assert await store.get_by_hash("meridian-supply", sha) != projects


async def test_get_by_id_is_scoped_to_the_entity(
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    sha: str,
) -> None:
    store = SqlFileRecordStore(sessions)
    record = await store.insert(_record("meridian-supply", sha))
    assert await store.get("meridian-supply", record.id) == record
    assert await store.get("meridian-projects", record.id) is None
    assert await store.get("meridian-supply", uuid7()) is None
