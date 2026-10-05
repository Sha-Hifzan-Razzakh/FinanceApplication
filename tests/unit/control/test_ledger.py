"""CS-011..013 hash chain, without a database. TS-03 lives here."""

import itertools
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from invoice_to_pay.contracts.run import LedgerEntry
from invoice_to_pay.control.ledger import entry_hash, next_entry, verify_entries

T0 = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)


def _chain(run_id: UUID, n: int = 5) -> list[LedgerEntry]:
    entries: list[LedgerEntry] = []
    prev: LedgerEntry | None = None
    for i in range(n):
        prev = next_entry(
            prev,
            run_id=run_id,
            kind="action" if i % 2 else "decision",
            body={"step": i, "amount": Decimal("48300.00")},
            trace_id=f"trace-{i}",
            at=T0 + timedelta(seconds=i),
        )
        entries.append(prev)
    return entries


def test_cs012_first_entry_starts_the_chain() -> None:
    first = _chain(uuid4(), 1)[0]
    assert first.seq == 1
    assert first.prev_hash is None
    assert len(first.hash) == 64


def test_cs012_entries_link_by_previous_hash() -> None:
    entries = _chain(uuid4())
    assert [e.seq for e in entries] == [1, 2, 3, 4, 5]
    for prev, entry in itertools.pairwise(entries):
        assert entry.prev_hash == prev.hash


def test_cs012_body_is_normalised_to_json_values() -> None:
    first = _chain(uuid4(), 1)[0]
    assert first.body == {"step": 0, "amount": "48300.00"}


def test_cs012_hash_is_deterministic_and_key_order_independent() -> None:
    run_id = uuid4()
    a = entry_hash(None, run_id, 1, "decision", {"a": 1, "b": 2}, "t", T0)
    b = entry_hash(None, run_id, 1, "decision", {"b": 2, "a": 1}, "t", T0)
    assert a == b


def test_cs012_naive_time_is_refused() -> None:
    with pytest.raises(ValueError):
        next_entry(None, run_id=uuid4(), kind="k", body={}, trace_id="", at=datetime(2026, 10, 5))


def test_cs013_intact_chain_verifies() -> None:
    assert verify_entries(_chain(uuid4())) is True


def test_cs013_empty_chain_verifies() -> None:
    assert verify_entries([]) is True


def test_ts03_ledger_detects_tampering() -> None:
    """TS-03: given 5 entries and an edited body, verify_chain returns False."""
    entries = _chain(uuid4())
    entries[2] = entries[2].model_copy(update={"body": {"step": 2, "amount": "1.00"}})
    assert verify_entries(entries) is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("kind", "approval"),
        ("trace_id", "forged"),
        ("at", T0 + timedelta(days=1)),
        ("run_id", UUID(int=7)),
        ("seq", 9),
        ("prev_hash", "f" * 64),
        ("hash", "e" * 64),
    ],
)
def test_cs013_editing_any_field_breaks_the_chain(field: str, value: object) -> None:
    entries = _chain(uuid4())
    entries[3] = entries[3].model_copy(update={field: value})
    assert verify_entries(entries) is False


def test_cs013_deleting_a_middle_entry_breaks_the_chain() -> None:
    entries = _chain(uuid4())
    del entries[1]
    assert verify_entries(entries) is False


def test_cs013_reordering_breaks_the_chain() -> None:
    entries = _chain(uuid4())
    entries[1], entries[2] = entries[2], entries[1]
    assert verify_entries(entries) is False


def test_cs013_rehashing_one_entry_still_breaks_the_next_link() -> None:
    entries = _chain(uuid4())
    e = entries[2]
    forged_body = {"step": 2, "amount": "1.00"}
    forged_hash = entry_hash(e.prev_hash, e.run_id, e.seq, e.kind, forged_body, e.trace_id, e.at)
    entries[2] = e.model_copy(update={"body": forged_body, "hash": forged_hash})
    assert verify_entries(entries) is False
