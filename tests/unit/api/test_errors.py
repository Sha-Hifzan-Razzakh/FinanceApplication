"""CS-005 domain_error_handler."""

from fastapi import APIRouter
from fastapi.testclient import TestClient

from invoice_to_pay.control.errors import DomainError
from invoice_to_pay.main import create_app


class _Conflict(DomainError):
    status_code = 409


def _client_raising(exc: Exception) -> TestClient:
    app = create_app()
    router = APIRouter()

    @router.get("/boom")
    async def boom() -> None:
        raise exc

    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_cs005_domain_error_maps_to_envelope(settings_env: dict[str, str]) -> None:
    response = _client_raising(DomainError("validation not passed")).get("/boom")
    assert response.status_code == 400
    assert response.json() == {"error": {"type": "DomainError", "message": "validation not passed"}}


def test_cs005_subclass_status_code_is_used(settings_env: dict[str, str]) -> None:
    response = _client_raising(_Conflict("same approver")).get("/boom")
    assert response.status_code == 409
    assert response.json()["error"]["type"] == "_Conflict"


def test_cs005_non_domain_error_is_not_leaked(settings_env: dict[str, str]) -> None:
    response = _client_raising(RuntimeError("secret detail")).get("/boom")
    assert response.status_code == 500
    assert "secret detail" not in response.text
