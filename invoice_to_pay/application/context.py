"""Request- and run-scoped context."""

from contextvars import ContextVar

from invoice_to_pay.contracts.common import Principal

current_principal: ContextVar[Principal] = ContextVar("current_principal")
"""Carry the principal into graph nodes, adapters and tools."""

# TODO(T-108): the intake job sets current_principal for each run it starts.
