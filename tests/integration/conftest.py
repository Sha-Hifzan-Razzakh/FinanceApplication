"""Integration fixtures: a migrated test database on the local stack."""

import asyncio
import os
from collections.abc import AsyncIterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.environ.get(
    "ITP_TEST_DATABASE_URL",
    "postgresql+asyncpg://itp:itp-local-only@localhost:5432/itp_test",
)


async def _ensure_database(url: str) -> None:
    target = make_url(url)
    admin = create_async_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": target.database},
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{target.database}"'))
    finally:
        await admin.dispose()


@pytest.fixture(scope="session")
def migrated_database_url() -> str:
    """Create the test database if needed and migrate it to head."""
    asyncio.run(_ensure_database(TEST_DATABASE_URL))
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(config, "head")
    return TEST_DATABASE_URL


@pytest.fixture
async def engine(migrated_database_url: str) -> AsyncIterator[AsyncEngine]:
    """Async engine on the migrated test database."""
    eng = create_async_engine(migrated_database_url)
    yield eng
    await eng.dispose()


@pytest.fixture
def sessions(engine: AsyncEngine) -> async_sessionmaker:  # type: ignore[type-arg]
    """Session factory bound to the test engine."""
    return async_sessionmaker(engine, expire_on_commit=False)
