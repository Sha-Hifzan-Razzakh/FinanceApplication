"""CS-032 support: the labelled invoices, the exact-amount scorer and the judge mapping.

The live eval (evals/deepeval/test_extraction.py) calls real models; these tests prove its
dataset is sound and its scorer fails on a wrong amount, without any model call.
"""

from decimal import Decimal

import pytest

from evals.deepeval.dataset import LABELLED, LabelledInvoice, render_pdf
from evals.deepeval.harness import amount_mismatches, extract_case, judge_for
from evals.deepeval.harness import pdf_record as _file
from invoice_to_pay.adapters.llamaindex_reader import read_pdf
from invoice_to_pay.contracts.common import Quote
from invoice_to_pay.contracts.invoice import InvoiceDraft, InvoiceLine, draft_to_invoice
from tests.fakes.files import InMemoryStorage
from tests.fakes.llm import ScriptedLLM

D = Decimal


def _draft_from_label(case: LabelledInvoice) -> InvoiceDraft:
    quote = Quote(page=1, text="x")
    fields = ("supplier_name", "number", "issued_on", "currency", "subtotal", "vat", "total")
    return InvoiceDraft.model_validate(
        {
            "supplier_name": case.supplier_name,
            "number": case.number,
            "issued_on": case.issued_on,
            "currency": case.currency,
            "lines": [
                InvoiceLine(
                    description=line.description,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    amount=line.amount,
                    vat_rate=case.vat_rate,
                    source=quote,
                )
                for line in case.lines
            ],
            "subtotal": case.subtotal,
            "vat": case.vat,
            "total": case.total,
            "field_quotes": {name: quote for name in fields},
        }
    )


def test_there_are_twenty_distinct_labelled_invoices() -> None:
    assert len(LABELLED) == 20
    assert len({c.case_id for c in LABELLED}) == 20
    assert len({c.number for c in LABELLED}) == 20


def test_the_set_covers_the_hard_shapes() -> None:
    assert {c.currency for c in LABELLED} == {"AED", "USD", "EUR"}
    assert any(len(c.lines) > 6 for c in LABELLED)  # long enough to run onto a second page
    assert any(c.vat_rate == D("0") for c in LABELLED)
    assert any(c.total >= D("10000") for c in LABELLED)  # printed with a thousands separator
    assert any(line.unit_price.as_tuple().exponent == -4 for c in LABELLED for line in c.lines)


@pytest.mark.parametrize("case", LABELLED, ids=lambda c: c.case_id)
def test_each_label_adds_up_and_promotes_to_an_invoice(case: LabelledInvoice) -> None:

    invoice = draft_to_invoice(_draft_from_label(case), _file(), "V-1")
    assert invoice.total == case.total
    assert amount_mismatches(case, invoice) == []


@pytest.mark.parametrize("case", LABELLED, ids=lambda c: c.case_id)
async def test_each_pdf_prints_every_labelled_amount(case: LabelledInvoice) -> None:

    storage = InMemoryStorage()
    file = _file()
    await storage.put(file.object_key, render_pdf(case), file.mime_type)
    text = "\n".join(doc.text for doc in await read_pdf(file, storage=storage))
    assert case.number in text
    for amount in (case.subtotal, case.vat, case.total):
        assert f"{amount:,.2f}" in text
    for line in case.lines:
        assert line.description in text
        assert f"{line.amount:,.2f}" in text


def test_a_long_invoice_is_split_over_two_pages() -> None:
    long_case = next(c for c in LABELLED if len(c.lines) > 6)
    assert render_pdf(long_case).count(b"/Type /Page ") == 2


@pytest.mark.parametrize("field", ["subtotal", "vat", "total"])
def test_the_scorer_fails_on_any_wrong_header_amount(field: str) -> None:

    case = LABELLED[0]
    invoice = draft_to_invoice(_draft_from_label(case), _file(), "V-1")
    wrong = invoice.model_copy(update={field: getattr(invoice, field) + D("0.01")})
    assert [m for m in amount_mismatches(case, wrong) if field in m]


def test_the_scorer_fails_on_a_wrong_line_amount_and_a_missing_line() -> None:

    case = next(c for c in LABELLED if len(c.lines) > 1)
    invoice = draft_to_invoice(_draft_from_label(case), _file(), "V-1")
    first = invoice.lines[0].model_copy(update={"amount": invoice.lines[0].amount + D("1")})
    assert amount_mismatches(
        case, invoice.model_copy(update={"lines": [first, *invoice.lines[1:]]})
    )
    assert amount_mismatches(case, invoice.model_copy(update={"lines": invoice.lines[:-1]}))


async def test_extract_case_runs_the_real_pipeline_on_the_rendered_pdf() -> None:
    case = LABELLED[0]
    llm = ScriptedLLM(_draft_from_label(case))
    result = await extract_case(case, llm)
    assert result.invoice is not None
    assert amount_mismatches(case, result.invoice) == []
    document = llm.calls[0][1]["document"]
    assert case.number in document and f"{case.total:,.2f}" in document


@pytest.mark.parametrize(
    ("model_id", "env", "class_name"),
    [
        ("anthropic:claude-opus-5-5", "ANTHROPIC_API_KEY", "AnthropicModel"),
        ("openai:gpt-test", "OPENAI_API_KEY", "OpenAIModel"),
        ("deepseek:deepseek-test", "DEEPSEEK_API_KEY", "DeepSeekModel"),
    ],
)
def test_judge_follows_the_provider_of_the_reason_model(
    monkeypatch: pytest.MonkeyPatch, model_id: str, env: str, class_name: str
) -> None:
    monkeypatch.setenv(env, "unit-test-placeholder")
    judge = judge_for(model_id)
    assert type(judge).__name__ == class_name
    assert model_id.split(":")[1] in judge.get_model_name()


def test_judge_refuses_an_unknown_provider() -> None:
    with pytest.raises(ValueError, match="provider"):
        judge_for("mistral:large")
