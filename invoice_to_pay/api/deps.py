"""FastAPI dependencies: caller identity and role checks."""

from collections.abc import Awaitable, Callable
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from invoice_to_pay.application.context import current_principal
from invoice_to_pay.config.settings import Settings, get_settings
from invoice_to_pay.contracts.common import Principal

# tokenUrl only feeds the OpenAPI docs; tokens are issued by the identity provider.
oauth2 = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

_ALGORITHMS = ["RS256"]
_REQUIRED_CLAIMS = ["exp", "iss", "aud", "sub"]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_principal(
    token: Annotated[str | None, Depends(oauth2)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    """Validate JWT, build Principal with entity, roles, scopes."""
    if token is None:
        raise _unauthorized()
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            settings.auth_public_key,
            algorithms=_ALGORITHMS,
            audience=settings.auth_audience,
            issuer=settings.auth_issuer,
            options={"require": _REQUIRED_CLAIMS},
        )
        scope = claims.get("scope", "")
        if not isinstance(scope, str):
            raise _unauthorized()
        principal = Principal(
            subject=claims["sub"],
            kind=claims.get("kind", "user"),
            entity=claims.get("entity"),  # type: ignore[arg-type]  # validated by Principal
            roles=claims.get("roles", []),
            scopes=scope.split(),
        )
    except (jwt.InvalidTokenError, ValidationError) as exc:
        raise _unauthorized() from exc
    current_principal.set(principal)
    return principal


def require_role(*roles: str) -> Callable[[Principal], Awaitable[Principal]]:
    """Dependency factory that refuses callers without a role."""
    if not roles:
        raise ValueError("require_role needs at least one role")
    allowed = frozenset(roles)

    async def _check(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
        if allowed.isdisjoint(principal.roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not allowed")
        return principal

    return _check
