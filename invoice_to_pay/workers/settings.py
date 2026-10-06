"""Arq worker settings: `make worker` runs WorkerSettings."""

from collections.abc import Callable
from typing import Any, ClassVar

from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from invoice_to_pay.adapters.sql_file_records import SqlFileRecordStore
from invoice_to_pay.adapters.sql_runs import SqlRunStore
from invoice_to_pay.config.settings import get_settings
from invoice_to_pay.control.ledger import RunLedger
from invoice_to_pay.observability.tracing import current_trace_id, setup_logging, setup_tracing
from invoice_to_pay.workers.intake import IntakeDeps, invoice_received_job


async def startup(ctx: dict[str, Any]) -> None:
    """Open the database pool and build the job dependencies."""
    settings = get_settings()
    setup_logging()
    setup_tracing(settings)
    engine = create_async_engine(str(settings.database_url), pool_pre_ping=True)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    ctx["engine"] = engine
    ctx["intake"] = IntakeDeps(
        files=SqlFileRecordStore(sessions),
        runs=SqlRunStore(sessions),
        ledger=RunLedger(sessions, trace_id=current_trace_id),
        agent_subject=settings.agent_subject,
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    """Close the database pool."""
    await ctx["engine"].dispose()


class WorkerSettings:
    """Arq configuration; Redis from ITP_REDIS_URL."""

    functions: ClassVar[list[Callable[..., Any]]] = [invoice_received_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(str(get_settings().redis_url))
