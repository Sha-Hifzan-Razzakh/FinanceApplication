"""M-52 LedgerEntry contract."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from invoice_to_pay.contracts.run import LedgerEntry


def _entry(**overrides: object) -> LedgerEntry:
    fields: dict[str, object] = {
        "run_id": uuid4(),
        "seq": 1,
        "kind": "decision",
        "body": {"doc_type": "invoice"},
        "prev_hash": None,
        "hash": "0" * 64,
        "trace_id": "",
        "at": datetime(2026, 10, 5, tzinfo=UTC),
    }
    fields.update(overrides)
    return LedgerEntry.model_validate(fields)


def test_ledger_entry_valid() -> None:
    assert _entry().seq == 1


def test_ledger_entry_rejects_seq_below_one() -> None:
    with pytest.raises(ValidationError):
        _entry(seq=0)


def test_ledger_entry_is_frozen() -> None:
    entry = _entry()
    with pytest.raises(ValidationError):
        entry.kind = "action"  # type: ignore[misc]
