"""Request- and run-scoped context."""

from contextvars import ContextVar

from invoice_to_pay.contracts.common import Principal

current_principal: ContextVar[Principal] = ContextVar("current_principal")
"""Carry the principal into graph nodes, adapters and tools."""
