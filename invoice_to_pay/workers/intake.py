"""Intake job: one run per stored file."""

from dataclasses import dataclass
from typing import Any

import structlog

from invoice_to_pay.application.context import current_principal
from invoice_to_pay.application.ports import FileRecordStore, LedgerWriter, RunStore
from invoice_to_pay.application.use_cases.settle_invoice import start_settle_run
from invoice_to_pay.contracts.common import Principal
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.observability.tracing import attached_trace

log = structlog.get_logger()


@dataclass(frozen=True)
class IntakeDeps:
    """What the intake job needs; built once per worker process."""

    files: FileRecordStore
    runs: RunStore
    ledger: LedgerWriter
    agent_subject: str


async def handle_invoice_received(evt: InvoiceReceived, deps: IntakeDeps) -> None:
    """Start one run per file hash (idempotent)."""
    principal = Principal(subject=deps.agent_subject, kind="agent", entity=evt.entity)
    token = current_principal.set(principal)
    try:
        file = await deps.files.get(evt.entity, evt.file_id)
        if file is None or file.sha256 != evt.sha256:
            log.warning("intake_file_not_found", file_id=str(evt.file_id), entity=evt.entity)
            return
        run_id = await start_settle_run(file, principal, runs=deps.runs, ledger=deps.ledger)
        log.info("intake_handled", run_id=str(run_id), file_id=str(file.id))
    finally:
        current_principal.reset(token)


async def invoice_received_job(
    ctx: dict[str, Any], event: dict[str, Any], trace: dict[str, str] | None = None
) -> None:
    """Arq job: validate the event, continue the publisher's trace, handle it."""
    evt = InvoiceReceived.model_validate(event)
    with attached_trace(trace or {}):
        await handle_invoice_received(evt, ctx["intake"])
