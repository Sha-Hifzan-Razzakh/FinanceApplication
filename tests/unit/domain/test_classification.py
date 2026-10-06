"""route_classification: where a classified document goes before any model extraction."""

import pytest

from invoice_to_pay.contracts.decisions import DocumentClassification
from invoice_to_pay.domain.classification import route_classification

MIN = 0.9


def _c(
    doc_type: str = "invoice", doc_type_p: float = 0.99, readable_p: float = 0.99
) -> DocumentClassification:
    return DocumentClassification(
        doc_type=doc_type,  # type: ignore[arg-type]
        doc_type_p=doc_type_p,
        readable_p=readable_p,
    )


def test_a_confident_readable_invoice_goes_to_extraction() -> None:
    assert route_classification(_c(), min_confidence=MIN) == "extract"


@pytest.mark.parametrize("doc_type", ["statement", "reminder", "other", "credit_note"])
def test_done_when_non_invoices_never_reach_extraction(doc_type: str) -> None:
    """Done when: statements and reminders never reach extraction."""
    assert route_classification(_c(doc_type), min_confidence=MIN) == "reject"


@pytest.mark.parametrize("doc_type", ["invoice", "statement", "reminder", "other", "credit_note"])
def test_done_when_low_type_confidence_goes_to_a_person(doc_type: str) -> None:
    """Done when: low confidence goes to a person, whatever the type."""
    assert route_classification(_c(doc_type, doc_type_p=0.89), min_confidence=MIN) == "hold"


def test_an_illegible_document_goes_to_a_person() -> None:
    assert route_classification(_c(readable_p=0.5), min_confidence=MIN) == "hold"


def test_illegible_non_invoice_is_held_not_rejected() -> None:
    assert route_classification(_c("statement", readable_p=0.2), min_confidence=MIN) == "hold"


def test_confidence_exactly_at_the_threshold_passes() -> None:
    assert route_classification(_c(doc_type_p=0.9, readable_p=0.9), min_confidence=MIN) == "extract"


def test_threshold_is_a_parameter_not_a_constant() -> None:
    c = _c(doc_type_p=0.8, readable_p=0.8)
    assert route_classification(c, min_confidence=0.7) == "extract"
    assert route_classification(c, min_confidence=0.9) == "hold"


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_a_threshold_outside_zero_one_is_a_programming_error(bad: float) -> None:
    with pytest.raises(ValueError, match="min_confidence"):
        route_classification(_c(), min_confidence=bad)
