"""Shared pieces of the extraction eval: run one case, score amounts exactly, pick the judge."""

from datetime import UTC, datetime
from typing import Any

from deepeval.models import AnthropicModel, DeepEvalBaseLLM, DeepSeekModel, OpenAIModel

from evals.deepeval.dataset import LabelledInvoice, render_pdf
from invoice_to_pay.adapters.llamaindex_reader import read_pdf
from invoice_to_pay.application.ports import LLMPort
from invoice_to_pay.application.use_cases.extract_invoice import ExtractionResult, extract_invoice
from invoice_to_pay.contracts.common import uuid7
from invoice_to_pay.contracts.intake import FileRecord
from invoice_to_pay.contracts.invoice import Invoice, InvoiceDraft
from tests.fakes.files import InMemoryStorage

_JUDGES: dict[str, Any] = {
    "anthropic": AnthropicModel,
    "openai": OpenAIModel,
    "deepseek": DeepSeekModel,
}


def judge_for(model_id: str) -> DeepEvalBaseLLM:
    """The DeepEval judge for a provider:model id (the reason role judges descriptions)."""
    provider, _, model = model_id.partition(":")
    if provider not in _JUDGES or not model:
        raise ValueError(f"judge needs a provider:model id with provider in {sorted(_JUDGES)}")
    judge: DeepEvalBaseLLM = _JUDGES[provider](model=model)
    return judge


def pdf_record(case_id: str = "case", entity: str = "meridian-supply") -> FileRecord:
    """A FileRecord for a PDF held in memory; the hash is a stand-in, nothing verifies it."""
    sha = "e" * 64
    return FileRecord.model_validate(
        {
            "id": uuid7(),
            "entity": entity,
            "sha256": sha,
            "channel": "email",
            "object_key": f"{entity}/{sha}",
            "mime_type": "application/pdf",
            "size_bytes": 1000,
            "received_at": datetime.now(UTC),
        }
    )


async def extract_case(case: LabelledInvoice, llm: LLMPort) -> ExtractionResult:
    """Render the case's PDF, read it and run the production extraction on it."""
    storage = InMemoryStorage()
    file = pdf_record(case.case_id)
    await storage.put(file.object_key, render_pdf(case), file.mime_type)

    async def read(f: FileRecord) -> Any:
        return await read_pdf(f, storage=storage)

    async def vendor(draft: InvoiceDraft) -> str | None:
        return f"V-{case.case_id}"  # the vendor master is not under test here

    return await extract_invoice(file, read=read, llm=llm, resolve_supplier=vendor)


def amount_mismatches(case: LabelledInvoice, invoice: Invoice) -> list[str]:
    """Every amount field that differs from the label, exactly (no tolerance); empty = pass."""
    problems = [
        f"{name}: expected {want}, got {got}"
        for name, want, got in (
            ("subtotal", case.subtotal, invoice.subtotal),
            ("vat", case.vat, invoice.vat),
            ("total", case.total, invoice.total),
        )
        if want != got
    ]
    if invoice.currency != case.currency:
        problems.append(f"currency: expected {case.currency}, got {invoice.currency}")
    if len(invoice.lines) != len(case.lines):
        problems.append(f"lines: expected {len(case.lines)}, got {len(invoice.lines)}")
        return problems
    for n, (want_line, got_line) in enumerate(zip(case.lines, invoice.lines, strict=True), 1):
        for name in ("quantity", "unit_price", "amount"):
            want, got = getattr(want_line, name), getattr(got_line, name)
            if want != got:
                problems.append(f"line {n} {name}: expected {want}, got {got}")
    return problems
