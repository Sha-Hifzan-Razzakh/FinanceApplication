"""Shared fixtures: a complete ITP_ environment with fictitious, local-only values."""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from invoice_to_pay.config.settings import get_settings

if TYPE_CHECKING:
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

IDP_ISSUER = "https://idp.test.example"
IDP_AUDIENCE = "invoice-to-pay"

TokenFactory = Callable[..., str]


def _rsa_key_pair() -> tuple[str, str]:
    """Throwaway RSA key pair (private PEM, public PEM) for signing test tokens."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private_pem, public_pem


SIGNING_KEY, PUBLIC_KEY = _rsa_key_pair()
OTHER_SIGNING_KEY, _ = _rsa_key_pair()

REQUIRED_ENV: dict[str, str] = {
    "ITP_DATABASE_URL": "postgresql+asyncpg://itp:itp@localhost:5432/itp",
    "ITP_REDIS_URL": "redis://localhost:6379/0",
    "ITP_OBJECT_BUCKET": "itp-test",
    "ITP_VAULT_URL": "http://localhost:8200",
    "ITP_ERP_MCP_URL": "http://localhost:8100/mcp",
    "ITP_MAIL_MCP_URL": "http://localhost:8101/mcp",
    "ITP_LLM_EXTRACT_MODEL": "anthropic:test-extract-model",
    "ITP_LLM_REASON_MODEL": "openai:test-reason-model",
    "ITP_JEV_MODEL": "jev-test-2026-01",
    "ITP_EMBEDDING_MODEL": "openai:test-embedding-model",
    "ITP_AUTH_ISSUER": IDP_ISSUER,
    "ITP_AUTH_AUDIENCE": IDP_AUDIENCE,
    "ITP_AUTH_PUBLIC_KEY": PUBLIC_KEY,
}


@pytest.fixture
def settings_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, str]]:
    """Set every required ITP_ variable and reset the cached Settings around the test."""
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    yield dict(REQUIRED_ENV)
    get_settings.cache_clear()


@pytest.fixture
def make_token() -> TokenFactory:
    """Mint an RS256 test token; keyword overrides replace or (with None) drop claims."""

    def _make(*, signing_key: str = SIGNING_KEY, **overrides: Any) -> str:
        now = datetime.now(UTC)
        claims: dict[str, Any] = {
            "iss": IDP_ISSUER,
            "aud": IDP_AUDIENCE,
            "sub": "u-clerk-1",
            "entity": "meridian-supply",
            "roles": ["ap_clerk"],
            "scope": "erp.read",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        claims.update(overrides)
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, signing_key, algorithm="RS256")

    return _make


@pytest.fixture(scope="session")
def span_exporter() -> "InMemorySpanExporter":
    """Install tracing once for the session and record every finished span in memory."""
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from invoice_to_pay.config.settings import Settings
    from invoice_to_pay.observability.tracing import setup_tracing

    settings = Settings(**{k.removeprefix("ITP_").lower(): v for k, v in REQUIRED_ENV.items()})
    exporter = InMemorySpanExporter()
    setup_tracing(settings).add_span_processor(SimpleSpanProcessor(exporter))
    return exporter


@pytest.fixture
def spans(span_exporter: "InMemorySpanExporter") -> "InMemorySpanExporter":
    """The session span recorder, emptied before the test."""
    span_exporter.clear()
    return span_exporter
