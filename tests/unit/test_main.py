"""CS-003 create_app and CS-004 lifespan."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from invoice_to_pay.config.settings import Settings
from invoice_to_pay.control.errors import DomainError
from invoice_to_pay.main import create_app


def test_cs003_create_app_returns_fastapi(settings_env: dict[str, str]) -> None:
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.exception_handlers.get(DomainError) is not None


def test_cs003_create_app_fails_fast_without_required_settings(
    settings_env: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ITP_DATABASE_URL")
    from invoice_to_pay.config.settings import get_settings

    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        create_app()


def test_cs003_health_route(settings_env: dict[str, str]) -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cs004_lifespan_puts_settings_on_app_state(settings_env: dict[str, str]) -> None:
    app = create_app()
    with TestClient(app):
        assert isinstance(app.state.settings, Settings)


def test_cs004_lifespan_opens_a_session_factory(settings_env: dict[str, str]) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    app = create_app()
    with TestClient(app):
        assert isinstance(app.state.db_sessions, async_sessionmaker)


def test_cs004_lifespan_releases_state_on_shutdown(settings_env: dict[str, str]) -> None:
    app = create_app()
    with TestClient(app):
        pass
    assert not hasattr(app.state, "settings")
    assert not hasattr(app.state, "db_sessions")


def test_cs003_module_exposes_lazy_app_for_fastapi_cli(settings_env: dict[str, str]) -> None:
    import invoice_to_pay.main as main

    assert "app" in dir(main)
    assert isinstance(main.app, FastAPI)


def test_cs004_lifespan_builds_the_file_service(settings_env: dict[str, str]) -> None:
    from invoice_to_pay.files.service import FileService

    app = create_app()
    with TestClient(app):
        assert isinstance(app.state.file_service, FileService)
    assert not hasattr(app.state, "file_service")
