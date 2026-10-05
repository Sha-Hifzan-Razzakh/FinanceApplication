"""CS-008 current_principal."""

import asyncio

import pytest

from invoice_to_pay.application.context import current_principal
from invoice_to_pay.contracts.common import Principal

SUPPLY = Principal(subject="u-1", kind="user", entity="meridian-supply")
PROJECTS = Principal(subject="u-2", kind="user", entity="meridian-projects")


def test_cs008_unset_principal_raises_lookup_error() -> None:
    with pytest.raises(LookupError):
        current_principal.get()


async def test_cs008_principal_is_isolated_per_task() -> None:
    async def run_as(principal: Principal) -> str:
        current_principal.set(principal)
        await asyncio.sleep(0)
        return current_principal.get().entity

    results = await asyncio.gather(run_as(SUPPLY), run_as(PROJECTS))
    assert results == ["meridian-supply", "meridian-projects"]
