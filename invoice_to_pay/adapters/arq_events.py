"""EventPublisher on Arq (Redis job queue)."""

import asyncio
from typing import Any

from arq.connections import RedisSettings, create_pool

from invoice_to_pay.application.ports import EventPublisher
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.observability.tracing import inject_trace

INVOICE_RECEIVED_JOB = "invoice_received_job"


class ArqEventPublisher(EventPublisher):
    """Enqueues InvoiceReceived for the intake worker, carrying the caller's trace context."""

    def __init__(self, redis_dsn: str, *, pool: Any = None) -> None:
        self._settings = RedisSettings.from_dsn(redis_dsn)
        self._pool = pool
        self._lock = asyncio.Lock()

    async def _get_pool(self) -> Any:
        async with self._lock:
            if self._pool is None:
                self._pool = await create_pool(self._settings)
            return self._pool

    async def publish(self, event: InvoiceReceived) -> None:
        """Enqueue one job per event; the event id keeps a retried enqueue from doubling up."""
        pool = await self._get_pool()
        await pool.enqueue_job(
            INVOICE_RECEIVED_JOB,
            event.model_dump(mode="json"),
            inject_trace(),
            _job_id=f"invoice-received:{event.event_id}",
        )

    async def close(self) -> None:
        """Close the Redis pool if one was opened."""
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None
