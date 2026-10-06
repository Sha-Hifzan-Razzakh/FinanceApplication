"""Use case: settle one invoice file."""

from uuid import UUID

from invoice_to_pay.application.context import current_principal
from invoice_to_pay.application.ports import LedgerWriter, RunStore
from invoice_to_pay.contracts.common import Principal
from invoice_to_pay.contracts.intake import FileRecord
from invoice_to_pay.control.errors import DomainError
from invoice_to_pay.observability.tracing import run_span

GOAL_TYPE = "ap.settle_invoice"


async def start_settle_run(
    file: FileRecord, p: Principal, *, runs: RunStore, ledger: LedgerWriter
) -> UUID:
    """Create run row, ledger open, invoke run_graph with thread_id."""
    if file.entity != p.entity:
        raise DomainError("file belongs to another entity")
    thread_id = f"{file.entity}:{file.id}"
    run_id, created = await runs.start(file.entity, thread_id, GOAL_TYPE)
    if not created:
        return run_id
    token = current_principal.set(p)
    try:
        await _open_run(run_id, file, p, thread_id, ledger)
    finally:
        current_principal.reset(token)
    return run_id


async def _open_run(
    run_id: UUID, file: FileRecord, p: Principal, thread_id: str, ledger: LedgerWriter
) -> None:
    with run_span(run_id):
        await ledger.append(
            run_id,
            "received",
            {
                "file_id": str(file.id),
                "sha256": file.sha256,
                "channel": file.channel,
                "thread_id": thread_id,
                "goal_type": GOAL_TYPE,
                "principal": p.subject,
            },
        )
        # TODO(T-208): await run_graph.ainvoke(state, config={"configurable": {"thread_id": ...}})
