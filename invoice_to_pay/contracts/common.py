"""Contracts shared across the program."""

from datetime import datetime
from typing import Generic, Literal, Self, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

T = TypeVar("T")

EntityId = Literal["meridian-supply", "meridian-projects"]
"""One definition of the legal entities."""


class Quote(BaseModel):
    """Where a value was read from in a document."""

    model_config = ConfigDict(frozen=True)

    page: int = Field(ge=1, description="Page number in the source file")
    text: str = Field(max_length=300, description="Verbatim text the value came from")
    bbox: tuple[float, float, float, float] | None = Field(
        default=None, description="Box on the page, when the parser gives one"
    )


class Fact(BaseModel, Generic[T]):  # noqa: UP046 — signature fixed by CS-009
    """A belief with its provenance; every run-state fact is one."""

    model_config = ConfigDict(frozen=True)

    value: T = Field(description="The value itself")
    source: Literal["observed", "extracted", "inferred", "assumed"] = Field(
        description=("observed = system of record; extracted = document; inferred = model/memory")
    )
    observation_id: UUID | None = Field(
        default=None, description="Observation row backing the fact; required if observed"
    )
    observed_at: datetime = Field(description="When it was read; tz-aware")
    quote: Quote | None = Field(default=None, description="Document quote for extracted facts")

    @field_validator("observed_at")
    @classmethod
    def _tz_aware(cls, value: datetime) -> datetime:
        """Refuse naive datetimes (C-04)."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        return value

    @model_validator(mode="after")
    def _observed_needs_observation(self) -> Self:
        """An observed fact must point at the Observation row that backs it."""
        if self.source == "observed" and self.observation_id is None:
            raise ValueError("observation_id is required when source='observed'")
        return self


class Principal(BaseModel):
    """Who is acting: user or agent, entity, roles, scopes."""

    model_config = ConfigDict(frozen=True)

    subject: str
    kind: Literal["user", "agent"]
    entity: EntityId
    roles: list[str] = []
    scopes: list[str] = []
