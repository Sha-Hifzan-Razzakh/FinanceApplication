"""FastAPI entry point: app factory and lifespan."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from invoice_to_pay.api.errors import domain_error_handler
from invoice_to_pay.config.settings import get_settings
from invoice_to_pay.control.errors import DomainError
from invoice_to_pay.observability.tracing import setup_logging, setup_tracing

health_router = APIRouter()


@health_router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    # TODO: return 503 when the database or Redis is unreachable; no task in the workbook owns
    # readiness checks yet.
    return {"status": "ok"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open DB pool, Redis, MCP sessions, checkpointer; close on shutdown."""
    settings = get_settings()
    app.state.settings = settings
    engine = create_async_engine(str(settings.database_url), pool_pre_ping=True)
    app.state.db_sessions = async_sessionmaker(engine, expire_on_commit=False)
    # TODO(T-108): open the Redis pool.
    # TODO(T-202): open the ERP MCP client session.
    # TODO(T-213): set up the LangGraph AsyncPostgresSaver checkpointer.
    try:
        yield
    finally:
        await engine.dispose()
        del app.state.db_sessions
        del app.state.settings


def create_app() -> FastAPI:
    """App factory: routers, middleware, exception handlers."""
    settings = get_settings()  # fail at startup when a required setting is missing
    setup_logging()
    provider = setup_tracing(settings)
    app = FastAPI(title="Invoice-to-Pay", lifespan=lifespan)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]
    app.include_router(health_router)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    # TODO(T-107): include the intake router.
    return app


def __getattr__(name: str) -> FastAPI:
    """Build `app` on first access so `fastapi dev invoice_to_pay/main.py` finds it lazily."""
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Expose the lazy `app` to fastapi-cli discovery."""
    return [*globals(), "app"]
