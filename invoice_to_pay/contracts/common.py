"""Contracts shared across the program."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

# TODO(T-103): Quote, Fact[T] and the shared entity type.


class Principal(BaseModel):
    """Who is acting: user or agent, entity, roles, scopes."""

    model_config = ConfigDict(frozen=True)

    subject: str
    kind: Literal["user", "agent"]
    entity: Literal["meridian-supply", "meridian-projects"]
    roles: list[str] = []
    scopes: list[str] = []
