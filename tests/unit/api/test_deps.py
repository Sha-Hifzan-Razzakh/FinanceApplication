"""CS-006 get_principal and CS-007 require_role."""

from typing import Annotated

import pytest
from fastapi import APIRouter, Depends, HTTPException
from fastapi.testclient import TestClient

from invoice_to_pay.api.deps import get_principal, require_role
from invoice_to_pay.application.context import current_principal
from invoice_to_pay.contracts.common import Principal
from invoice_to_pay.main import create_app
from tests.conftest import OTHER_SIGNING_KEY, TokenFactory

# A stand-in for any entity-scoped store: the query is always filtered by the caller's entity.
_RECORDS = {"f-supply": "meridian-supply", "f-projects": "meridian-projects"}

CallerDep = Annotated[Principal, Depends(get_principal)]


def _client() -> TestClient:
    app = create_app()
    router = APIRouter()

    @router.get("/whoami")
    async def whoami(principal: CallerDep) -> dict[str, object]:
        return principal.model_dump()

    @router.get("/context-entity")
    async def context_entity(principal: CallerDep) -> dict[str, str]:
        return {"entity": current_principal.get().entity}

    @router.get("/records/{record_id}")
    async def read_record(record_id: str, principal: CallerDep) -> dict[str, str]:
        if _RECORDS.get(record_id) != principal.entity:
            raise HTTPException(status_code=404)
        return {"id": record_id}

    @router.get("/approvals-probe", dependencies=[Depends(require_role("ap_lead", "treasury"))])
    async def approvals_probe() -> dict[str, str]:
        return {"ok": "yes"}

    app.include_router(router)
    return TestClient(app)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_cs006_valid_token_builds_principal(
    settings_env: dict[str, str], make_token: TokenFactory
) -> None:
    token = make_token(roles=["ap_lead"], scope="erp.read erp.post")
    response = _client().get("/whoami", headers=_bearer(token))
    assert response.status_code == 200
    assert response.json() == {
        "subject": "u-clerk-1",
        "kind": "user",
        "entity": "meridian-supply",
        "roles": ["ap_lead"],
        "scopes": ["erp.read", "erp.post"],
    }


def test_cs006_agent_kind_is_read_from_token(
    settings_env: dict[str, str], make_token: TokenFactory
) -> None:
    token = make_token(sub="agent-itp", kind="agent", roles=None, scope=None)
    body = _client().get("/whoami", headers=_bearer(token)).json()
    assert body["kind"] == "agent"
    assert body["roles"] == []
    assert body["scopes"] == []


def test_cs006_no_token_is_401(settings_env: dict[str, str]) -> None:
    response = _client().get("/whoami")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"entity": None}, id="missing-entity"),
        pytest.param({"entity": "other-co"}, id="unknown-entity"),
        pytest.param({"sub": None}, id="missing-sub"),
        pytest.param({"kind": "robot"}, id="unknown-kind"),
        pytest.param({"exp": 1}, id="expired"),
        pytest.param({"exp": None}, id="missing-exp"),
        pytest.param({"aud": "someone-else"}, id="wrong-audience"),
        pytest.param({"iss": "https://evil.example"}, id="wrong-issuer"),
        pytest.param({"signing_key": OTHER_SIGNING_KEY}, id="wrong-signing-key"),
        pytest.param({"scope": ["erp.post"]}, id="scope-not-a-string"),
        pytest.param({"roles": "ap_lead"}, id="roles-not-a-list"),
    ],
)
def test_cs006_invalid_token_is_401(
    settings_env: dict[str, str], make_token: TokenFactory, overrides: dict[str, object]
) -> None:
    response = _client().get("/whoami", headers=_bearer(make_token(**overrides)))
    assert response.status_code == 401


def test_cs006_unsigned_token_is_401(settings_env: dict[str, str]) -> None:
    import jwt

    token = jwt.encode({"sub": "u-1", "entity": "meridian-supply"}, key=None, algorithm="none")
    assert _client().get("/whoami", headers=_bearer(token)).status_code == 401


def test_cs006_tampered_entity_is_401(
    settings_env: dict[str, str], make_token: TokenFactory
) -> None:
    import base64
    import json

    header, payload, signature = make_token().split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["entity"] = "meridian-projects"
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    response = _client().get("/whoami", headers=_bearer(f"{header}.{forged}.{signature}"))
    assert response.status_code == 401


def test_cs006_entity_comes_only_from_token(
    settings_env: dict[str, str], make_token: TokenFactory
) -> None:
    response = _client().get(
        "/whoami?entity=meridian-projects",
        headers={**_bearer(make_token()), "X-Entity": "meridian-projects"},
    )
    assert response.json()["entity"] == "meridian-supply"


def test_cs006_token_for_entity_a_cannot_read_entity_b(
    settings_env: dict[str, str], make_token: TokenFactory
) -> None:
    client = _client()
    supply = _bearer(make_token(entity="meridian-supply"))
    assert client.get("/records/f-supply", headers=supply).status_code == 200
    assert client.get("/records/f-projects", headers=supply).status_code == 404


def test_cs006_sets_current_principal_for_the_request(
    settings_env: dict[str, str], make_token: TokenFactory
) -> None:
    token = make_token(entity="meridian-projects")
    response = _client().get("/context-entity", headers=_bearer(token))
    assert response.json() == {"entity": "meridian-projects"}


def test_cs007_role_present_passes(settings_env: dict[str, str], make_token: TokenFactory) -> None:
    token = make_token(roles=["treasury"])
    assert _client().get("/approvals-probe", headers=_bearer(token)).status_code == 200


def test_cs007_role_missing_is_403(settings_env: dict[str, str], make_token: TokenFactory) -> None:
    token = make_token(roles=["ap_clerk"])
    assert _client().get("/approvals-probe", headers=_bearer(token)).status_code == 403


def test_cs007_require_role_needs_a_valid_token(settings_env: dict[str, str]) -> None:
    assert _client().get("/approvals-probe").status_code == 401


def test_cs007_require_role_without_roles_is_a_programming_error() -> None:
    with pytest.raises(ValueError):
        require_role()
