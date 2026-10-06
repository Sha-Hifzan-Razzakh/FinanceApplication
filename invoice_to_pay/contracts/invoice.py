"""Invoice contracts: the line, the loose draft the model fills, and the validated invoice."""

from datetime import date
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from invoice_to_pay.contracts.common import EntityId, Quote
from invoice_to_pay.contracts.intake import FileRecord

_CENT = Decimal("0.01")

# Draft fields that must be filled and quoted before a draft becomes an Invoice.
_REQUIRED_FOR_INVOICE = ("number", "issued_on", "currency", "subtotal", "vat", "total")
# Draft fields that carry no entry in field_quotes: lines quote themselves via InvoiceLine.source.
_UNQUOTED_FIELDS = frozenset({"lines", "field_quotes"})


class InvoiceLine(BaseModel):
    """One invoice line with its source quote."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(max_length=300, description="Line text as printed")
    sku: str | None = Field(default=None, description="Filled by line mapping")
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0, decimal_places=4)
    amount: Decimal = Field(ge=0, description="Line net amount")
    vat_rate: Decimal = Field(default=Decimal("0.05"), ge=0, le=1, description="UAE standard 5%")
    source: Quote = Field(description="Where this line was read")

    @model_validator(mode="after")
    def _amount_matches_quantity_times_price(self) -> Self:
        """amount == quantity * unit_price, within one cent."""
        if abs(self.amount - self.quantity * self.unit_price) > _CENT:
            raise ValueError("amount must equal quantity * unit_price (within 0.01)")
        return self


class InvoiceDraft(BaseModel):
    """What the model fills; loose, quoted, not yet trusted."""

    model_config = ConfigDict(extra="forbid")

    supplier_name: str | None = None
    supplier_trn: str | None = Field(default=None, description="Tax registration number")
    number: str | None = None
    issued_on: date | None = None
    due_on: date | None = None
    currency: str | None = None
    po_number: str | None = None
    lines: list[InvoiceLine] = []
    subtotal: Decimal | None = None
    vat: Decimal | None = None
    total: Decimal | None = None
    printed_iban: str | None = Field(default=None, description="Never used to pay")
    field_quotes: dict[str, Quote] = Field(default={}, description="Quote per filled field")

    @model_validator(mode="after")
    def _every_filled_field_is_quoted(self) -> Self:
        """Every non-null field has an entry in field_quotes."""
        unquoted = [
            name
            for name in type(self).model_fields
            if name not in _UNQUOTED_FIELDS
            and getattr(self, name) is not None
            and name not in self.field_quotes
        ]
        if unquoted:
            raise ValueError(f"fields without a quote: {', '.join(unquoted)}")
        return self


class Invoice(BaseModel):
    """The validated invoice the run works on."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity: EntityId
    file_id: UUID
    supplier_id: str = Field(description="Resolved against vendor master")
    number: str = Field(min_length=1)
    issued_on: date
    due_on: date | None = Field(default=None, description="On or after issued_on")
    currency: Literal["AED", "USD", "EUR"]
    po_number: str | None = None
    lines: list[InvoiceLine] = Field(min_length=1)
    subtotal: Decimal = Field(ge=0)
    vat: Decimal = Field(ge=0)
    total: Decimal = Field(gt=0)
    printed_iban: str | None = Field(default=None, description="Compared with master only")

    @model_validator(mode="after")
    def _adds_up(self) -> Self:
        """Σlines = subtotal; subtotal + vat = total; due_on ≥ issued_on."""
        lines_total = sum((line.amount for line in self.lines), Decimal(0))
        if lines_total != self.subtotal:
            raise ValueError(f"lines sum to {lines_total} but subtotal is {self.subtotal}")
        if self.subtotal + self.vat != self.total:
            raise ValueError(
                f"subtotal {self.subtotal} + vat {self.vat} does not equal total {self.total}"
            )
        if self.due_on is not None and self.due_on < self.issued_on:
            raise ValueError("due_on must be on or after issued_on")
        return self


def draft_to_invoice(d: InvoiceDraft, file: FileRecord, vendor_id: str) -> Invoice:
    """Promote a draft once every required field is present and quoted."""
    missing = [name for name in _REQUIRED_FOR_INVOICE if getattr(d, name) is None]
    if not d.lines:
        missing.append("lines")
    unquoted = [
        name
        for name in _REQUIRED_FOR_INVOICE
        if getattr(d, name) is not None and name not in d.field_quotes
    ]
    if missing or unquoted:
        problems = []
        if missing:
            problems.append(f"missing: {', '.join(missing)}")
        if unquoted:
            problems.append(f"without a quote: {', '.join(unquoted)}")
        raise ValueError("draft cannot become an invoice (" + "; ".join(problems) + ")")
    return Invoice.model_validate(
        {
            "entity": file.entity,
            "file_id": file.id,
            "supplier_id": vendor_id,
            "number": d.number,
            "issued_on": d.issued_on,
            "due_on": d.due_on,
            "currency": d.currency,
            "po_number": d.po_number,
            "lines": d.lines,
            "subtotal": d.subtotal,
            "vat": d.vat,
            "total": d.total,
            "printed_iban": d.printed_iban,
        }
    )
