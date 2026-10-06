"""Typed configuration (M-58 Settings), loaded once from ITP_ environment variables."""

from decimal import Decimal
from functools import lru_cache
from typing import Final, Self

from pydantic import Field, HttpUrl, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLM_PROVIDERS: Final = ("anthropic", "openai", "deepseek")


def _provider_and_model(value: str) -> tuple[str, str]:
    """Split a 'provider:model' id; the model part may not be empty or contain ':'."""
    provider, _, model = value.partition(":")
    if provider not in LLM_PROVIDERS or not model or ":" in model:
        raise ValueError(f"model id must be provider:model with provider in {LLM_PROVIDERS}")
    return provider, model


class Settings(BaseSettings):
    """Typed configuration from env and vault."""

    model_config = SettingsConfigDict(env_prefix="ITP_", extra="forbid")

    database_url: PostgresDsn
    redis_url: RedisDsn
    object_bucket: str
    vault_url: HttpUrl
    erp_mcp_url: HttpUrl
    mail_mcp_url: HttpUrl
    llm_extract_model: str = Field(description="Pinned provider:model id")
    llm_reason_model: str = Field(description="Pinned provider:model id")
    jev_model: str = Field(description="Pinned version")
    embedding_model: str = Field(description="Pinned; stored with every vector")
    post_alone_max_aed: Decimal = Field(default=Decimal("25000"), gt=0)
    two_approver_min_aed: Decimal = Field(default=Decimal("250000"), gt=0)
    daily_autonomous_cap_aed: Decimal = Field(default=Decimal("500000"), gt=0)
    doc_type_threshold: float = 0.9
    line_map_threshold: float = 0.9
    near_duplicate_threshold: float = 0.7
    approval_ttl_hours: int = 24
    otel_endpoint: HttpUrl | None = None
    auth_issuer: str = Field(description="Expected iss claim of bearer tokens")
    auth_audience: str = Field(description="Expected aud claim of bearer tokens")
    auth_public_key: str = Field(description="PEM public key that verifies RS256 tokens")
    agent_subject: str = Field(
        default="agent:invoice-to-pay", description="Principal subject the agent runs as"
    )

    @field_validator("jev_model")
    @classmethod
    def _jev_model_pinned(cls, value: str) -> str:
        """Refuse the floating 'jev-latest' alias; decisions must be reproducible."""
        if value == "jev-latest":
            raise ValueError("jev_model must be a pinned version, not 'jev-latest'")
        return value

    @field_validator("llm_extract_model", "llm_reason_model")
    @classmethod
    def _llm_role_pinned(cls, value: str) -> str:
        """Roles are provider:model ids, never a floating 'latest' alias."""
        _, model = _provider_and_model(value)
        if model == "latest" or model.endswith("-latest"):
            raise ValueError("model id must be pinned, not a 'latest' alias")
        return value

    @field_validator("embedding_model")
    @classmethod
    def _embedding_from_openai(cls, value: str) -> str:
        """Embeddings come from OpenAI (DR-018)."""
        provider, _ = _provider_and_model(value)
        if provider != "openai":
            raise ValueError("embedding_model must be an openai:model id")
        return value

    @field_validator("auth_public_key")
    @classmethod
    def _unescape_pem(cls, value: str) -> str:
        """Accept a PEM written on one line with literal \\n, as .env files need."""
        return value.replace("\\n", "\n")

    @model_validator(mode="after")
    def _approval_thresholds_ordered(self) -> Self:
        """Two-approver threshold must sit above the post-alone limit."""
        if self.two_approver_min_aed <= self.post_alone_max_aed:
            raise ValueError("two_approver_min_aed must be greater than post_alone_max_aed")
        return self


@lru_cache
def get_settings() -> Settings:
    """Single cached settings instance for Depends."""
    return Settings()
