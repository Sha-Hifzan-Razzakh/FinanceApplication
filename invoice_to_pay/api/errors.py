"""Error envelope for HTTP responses."""

from fastapi import Request
from fastapi.responses import JSONResponse

from invoice_to_pay.control.errors import DomainError


async def domain_error_handler(req: Request, exc: DomainError) -> JSONResponse:
    """Map typed domain errors to one error envelope and status."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"type": type(exc).__name__, "message": str(exc)}},
    )
