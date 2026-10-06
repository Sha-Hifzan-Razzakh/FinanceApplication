"""CS-030 InvoiceLine / InvoiceDraft / Invoice and CS-031 draft_to_invoice. TS-01 lives here."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from invoice_to_pay.contracts.common import Quote, uuid7
from invoice_to_pay.contracts.intake import FileRecord
from invoice_to_pay.contracts.invoice import Invoice, InvoiceDraft, InvoiceLine, draft_to_invoice

Q = Quote(page=1, text="printed text")
D = Decimal


def _line(**overrides: Any) -> InvoiceLine:
    fields: dict[str, Any] = {
        "description": "HEB 200 beam 6m",
        "quantity": D("120"),
        "unit_price": D("400.00"),
        "amount": D("48000.00"),
        "source": Q,
    }
    fields.update(overrides)
    return InvoiceLine.model_validate(fields)


def _invoice_fields(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "entity": "meridian-supply",
        "file_id": uuid4(),
        "supplier_id": "V-GS-001",
        "number": "INV-88213",
        "issued_on": date(2026, 10, 5),
        "currency": "AED",
        "lines": [_line()],
        "subtotal": D("48000.00"),
        "vat": D("2400.00"),
        "total": D("50400.00"),
    }
    fields.update(overrides)
    return fields


def _invoice(**overrides: Any) -> Invoice:
    return Invoice.model_validate(_invoice_fields(**overrides))


# InvoiceLine


def test_cs030_line_defaults() -> None:
    line = _line()
    assert line.sku is None
    assert line.vat_rate == D("0.05")


@pytest.mark.parametrize(
    "overrides",
    [
        {"quantity": D("0")},
        {"quantity": D("-1")},
        {"unit_price": D("-0.01")},
        {"unit_price": D("400.00001"), "amount": D("48000.00")},
        {"amount": D("-1")},
        {"vat_rate": D("-0.01")},
        {"vat_rate": D("1.01")},
        {"description": "x" * 301},
        {"extra_field": 1},
    ],
)
def test_cs030_line_rejects_bad_values(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        _line(**overrides)


def test_cs030_line_accepts_boundaries() -> None:
    _line(description="x" * 300)
    _line(vat_rate=D("0"))
    _line(vat_rate=D("1"))
    _line(unit_price=D("0"), amount=D("0"))
    _line(unit_price=D("0.1234"), quantity=D("1"), amount=D("0.12"))


def test_cs030_line_amount_must_equal_quantity_times_unit_price() -> None:
    with pytest.raises(ValidationError, match="unit_price"):
        _line(amount=D("47900.00"))


def test_cs030_line_amount_within_one_cent_is_accepted() -> None:
    _line(quantity=D("3"), unit_price=D("33.3333"), amount=D("100.00"))
    _line(amount=D("48000.01"))
    with pytest.raises(ValidationError):
        _line(amount=D("48000.02"))


# Invoice


def test_cs030_invoice_valid() -> None:
    invoice = _invoice()
    assert invoice.total == D("50400.00")
    assert invoice.due_on is None


def test_ts01_invoice_totals_must_add_up() -> None:
    """TS-01: lines summing to 47,900 with subtotal 48,000 raises ValueError."""
    short = _line(amount=D("47900.00"), unit_price=D("399.1667"))
    with pytest.raises(ValueError, match="subtotal"):
        _invoice(lines=[short], subtotal=D("48000.00"))


def test_cs030_subtotal_plus_vat_must_equal_total() -> None:
    with pytest.raises(ValidationError, match="total"):
        _invoice(total=D("50000.00"))


def test_cs030_multiple_lines_are_summed() -> None:
    lines = [
        _line(),
        _line(description="Plate", quantity=D("2"), unit_price=D("50.00"), amount=D("100.00")),
    ]
    invoice = _invoice(lines=lines, subtotal=D("48100.00"), vat=D("2405.00"), total=D("50505.00"))
    assert len(invoice.lines) == 2


def test_cs030_due_date_cannot_precede_issue_date() -> None:
    with pytest.raises(ValidationError, match="due_on"):
        _invoice(due_on=date(2026, 10, 4))
    assert _invoice(due_on=date(2026, 10, 5)).due_on == date(2026, 10, 5)


@pytest.mark.parametrize(
    "overrides",
    [
        {"lines": []},
        {"number": ""},
        {"currency": "GBP"},
        {"entity": "other-co"},
        {"subtotal": D("-1")},
        {"vat": D("-1")},
        {
            "total": D("0"),
            "subtotal": D("0"),
            "vat": D("0"),
            "lines": [_line(quantity=D("1"), unit_price=D("0"), amount=D("0"))],
        },
        {"surprise": True},
    ],
)
def test_cs030_invoice_rejects_bad_values(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        _invoice(**overrides)


def test_cs030_invoice_is_frozen() -> None:
    invoice = _invoice()
    with pytest.raises(ValidationError):
        invoice.number = "other"  # type: ignore[misc]


def test_cs030_money_is_decimal_and_floats_convert_without_binary_noise() -> None:
    assert isinstance(_invoice().total, Decimal)
    # A float from JSON becomes the Decimal of its printed form, not of its binary value.
    assert _invoice(total=50400.0).total == D("50400.0")


# InvoiceDraft


def _draft_fields(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "supplier_name": "Gulf Steel Trading LLC",
        "supplier_trn": "100000000000003",
        "number": "INV-88213",
        "issued_on": date(2026, 10, 5),
        "currency": "AED",
        "po_number": "PO-5521",
        "lines": [_line()],
        "subtotal": D("48000.00"),
        "vat": D("2400.00"),
        "total": D("50400.00"),
        "printed_iban": "AE000000000000000000001",
    }
    fields.update(overrides)
    quoted = {k: Q for k, v in fields.items() if v is not None and k != "lines"}
    fields.setdefault("field_quotes", quoted)
    return fields


def test_cs030_empty_draft_is_valid() -> None:
    draft = InvoiceDraft()
    assert draft.lines == []
    assert draft.field_quotes == {}


def test_cs030_draft_every_filled_field_needs_a_quote() -> None:
    InvoiceDraft.model_validate(_draft_fields())
    fields = _draft_fields()
    del fields["field_quotes"]["total"]
    with pytest.raises(ValidationError, match="total"):
        InvoiceDraft.model_validate(fields)


def test_cs030_draft_null_fields_need_no_quote() -> None:
    InvoiceDraft.model_validate({"number": "INV-1", "field_quotes": {"number": Q}})


def test_cs030_draft_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        InvoiceDraft.model_validate({"surprise": 1})


# CS-031 draft_to_invoice


def _file(entity: str = "meridian-supply") -> FileRecord:
    sha = "a" * 64
    return FileRecord.model_validate(
        {
            "id": uuid7(),
            "entity": entity,
            "sha256": sha,
            "channel": "scan",
            "object_key": f"{entity}/{sha}",
            "mime_type": "application/pdf",
            "size_bytes": 70,
            "received_at": datetime.now(UTC),
        }
    )


def test_cs031_promotes_a_complete_quoted_draft() -> None:
    file = _file()
    invoice = draft_to_invoice(InvoiceDraft.model_validate(_draft_fields()), file, "V-GS-001")
    assert invoice.entity == "meridian-supply"
    assert invoice.file_id == file.id
    assert invoice.supplier_id == "V-GS-001"
    assert invoice.number == "INV-88213"
    assert invoice.po_number == "PO-5521"
    assert invoice.printed_iban == "AE000000000000000000001"
    assert invoice.total == D("50400.00")


def test_cs031_entity_comes_from_the_file() -> None:
    projects = _file("meridian-projects")
    invoice = draft_to_invoice(InvoiceDraft.model_validate(_draft_fields()), projects, "V-1")
    assert invoice.entity == "meridian-projects"


@pytest.mark.parametrize("missing", ["number", "issued_on", "currency", "subtotal", "vat", "total"])
def test_cs031_refuses_a_draft_missing_a_required_field(missing: str) -> None:
    fields = _draft_fields(**{missing: None})
    fields["field_quotes"] = {k: Q for k, v in fields.items() if v is not None and k != "lines"}
    with pytest.raises(ValueError, match=missing):
        draft_to_invoice(InvoiceDraft.model_validate(fields), _file(), "V-1")


def test_cs031_refuses_a_draft_without_lines() -> None:
    fields = _draft_fields(lines=[])
    with pytest.raises(ValueError, match="lines"):
        draft_to_invoice(InvoiceDraft.model_validate(fields), _file(), "V-1")


def test_cs031_refuses_a_draft_with_a_total_but_no_quote() -> None:
    """The draft model refuses it up front, so a draft with an unquoted total never exists."""
    fields = _draft_fields()
    del fields["field_quotes"]["total"]
    with pytest.raises(ValidationError):
        draft_to_invoice(InvoiceDraft.model_validate(fields), _file(), "V-1")


def test_cs031_refuses_a_draft_whose_quotes_were_bypassed() -> None:
    """model_copy skips validation, so promotion re-checks that required fields are quoted."""
    draft = InvoiceDraft.model_validate(_draft_fields())
    bypassed = draft.model_copy(update={"field_quotes": {"number": Q}})
    with pytest.raises(ValueError, match="without a quote"):
        draft_to_invoice(bypassed, _file(), "V-1")


def test_cs031_arithmetic_failures_surface_as_value_errors() -> None:
    draft = InvoiceDraft.model_validate(_draft_fields(total=D("50000.00")))
    with pytest.raises(ValueError, match="total"):
        draft_to_invoice(draft, _file(), "V-1")


def test_cs031_does_not_use_the_printed_iban_for_anything_else() -> None:
    draft = InvoiceDraft.model_validate(_draft_fields(printed_iban="AE999999999999999999999"))
    invoice = draft_to_invoice(draft, _file(), "V-1")
    assert invoice.supplier_id == "V-1"
    assert invoice.printed_iban == "AE999999999999999999999"
