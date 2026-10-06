"""TS-34 extraction accuracy: every amount exact on the labelled invoices (CS-032).

Live eval: calls the real extract model (ITP_LLM_EXTRACT_MODEL) and, for descriptions, the
reason model as judge (ITP_LLM_REASON_MODEL). Run with `make eval`; provider keys come from the
provider's own environment variable. A missing key makes these tests error, never skip.
"""

import pytest
from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from evals.deepeval.dataset import LABELLED, LabelledInvoice
from evals.deepeval.harness import amount_mismatches, extract_case, judge_for
from invoice_to_pay.adapters.langchain_llm import LangChainLLM
from invoice_to_pay.config.settings import get_settings
from invoice_to_pay.prompts.registry import PromptRegistry

DESCRIPTION_THRESHOLD = 0.8


@pytest.fixture(scope="session")
def llm() -> LangChainLLM:
    return LangChainLLM(get_settings().llm_extract_model, prompts=PromptRegistry())


@pytest.fixture(scope="session")
def description_metric() -> GEval:
    return GEval(
        name="Line descriptions",
        criteria=(
            "The actual output lists the invoice line descriptions the expected output lists, "
            "in the same order. Differences in case, spacing or punctuation are fine. A missing, "
            "extra, merged or reworded item is not."
        ),
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        model=judge_for(get_settings().llm_reason_model),
        threshold=DESCRIPTION_THRESHOLD,
    )


@pytest.mark.parametrize("case", LABELLED, ids=lambda c: c.case_id)
async def test_extraction_amounts(
    case: LabelledInvoice, llm: LangChainLLM, description_metric: GEval
) -> None:
    result = await extract_case(case, llm)
    assert result.invoice is not None, f"{case.case_id} held: {result.held_reason}"
    assert amount_mismatches(case, result.invoice) == []  # exact, no tolerance
    assert_test(
        LLMTestCase(
            input=case.case_id,
            actual_output="\n".join(line.description for line in result.invoice.lines),
            expected_output="\n".join(line.description for line in case.lines),
        ),
        [description_metric],
    )
