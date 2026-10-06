"""CS-001 Settings and CS-002 get_settings."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from invoice_to_pay.config.settings import Settings, get_settings


def test_cs001_settings_loads_from_itp_env(settings_env: dict[str, str]) -> None:
    settings = Settings()  # type: ignore[call-arg]
    assert settings.object_bucket == "itp-test"
    assert str(settings.database_url).startswith("postgresql+asyncpg://")
    assert settings.otel_endpoint is None


def test_cs001_settings_defaults_match_contract(settings_env: dict[str, str]) -> None:
    settings = Settings()  # type: ignore[call-arg]
    assert settings.post_alone_max_aed == Decimal("25000")
    assert settings.two_approver_min_aed == Decimal("250000")
    assert settings.daily_autonomous_cap_aed == Decimal("500000")
    assert isinstance(settings.post_alone_max_aed, Decimal)
    assert settings.doc_type_threshold == 0.9
    assert settings.line_map_threshold == 0.9
    assert settings.near_duplicate_threshold == 0.7
    assert settings.approval_ttl_hours == 24


@pytest.mark.parametrize("missing", ["ITP_DATABASE_URL", "ITP_JEV_MODEL", "ITP_VAULT_URL"])
def test_cs001_missing_required_setting_fails(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.delenv(missing)
    with pytest.raises(ValidationError) as excinfo:
        Settings()  # type: ignore[call-arg]
    assert missing.removeprefix("ITP_").lower() in str(excinfo.value)


def test_cs001_jev_latest_is_refused(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ITP_JEV_MODEL", "jev-latest")
    with pytest.raises(ValidationError, match="jev-latest"):
        Settings()  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "key", ["ITP_POST_ALONE_MAX_AED", "ITP_TWO_APPROVER_MIN_AED", "ITP_DAILY_AUTONOMOUS_CAP_AED"]
)
@pytest.mark.parametrize("value", ["0", "-1"])
def test_cs001_money_thresholds_must_be_positive(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


@pytest.mark.parametrize("two_approver_min", ["25000", "10000"])
def test_cs001_two_approver_min_must_exceed_post_alone_max(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch, two_approver_min: str
) -> None:
    monkeypatch.setenv("ITP_TWO_APPROVER_MIN_AED", two_approver_min)
    with pytest.raises(ValidationError, match="two_approver_min_aed"):
        Settings()  # type: ignore[call-arg]


def test_cs001_settings_rejects_unknown_init_fields(settings_env: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        Settings(not_a_setting="x")  # type: ignore[call-arg]


def test_cs001_money_is_decimal_not_float(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ITP_POST_ALONE_MAX_AED", "25000.10")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.post_alone_max_aed == Decimal("25000.10")


def test_cs002_get_settings_is_cached(settings_env: dict[str, str]) -> None:
    first = get_settings()
    assert get_settings() is first


def test_cs002_get_settings_fails_when_required_missing(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ITP_REDIS_URL")
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        get_settings()


def test_cs001_auth_public_key_accepts_escaped_newlines(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    pem = settings_env["ITP_AUTH_PUBLIC_KEY"]
    monkeypatch.setenv("ITP_AUTH_PUBLIC_KEY", pem.replace("\n", "\\n"))
    assert Settings().auth_public_key == pem  # type: ignore[call-arg]


@pytest.mark.parametrize("missing", ["ITP_AUTH_ISSUER", "ITP_AUTH_AUDIENCE", "ITP_AUTH_PUBLIC_KEY"])
def test_cs001_auth_settings_are_required(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.delenv(missing)
    with pytest.raises(ValidationError):
        Settings()  # type: ignore[call-arg]


def test_cs001_agent_subject_default_and_override(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    assert Settings().agent_subject == "agent:invoice-to-pay"  # type: ignore[call-arg]
    monkeypatch.setenv("ITP_AGENT_SUBJECT", "agent:staging")
    assert Settings().agent_subject == "agent:staging"  # type: ignore[call-arg]


@pytest.mark.parametrize("key", ["ITP_LLM_EXTRACT_MODEL", "ITP_LLM_REASON_MODEL"])
@pytest.mark.parametrize(
    "value", ["anthropic:claude-sonnet-5-5", "openai:gpt-test", "deepseek:deepseek-test"]
)
def test_cs001_llm_roles_accept_provider_model_ids(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    monkeypatch.setenv(key, value)
    settings = Settings()  # type: ignore[call-arg]
    assert value in {settings.llm_extract_model, settings.llm_reason_model}


@pytest.mark.parametrize("key", ["ITP_LLM_EXTRACT_MODEL", "ITP_LLM_REASON_MODEL"])
@pytest.mark.parametrize(
    "value", ["claude-sonnet-5-5", "mistral:large", "anthropic:", ":model", "openai:gpt:4"]
)
def test_cs001_llm_roles_refuse_ids_without_a_known_provider(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ValidationError, match="provider:model"):
        Settings()  # type: ignore[call-arg]


@pytest.mark.parametrize("value", ["anthropic:claude-latest", "openai:gpt-latest"])
def test_cs001_llm_roles_refuse_floating_latest_aliases(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("ITP_LLM_EXTRACT_MODEL", value)
    with pytest.raises(ValidationError, match="latest"):
        Settings()  # type: ignore[call-arg]


def test_cs001_embedding_model_must_be_an_openai_id(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ITP_EMBEDDING_MODEL", "anthropic:something")
    with pytest.raises(ValidationError, match="openai"):
        Settings()  # type: ignore[call-arg]
