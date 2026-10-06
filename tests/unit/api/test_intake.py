"""CS-019 POST /invoices/upload and GET /invoices/{file_id}."""

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from invoice_to_pay.api.deps import get_file_service
from invoice_to_pay.contracts.intake import MAX_UPLOAD_BYTES, UploadResponse
from invoice_to_pay.files.service import FileService
from invoice_to_pay.main import create_app
from tests.conftest import TokenFactory
from tests.fakes.documents import PDF, PNG, TEXT
from tests.fakes.files import InMemoryFileRecordStore, InMemoryStorage, RecordingPublisher


class _Harness:
    def __init__(self) -> None:
        self.storage = InMemoryStorage()
        self.records = InMemoryFileRecordStore()
        self.events = RecordingPublisher()
        self.service = FileService(storage=self.storage, records=self.records, events=self.events)


@pytest.fixture
def harness() -> _Harness:
    return _Harness()


@pytest.fixture
def client(settings_env: dict[str, str], harness: _Harness) -> Iterator[TestClient]:
    app: FastAPI = create_app()
    app.dependency_overrides[get_file_service] = lambda: harness.service
    with TestClient(app) as c:
        yield c


def _auth(make_token: TokenFactory, **claims: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(**claims)}"}


def _upload(
    client: TestClient, headers: dict[str, str], data: bytes, name: str = "inv.pdf"
) -> object:
    return client.post(
        "/invoices/upload",
        files={"file": (name, data, "application/pdf")},
        headers=headers,
    )


# POST /invoices/upload


def test_cs019_pdf_upload_is_accepted_with_202(
    client: TestClient, harness: _Harness, make_token: TokenFactory
) -> None:
    response = _upload(client, _auth(make_token), PDF)
    assert response.status_code == 202  # type: ignore[attr-defined]
    body = UploadResponse.model_validate(response.json())  # type: ignore[attr-defined]
    assert body.duplicate is False
    assert body.run_id is None
    (record,) = harness.records.records.values()
    assert body.file_id == record.id
    assert record.channel == "scan"
    assert len(harness.events.events) == 1


def test_cs019_image_upload_is_accepted(client: TestClient, make_token: TokenFactory) -> None:
    response = client.post(
        "/invoices/upload",
        files={"file": ("scan.png", PNG, "image/png")},
        headers=_auth(make_token),
    )
    assert response.status_code == 202


def test_cs019_same_file_twice_reports_duplicate(
    client: TestClient, make_token: TokenFactory
) -> None:
    first = _upload(client, _auth(make_token), PDF).json()  # type: ignore[attr-defined]
    second = _upload(client, _auth(make_token), PDF).json()  # type: ignore[attr-defined]
    assert second == {"file_id": first["file_id"], "run_id": None, "duplicate": True}


def test_cs019_oversized_upload_is_413(
    client: TestClient, harness: _Harness, make_token: TokenFactory
) -> None:
    too_big = PDF + b"0" * (MAX_UPLOAD_BYTES + 1 - len(PDF))
    response = _upload(client, _auth(make_token), too_big)
    assert response.status_code == 413  # type: ignore[attr-defined]
    assert harness.storage.objects == {}


def test_cs019_upload_at_the_limit_is_accepted(
    client: TestClient, make_token: TokenFactory
) -> None:
    exactly = PDF + b"0" * (MAX_UPLOAD_BYTES - len(PDF))
    assert _upload(client, _auth(make_token), exactly).status_code == 202  # type: ignore[attr-defined]


@pytest.mark.parametrize("data", [TEXT, b"", b"PK\x03\x04 zip pretending"])
def test_cs019_non_pdf_or_image_is_415(
    client: TestClient, harness: _Harness, make_token: TokenFactory, data: bytes
) -> None:
    # The declared content type says PDF; the bytes decide.
    response = _upload(client, _auth(make_token), data)
    assert response.status_code == 415  # type: ignore[attr-defined]
    assert harness.storage.objects == {}
    assert harness.events.events == []


def test_cs019_upload_without_token_is_401(client: TestClient, harness: _Harness) -> None:
    assert _upload(client, {}, PDF).status_code == 401  # type: ignore[attr-defined]
    assert harness.records.records == {}


def test_cs019_entity_comes_from_the_token_not_the_form(
    client: TestClient, harness: _Harness, make_token: TokenFactory
) -> None:
    response = client.post(
        "/invoices/upload",
        files={"file": ("inv.pdf", PDF, "application/pdf")},
        data={"entity": "meridian-supply", "channel": "email"},
        headers=_auth(make_token, entity="meridian-projects"),
    )
    assert response.status_code == 202
    (record,) = harness.records.records.values()
    assert record.entity == "meridian-projects"
    assert record.object_key.startswith("meridian-projects/")
    assert record.channel == "scan"


# GET /invoices/{file_id}


def test_get_file_record_for_own_entity(client: TestClient, make_token: TokenFactory) -> None:
    file_id = _upload(client, _auth(make_token), PDF).json()["file_id"]  # type: ignore[attr-defined]
    response = client.get(f"/invoices/{file_id}", headers=_auth(make_token))
    assert response.status_code == 200
    assert response.json()["id"] == file_id
    assert response.json()["entity"] == "meridian-supply"


def test_get_file_record_of_another_entity_is_404(
    client: TestClient, make_token: TokenFactory
) -> None:
    file_id = _upload(client, _auth(make_token), PDF).json()["file_id"]  # type: ignore[attr-defined]
    other = _auth(make_token, entity="meridian-projects")
    assert client.get(f"/invoices/{file_id}", headers=other).status_code == 404


def test_get_unknown_file_is_404(client: TestClient, make_token: TokenFactory) -> None:
    assert client.get(f"/invoices/{uuid4()}", headers=_auth(make_token)).status_code == 404


def test_get_file_record_needs_a_token(client: TestClient) -> None:
    assert client.get(f"/invoices/{uuid4()}").status_code == 401
