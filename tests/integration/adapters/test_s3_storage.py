"""S3Storage against the local object store (MinIO from docker-compose)."""

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import aioboto3
import pytest

from invoice_to_pay.adapters.s3_storage import S3Storage
from tests.fakes.documents import PDF

ENDPOINT = os.environ.get("ITP_TEST_S3_ENDPOINT", "http://localhost:9000")
ACCESS_KEY = os.environ.get("ITP_TEST_S3_ACCESS_KEY", "itp-local")
SECRET_KEY = os.environ.get("ITP_TEST_S3_SECRET_KEY", "itp-local-only")


@pytest.fixture
async def storage() -> AsyncIterator[S3Storage]:
    """A fresh bucket per test."""
    session = aioboto3.Session(
        aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name="us-east-1"
    )
    bucket = f"itp-test-{uuid4().hex[:12]}"
    async with session.client("s3", endpoint_url=ENDPOINT) as s3:
        await s3.create_bucket(Bucket=bucket)
    yield S3Storage(bucket=bucket, session=session, endpoint_url=ENDPOINT)


async def test_cs017_put_get_round_trip(storage: S3Storage) -> None:
    key = f"meridian-supply/{'a' * 64}"
    await storage.put(key, PDF, "application/pdf")
    assert await storage.get(key) == PDF


async def test_cs017_delete_removes_the_object(storage: S3Storage) -> None:
    key = f"meridian-supply/{'b' * 64}"
    await storage.put(key, PDF, "application/pdf")
    await storage.delete(key)
    with pytest.raises(KeyError):
        await storage.get(key)


async def test_cs017_presign_returns_a_url_for_the_key(storage: S3Storage) -> None:
    key = f"meridian-projects/{'c' * 64}"
    url = await storage.presign(key, expires_in=300)
    assert url.startswith(ENDPOINT)
    assert key in url
    assert "X-Amz-Expires=300" in url
