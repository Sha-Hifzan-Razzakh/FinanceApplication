"""Where a classified document goes before any model extraction."""

from typing import Literal

from invoice_to_pay.contracts.decisions import DocumentClassification

Route = Literal["extract", "reject", "hold"]


def route_classification(c: DocumentClassification, *, min_confidence: float) -> Route:
    """Hold what is unclear or illegible, reject what is not an invoice, extract the rest."""
    if not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be between 0 and 1")
    if c.doc_type_p < min_confidence or c.readable_p < min_confidence:
        return "hold"
    return "extract" if c.doc_type == "invoice" else "reject"
