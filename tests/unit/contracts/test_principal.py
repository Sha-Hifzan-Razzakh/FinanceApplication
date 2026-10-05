"""M-01 Principal contract."""

import pytest
from pydantic import ValidationError

from invoice_to_pay.contracts.common import Principal


def test_principal_defaults_and_fields() -> None:
    p = Principal(subject="u-clerk-1", kind="user", entity="meridian-supply")
    assert p.roles == []
    assert p.scopes == []


def test_principal_rejects_unknown_entity() -> None:
    with pytest.raises(ValidationError):
        Principal(subject="u-1", kind="user", entity="other-co")  # type: ignore[arg-type]


def test_principal_rejects_unknown_kind() -> None:
    with pytest.raises(ValidationError):
        Principal(subject="u-1", kind="robot", entity="meridian-supply")  # type: ignore[arg-type]


def test_principal_is_frozen() -> None:
    p = Principal(subject="u-1", kind="user", entity="meridian-supply")
    with pytest.raises(ValidationError):
        p.entity = "meridian-projects"  # type: ignore[misc]
