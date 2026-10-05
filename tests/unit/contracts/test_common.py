"""CS-009 Quote / Fact[T] / Principal and CS-010 EntityId."""

import typing
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from invoice_to_pay.contracts.common import EntityId, Fact, Principal, Quote

NOW = datetime(2026, 10, 5, 9, 30, tzinfo=UTC)


# Quote


def test_cs009_quote_valid() -> None:
    q = Quote(page=1, text="Total AED 50,400.00", bbox=(10.0, 20.0, 110.0, 32.5))
    assert q.page == 1
    assert q.bbox == (10.0, 20.0, 110.0, 32.5)


def test_cs009_quote_bbox_is_optional() -> None:
    assert Quote(page=2, text="PO-5521").bbox is None


@pytest.mark.parametrize("page", [0, -1])
def test_cs009_quote_rejects_page_below_one(page: int) -> None:
    with pytest.raises(ValidationError):
        Quote(page=page, text="x")


def test_cs009_quote_rejects_text_over_300_chars() -> None:
    Quote(page=1, text="a" * 300)
    with pytest.raises(ValidationError):
        Quote(page=1, text="a" * 301)


def test_cs009_quote_rejects_bbox_of_wrong_length() -> None:
    with pytest.raises(ValidationError):
        Quote(page=1, text="x", bbox=(1.0, 2.0, 3.0))  # type: ignore[arg-type]


def test_cs009_quote_is_frozen() -> None:
    q = Quote(page=1, text="x")
    with pytest.raises(ValidationError):
        q.page = 2  # type: ignore[misc]


# Fact[T]


def test_cs009_fact_extracted_with_quote() -> None:
    fact = Fact[Decimal](
        value=Decimal("50400.00"),
        source="extracted",
        observed_at=NOW,
        quote=Quote(page=1, text="Total 50,400.00"),
    )
    assert fact.value == Decimal("50400.00")
    assert fact.observation_id is None


def test_cs009_fact_observed_with_observation_id() -> None:
    oid = uuid4()
    fact = Fact[str](value="PO-5521", source="observed", observation_id=oid, observed_at=NOW)
    assert fact.observation_id == oid


@pytest.mark.parametrize("source", ["inferred", "assumed"])
def test_cs009_fact_other_sources_need_no_observation(source: str) -> None:
    Fact[str](value="x", source=source, observed_at=NOW)  # type: ignore[arg-type]


def test_cs009_fact_rejects_unknown_source() -> None:
    with pytest.raises(ValidationError):
        Fact[str](value="x", source="guessed", observed_at=NOW)  # type: ignore[arg-type]


def test_cs009_fact_observed_requires_observation_id() -> None:
    with pytest.raises(ValidationError, match="observation_id"):
        Fact[str](value="PO-5521", source="observed", observed_at=NOW)


def test_cs009_fact_rejects_naive_observed_at() -> None:
    with pytest.raises(ValidationError):
        Fact[str](value="x", source="assumed", observed_at=datetime(2026, 10, 5, 9, 30))


def test_cs009_fact_validates_its_value_type() -> None:
    with pytest.raises(ValidationError):
        Fact[Decimal](value="not money", source="extracted", observed_at=NOW)  # type: ignore[arg-type]


def test_cs009_fact_is_frozen() -> None:
    fact = Fact[str](value="x", source="assumed", observed_at=NOW)
    with pytest.raises(ValidationError):
        fact.source = "observed"  # type: ignore[misc]


def test_cs009_fact_round_trips_through_json() -> None:
    fact = Fact[Decimal](
        value=Decimal("48300.00"),
        source="observed",
        observation_id=uuid4(),
        observed_at=NOW,
    )
    again = Fact[Decimal].model_validate_json(fact.model_dump_json())
    assert again == fact
    assert isinstance(again.value, Decimal)


# EntityId


def test_cs010_entity_id_lists_the_legal_entities() -> None:
    assert typing.get_args(EntityId) == ("meridian-supply", "meridian-projects")


def test_cs010_principal_entity_uses_entity_id() -> None:
    assert Principal.model_fields["entity"].annotation == EntityId
