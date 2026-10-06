"""M-04 FileRecord, UploadMeta and M-54 InvoiceReceived."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from invoice_to_pay.contracts.common import uuid7
from invoice_to_pay.contracts.events import InvoiceReceived
from invoice_to_pay.contracts.intake import FileRecord, UploadMeta

SHA = "a" * 64
NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)


def _record(**overrides: object) -> FileRecord:
    fields: dict[str, object] = {
        "id": uuid4(),
        "entity": "meridian-supply",
        "sha256": SHA,
        "channel": "scan",
        "object_key": f"meridian-supply/{SHA}",
        "mime_type": "application/pdf",
        "size_bytes": 1024,
        "received_at": NOW,
    }
    fields.update(overrides)
    return FileRecord.model_validate(fields)


def test_file_record_defaults() -> None:
    r = _record()
    assert r.status == "stored"
    assert r.sender is None
    assert r.untrusted_text_id is None


@pytest.mark.parametrize("sha", ["A" * 64, "a" * 63, "g" * 64, ""])
def test_file_record_sha256_must_be_64_lowercase_hex(sha: str) -> None:
    with pytest.raises(ValidationError):
        _record(sha256=sha, object_key=f"meridian-supply/{sha}")


def test_file_record_object_key_must_start_with_its_entity() -> None:
    with pytest.raises(ValidationError, match="object_key"):
        _record(object_key=f"meridian-projects/{SHA}")
    with pytest.raises(ValidationError, match="object_key"):
        _record(object_key=f"invoices/meridian-supply/{SHA}")


@pytest.mark.parametrize("size", [0, 20_000_001])
def test_file_record_size_limits(size: int) -> None:
    with pytest.raises(ValidationError):
        _record(size_bytes=size)


def test_file_record_size_upper_bound_is_inclusive() -> None:
    assert _record(size_bytes=20_000_000).size_bytes == 20_000_000


def test_file_record_rejects_unsupported_mime_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        _record(mime_type="text/plain")
    with pytest.raises(ValidationError):
        _record(duplicate=True)


def test_upload_meta_defaults_and_cannot_carry_entity() -> None:
    meta = UploadMeta(channel="portal", sender="Gulf Steel portal")
    assert meta.untrusted_text_id is None
    with pytest.raises(ValidationError):
        UploadMeta.model_validate({"channel": "scan", "entity": "meridian-projects"})
    with pytest.raises(ValidationError):
        UploadMeta.model_validate({"channel": "fax"})


def test_invoice_received_is_frozen() -> None:
    evt = InvoiceReceived(
        event_id=uuid4(),
        entity="meridian-supply",
        file_id=uuid4(),
        sha256=SHA,
        channel="scan",
        occurred_at=NOW,
    )
    with pytest.raises(ValidationError):
        evt.channel = "email"  # type: ignore[misc]


def test_uuid7_is_version_7_and_time_ordered() -> None:
    ids = [uuid7() for _ in range(50)]
    assert all(u.version == 7 for u in ids)
    assert all(u.variant == "specified in RFC 4122" for u in ids)
    assert ids == sorted(ids)
    assert len(set(ids)) == 50


def test_upload_response_defaults() -> None:
    from invoice_to_pay.contracts.intake import UploadResponse

    r = UploadResponse(file_id=uuid4())
    assert r.run_id is None
    assert r.duplicate is False


def test_file_record_size_limit_is_the_upload_limit() -> None:
    from invoice_to_pay.contracts.intake import MAX_UPLOAD_BYTES

    assert MAX_UPLOAD_BYTES == 20_000_000
    _record(size_bytes=MAX_UPLOAD_BYTES)
