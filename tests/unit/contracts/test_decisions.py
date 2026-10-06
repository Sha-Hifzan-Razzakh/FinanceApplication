"""M-09 DocumentClassification."""

import pytest
from pydantic import ValidationError

from invoice_to_pay.contracts.decisions import DocumentClassification


def test_classification_valid() -> None:
    c = DocumentClassification(doc_type="invoice", doc_type_p=0.97, readable_p=0.99)
    assert c.doc_type == "invoice"


@pytest.mark.parametrize("doc_type", ["invoice", "credit_note", "statement", "reminder", "other"])
def test_classification_accepts_every_listed_type(doc_type: str) -> None:
    DocumentClassification(doc_type=doc_type, doc_type_p=0.5, readable_p=0.5)  # type: ignore[arg-type]


def test_classification_rejects_an_unknown_type() -> None:
    with pytest.raises(ValidationError):
        DocumentClassification(doc_type="receipt", doc_type_p=0.9, readable_p=0.9)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["doc_type_p", "readable_p"])
@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_classification_probabilities_stay_in_zero_one(field: str, value: float) -> None:
    fields = {"doc_type": "invoice", "doc_type_p": 0.9, "readable_p": 0.9, field: value}
    with pytest.raises(ValidationError):
        DocumentClassification.model_validate(fields)


@pytest.mark.parametrize("value", [0.0, 1.0])
def test_classification_probability_bounds_are_inclusive(value: float) -> None:
    DocumentClassification(doc_type="other", doc_type_p=value, readable_p=value)
