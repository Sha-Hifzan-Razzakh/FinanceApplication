"""Shared fixtures: a complete ITP_ environment with fictitious, local-only values."""

from collections.abc import Iterator

import pytest

from invoice_to_pay.config.settings import get_settings

REQUIRED_ENV: dict[str, str] = {
    "ITP_DATABASE_URL": "postgresql+asyncpg://itp:itp@localhost:5432/itp",
    "ITP_REDIS_URL": "redis://localhost:6379/0",
    "ITP_OBJECT_BUCKET": "itp-test",
    "ITP_VAULT_URL": "http://localhost:8200",
    "ITP_ERP_MCP_URL": "http://localhost:8100/mcp",
    "ITP_MAIL_MCP_URL": "http://localhost:8101/mcp",
    "ITP_LLM_EXTRACT_MODEL": "test-extract-model",
    "ITP_LLM_REASON_MODEL": "test-reason-model",
    "ITP_JEV_MODEL": "jev-test-2026-01",
    "ITP_EMBEDDING_MODEL": "test-embedding-model",
}


@pytest.fixture
def settings_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, str]]:
    """Set every required ITP_ variable and reset the cached Settings around the test."""
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    yield dict(REQUIRED_ENV)
    get_settings.cache_clear()
