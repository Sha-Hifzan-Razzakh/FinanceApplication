"""Read a stored invoice into a validated Invoice: one model reading, one retry, else held."""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from pydantic import ValidationError

from invoice_to_pay.application.ports import (
    DocumentLike,
    LLMPort,
    ReadDocuments,
    StructuredOutputError,
)
from invoice_to_pay.contracts.intake import FileRecord
from invoice_to_pay.contracts.invoice import Invoice, InvoiceDraft, draft_to_invoice

ResolveSupplier = Callable[[InvoiceDraft], Awaitable[str | None]]
"""Looks the supplier up in the vendor master; None when it is not there (never from the text)."""

EXTRACT = "extract_invoice"
RETRY = "extract_invoice_retry"


@dataclass(frozen=True)
class ExtractionResult:
    """An Invoice, or the reason the file was held for a person (draft kept for the reviewer)."""

    invoice: Invoice | None
    draft: InvoiceDraft | None
    held_reason: str | None
    attempts: int
    prompts: tuple[tuple[str, str], ...]  # (prompt id, version) per model call, for the ledger


def _render(documents: Sequence[DocumentLike]) -> str:
    blocks = []
    for doc in documents:
        pages = list(doc.metadata.get("pages", []))
        label = "page" if len(pages) == 1 else "pages"
        span = (
            str(pages[0]) if len(pages) == 1 else f"{pages[0]}-{pages[-1]}" if pages else "unknown"
        )
        blocks.append(f"[{doc.metadata.get('kind', 'text')}, {label} {span}]\n{doc.text}")
    return "\n\n".join(blocks)


def _describe(error: Exception) -> str:
    """Validation problems as plain lines: field and message, never the offending value."""
    if isinstance(error, ValidationError):
        return "\n".join(
            f"- {'.'.join(str(part) for part in e['loc']) or 'invoice'}: {e['msg']}"
            for e in error.errors(include_input=False)
        )
    return f"- {error}"


async def extract_invoice(
    file: FileRecord,
    *,
    read: ReadDocuments,
    llm: LLMPort,
    resolve_supplier: ResolveSupplier,
) -> ExtractionResult:
    """Read file, ask the model for an InvoiceDraft and promote it; one retry with the errors."""
    documents = await read(file)
    if not documents:
        # DEBT-011: a scan has no text layer; OD-06 decides how scans get read.
        return ExtractionResult(None, None, "no readable text in the file", 0, ())
    document = _render(documents)
    prompts: list[tuple[str, str]] = []
    draft: InvoiceDraft | None = None
    problems = ""
    for attempt in (1, 2):
        prompt_id = EXTRACT if attempt == 1 else RETRY
        variables = (
            {"document": document} if attempt == 1 else {"document": document, "errors": problems}
        )
        prompts.append((prompt_id, llm.prompt_version(prompt_id)))
        try:
            draft = await llm.structured(prompt_id, variables, InvoiceDraft)
            supplier_id = await resolve_supplier(draft)
            if supplier_id is None:
                return ExtractionResult(
                    None, draft, "supplier not found in the vendor master", attempt, tuple(prompts)
                )
            invoice = draft_to_invoice(draft, file, supplier_id)
        except (StructuredOutputError, ValueError) as error:
            problems = _describe(error)
            continue
        return ExtractionResult(invoice, draft, None, attempt, tuple(prompts))
    return ExtractionResult(
        None, draft, f"extraction invalid after one retry: {problems}", 2, tuple(prompts)
    )
