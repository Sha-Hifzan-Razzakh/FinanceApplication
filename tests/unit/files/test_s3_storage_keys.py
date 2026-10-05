"""CS-017 S3Storage refuses keys outside an entity prefix, before any network call."""

import aioboto3
import pytest

from invoice_to_pay.adapters.s3_storage import S3Storage


@pytest.fixture
def storage() -> S3Storage:
    return S3Storage(session=aioboto3.Session(), bucket="unused", endpoint_url=None)


@pytest.mark.parametrize(
    "key",
    ["invoices/meridian-supply/x", "other-co/x", "meridian-supply", "/meridian-supply/x", ""],
)
async def test_cs017_rejects_keys_without_entity_prefix(storage: S3Storage, key: str) -> None:
    with pytest.raises(ValueError, match="entity"):
        await storage.put(key, b"x", "application/pdf")
    with pytest.raises(ValueError, match="entity"):
        await storage.get(key)
    with pytest.raises(ValueError, match="entity"):
        await storage.delete(key)
    with pytest.raises(ValueError, match="entity"):
        await storage.presign(key, expires_in=60)
