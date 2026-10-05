"""CS-014 setup_tracing and CS-015 run_span."""

import json
from collections.abc import Iterator
from typing import Annotated
from uuid import uuid4

import pytest
import structlog
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from opentelemetry import context, propagate, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import HttpUrl

from invoice_to_pay.api.deps import get_principal
from invoice_to_pay.application.context import current_principal
from invoice_to_pay.config.settings import Settings
from invoice_to_pay.contracts.common import Principal
from invoice_to_pay.main import create_app
from invoice_to_pay.observability.tracing import (
    SERVICE_NAME,
    current_trace_id,
    exporter_for,
    run_span,
    setup_logging,
    setup_tracing,
)
from tests.conftest import TokenFactory

SUPPLY = Principal(subject="agent-itp", kind="agent", entity="meridian-supply")


@pytest.fixture
def as_supply() -> Iterator[Principal]:
    token = current_principal.set(SUPPLY)
    yield SUPPLY
    current_principal.reset(token)


def _settings(settings_env: dict[str, str]) -> Settings:
    return Settings()  # type: ignore[call-arg]


# CS-014 setup_tracing


def test_cs014_setup_tracing_installs_one_global_provider(
    settings_env: dict[str, str], span_exporter: InMemorySpanExporter
) -> None:
    provider = setup_tracing(_settings(settings_env))
    assert isinstance(provider, TracerProvider)
    assert setup_tracing(_settings(settings_env)) is provider
    assert trace.get_tracer_provider() is provider


def test_cs014_resource_names_the_service(
    settings_env: dict[str, str], span_exporter: InMemorySpanExporter
) -> None:
    provider = setup_tracing(_settings(settings_env))
    assert provider.resource.attributes["service.name"] == SERVICE_NAME


def test_cs014_no_endpoint_means_no_exporter(settings_env: dict[str, str]) -> None:
    assert exporter_for(_settings(settings_env)) is None


def test_cs014_endpoint_configures_otlp_exporter(settings_env: dict[str, str]) -> None:
    settings = _settings(settings_env).model_copy(
        update={"otel_endpoint": HttpUrl("http://localhost:4317")}
    )
    assert isinstance(exporter_for(settings), OTLPSpanExporter)


def test_cs014_create_app_instruments_fastapi(
    settings_env: dict[str, str], spans: InMemorySpanExporter
) -> None:
    with TestClient(create_app()) as client:
        client.get("/health")
    names = [s.name for s in spans.get_finished_spans()]
    assert "GET /health" in names


# CS-015 run_span


def test_cs015_run_span_is_a_root_with_run_and_entity(
    spans: InMemorySpanExporter, as_supply: Principal
) -> None:
    run_id = uuid4()
    with run_span(run_id) as span:
        assert span.is_recording()
    (finished,) = spans.get_finished_spans()
    assert finished.name == "run"
    assert finished.parent is None
    assert finished.attributes is not None
    assert finished.attributes["run.id"] == str(run_id)
    assert finished.attributes["entity"] == "meridian-supply"


def test_cs015_run_span_needs_a_principal(spans: InMemorySpanExporter) -> None:
    with pytest.raises(LookupError), run_span(uuid4()):
        pass


def test_cs015_spans_inside_a_run_share_its_trace(
    spans: InMemorySpanExporter, as_supply: Principal
) -> None:
    tracer = trace.get_tracer("test")
    with (
        run_span(uuid4()),
        tracer.start_as_current_span("read"),
        tracer.start_as_current_span("validate"),
    ):
        pass
    finished = spans.get_finished_spans()
    assert len(finished) == 3
    assert len({s.context.trace_id for s in finished}) == 1


def test_cs015_current_trace_id(spans: InMemorySpanExporter, as_supply: Principal) -> None:
    assert current_trace_id() == ""
    with run_span(uuid4()) as span:
        tid = current_trace_id()
        assert tid == format(span.get_span_context().trace_id, "032x")
    assert current_trace_id() == ""


def test_cs015_run_span_binds_log_context(
    spans: InMemorySpanExporter, as_supply: Principal
) -> None:
    run_id = uuid4()
    with run_span(run_id):
        bound = structlog.contextvars.get_contextvars()
        assert bound == {"run_id": str(run_id), "entity": "meridian-supply"}
    assert structlog.contextvars.get_contextvars() == {}


def test_log_lines_carry_trace_run_and_entity(
    spans: InMemorySpanExporter, as_supply: Principal, capsys: pytest.CaptureFixture[str]
) -> None:
    setup_logging()
    run_id = uuid4()
    with run_span(run_id):
        expected_trace = current_trace_id()
        structlog.get_logger().info("posted", posting_id="P-1")
    line = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert line["event"] == "posted"
    assert line["trace_id"] == expected_trace
    assert line["run_id"] == str(run_id)
    assert line["entity"] == "meridian-supply"
    assert len(line["span_id"]) == 16


def test_log_lines_outside_a_span_have_no_trace(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging()
    structlog.get_logger().info("startup")
    line = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert "trace_id" not in line


def test_done_when_upload_to_finish_shares_one_trace(
    settings_env: dict[str, str], make_token: TokenFactory, spans: InMemorySpanExporter
) -> None:
    """A run started from an upload request keeps the request's trace through to finish."""
    carriers: list[dict[str, str]] = []
    app = create_app()
    router = APIRouter()

    @router.post("/upload-probe")
    async def upload_probe(principal: Annotated[Principal, Depends(get_principal)]) -> None:
        carrier: dict[str, str] = {}
        propagate.inject(carrier)  # what the intake event carries to the worker (T-108)
        carriers.append(carrier)

    app.include_router(router)
    with TestClient(app) as client:
        response = client.post("/upload-probe", headers={"Authorization": f"Bearer {make_token()}"})
    assert response.status_code == 200

    # Worker side: restore the request's context, then run.
    attached = context.attach(propagate.extract(carriers[0]))
    principal_token = current_principal.set(SUPPLY)
    try:
        tracer = trace.get_tracer("test")
        with run_span(uuid4()), tracer.start_as_current_span("goal_check"):
            pass
    finally:
        current_principal.reset(principal_token)
        context.detach(attached)

    finished = spans.get_finished_spans()
    assert {"POST /upload-probe", "run", "goal_check"} <= {s.name for s in finished}
    assert len({s.context.trace_id for s in finished}) == 1
