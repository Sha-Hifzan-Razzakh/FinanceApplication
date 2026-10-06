"""Intake end to end on the local stack: event -> Redis/Arq -> worker -> one run in Postgres."""

import os
from collections.abc import AsyncIterator
from typing import Any

import pytest
from arq.connections import ArqRedis, RedisSettings, create_pool
from arq.worker import Worker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from invoice_to_pay.adapters.arq_events import INVOICE_RECEIVED_JOB, ArqEventPublisher
from invoice_to_pay.adapters.sql_file_records import SqlFileRecordStore
from invoice_to_pay.adapters.sql_runs import SqlRunStore
from invoice_to_pay.contracts.common import Principal
from invoice_to_pay.contracts.intake import UploadMeta
from invoice_to_pay.control.ledger import RunLedger
from invoice_to_pay.files.service import FileService
from invoice_to_pay.observability.tracing import current_trace_id
from invoice_to_pay.workers.intake import IntakeDeps, invoice_received_job
from tests.fakes.files import InMemoryStorage

REDIS_DSN = os.environ.get("ITP_TEST_REDIS_URL", "redis://localhost:6379/15")
UPLOADER = Principal(subject="u-clerk-1", kind="user", entity="meridian-supply")


@pytest.fixture
async def redis() -> AsyncIterator[ArqRedis]:
    pool = await create_pool(RedisSettings.from_dsn(REDIS_DSN))
    await pool.flushdb()
    yield pool
    await pool.flushdb()
    await pool.aclose()


async def _drain(deps: IntakeDeps) -> None:
    worker = Worker(
        functions=[invoice_received_job],
        redis_settings=RedisSettings.from_dsn(REDIS_DSN),
        burst=True,
        poll_delay=0.05,
        ctx={"intake": deps},
        handle_signals=False,
    )
    try:
        await worker.main()
    finally:
        await worker.close()


async def test_done_when_redelivered_and_duplicate_jobs_start_one_run(
    engine: AsyncEngine,
    sessions: async_sessionmaker,  # type: ignore[type-arg]
    redis: ArqRedis,
    spans: Any,
) -> None:
    records = SqlFileRecordStore(sessions)
    publisher = ArqEventPublisher(REDIS_DSN)
    files = FileService(storage=InMemoryStorage(), records=records, events=publisher)
    ledger = RunLedger(sessions, trace_id=current_trace_id)
    deps = IntakeDeps(
        files=records, runs=SqlRunStore(sessions), ledger=ledger, agent_subject="agent:test"
    )

    unique_pdf = b"%PDF-1.4\n" + os.urandom(32) + b"\n%%EOF\n"
    record, _ = await files.put(unique_pdf, UploadMeta(channel="scan"), UPLOADER)
    await files.put(unique_pdf, UploadMeta(channel="scan"), UPLOADER)  # duplicate upload
    # Redelivery: the same event again under a different job id.
    evt_jobs = await redis.queued_jobs()
    first_args = evt_jobs[0].args
    await redis.enqueue_job(INVOICE_RECEIVED_JOB, *first_args, _job_id="redelivered")
    await publisher.close()
    assert len(await redis.queued_jobs()) == 3

    await _drain(deps)

    async with engine.connect() as conn:
        runs = (
            await conn.execute(
                text("SELECT id, thread_id, status FROM itp.runs WHERE thread_id = :t"),
                {"t": f"meridian-supply:{record.id}"},
            )
        ).all()
    assert len(runs) == 1
    assert runs[0].status == "running"
    assert await ledger.verify_chain(runs[0].id) is True
