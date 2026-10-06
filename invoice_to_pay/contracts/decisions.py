"""Decision schemas: typed questions answered by a DecisionPort (Jev) instead of free text."""

from typing import Literal

from pydantic import BaseModel, Field

# TODO(T-204): DuplicateScores · TODO(T-205): LineMapping · TODO(T-403): ScopeDecision ·
# TODO(T-504): QueryClassification — each is defined by the task that first uses it.


class DocumentClassification(BaseModel):
    """Document type and readability, typed."""

    doc_type: Literal["invoice", "credit_note", "statement", "reminder", "other"] = Field(
        description="Jev choice"
    )
    doc_type_p: float = Field(ge=0, le=1, description="Probability of the chosen type")
    readable_p: float = Field(ge=0, le=1, description="Probability the document is legible")
