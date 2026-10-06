"""Object storage adapter (S3 API; MinIO locally)."""

from typing import Any, get_args

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from invoice_to_pay.application.ports import StoragePort
from invoice_to_pay.contracts.common import EntityId

_ENTITY_PREFIXES = tuple(f"{e}/" for e in get_args(EntityId))
_CONFIG = Config(signature_version="s3v4")  # SigV4 presigned URLs; MinIO and S3 refuse SigV2


def _checked(key: str) -> str:
    if not key.startswith(_ENTITY_PREFIXES) or key.endswith("/"):
        raise ValueError(f"object key must sit under an entity prefix: {key!r}")
    return key


class S3Storage(StoragePort):
    """Object storage implementation with entity-prefixed keys."""

    def __init__(
        self,
        *,
        bucket: str,
        session: aioboto3.Session | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        # Without an explicit session or endpoint, the AWS SDK reads AWS_* variables itself.
        self._session = session or aioboto3.Session()
        self._bucket = bucket
        self._endpoint_url = endpoint_url

    def _client(self) -> Any:
        return self._session.client("s3", endpoint_url=self._endpoint_url, config=_CONFIG)

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        """Store bytes under key (overwrites)."""
        _checked(key)
        async with self._client() as s3:
            await s3.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)

    async def get(self, key: str) -> bytes:
        """Return the bytes under key; KeyError when absent."""
        _checked(key)
        async with self._client() as s3:
            try:
                response = await s3.get_object(Bucket=self._bucket, Key=key)
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
                    raise KeyError(key) from exc
                raise
            async with response["Body"] as body:
                data: bytes = await body.read()
                return data

    async def delete(self, key: str) -> None:
        """Remove the object under key."""
        _checked(key)
        async with self._client() as s3:
            await s3.delete_object(Bucket=self._bucket, Key=key)

    async def presign(self, key: str, expires_in: int) -> str:
        """Time-limited download URL for key."""
        _checked(key)
        async with self._client() as s3:
            url: str = await s3.generate_presigned_url(
                "get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=expires_in
            )
            return url
