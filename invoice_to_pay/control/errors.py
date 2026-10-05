"""Typed domain errors every control raises (C-08)."""


class DomainError(Exception):
    """Base of every typed error; api/errors.py maps it to one envelope and status."""

    status_code: int = 400


# TODO(T-306): CS-081 hierarchy — ActionFailed, Inadmissible, Mismatch, InvalidTransition,
# ExtractionInvalid, ErpUnavailable, BudgetExhausted, Escalated, Untrusted.
