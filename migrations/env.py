"""Alembic environment: async engine, schema itp."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from invoice_to_pay.control.ledger import metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = metadata


def _url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    from invoice_to_pay.config.settings import get_settings

    return str(get_settings().database_url)


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="itp",
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async() -> None:
    engine = create_async_engine(_url())
    async with engine.connect() as connection:
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS itp"))
        await connection.commit()
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(_run_async())
