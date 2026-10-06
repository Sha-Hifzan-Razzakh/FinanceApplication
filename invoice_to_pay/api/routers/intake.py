"""Intake routes: upload a scan or PDF, read back its FileRecord."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from invoice_to_pay.api.deps import get_file_service, get_principal
from invoice_to_pay.contracts.common import Principal
from invoice_to_pay.contracts.intake import (
    MAX_UPLOAD_BYTES,
    FileRecord,
    UploadMeta,
    UploadResponse,
)
from invoice_to_pay.files.service import ALLOWED_MIME_TYPES, FileService, sniff_mime

router = APIRouter(prefix="/invoices", tags=["intake"])

CallerDep = Annotated[Principal, Depends(get_principal)]
FilesDep = Annotated[FileService, Depends(get_file_service)]


def _too_large() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        detail=f"File larger than {MAX_UPLOAD_BYTES} bytes",
    )


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload(file: UploadFile, p: CallerDep, files: FilesDep) -> UploadResponse:
    """Accept scan/PDF, enforce limits, call FileService.put, return 202."""
    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise _too_large()
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise _too_large()
    if sniff_mime(data) not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, PNG, JPEG or TIFF files are accepted",
        )
    record, duplicate = await files.put(data, UploadMeta(channel="scan"), p)
    # TODO(T-108): run_id stays None; the intake job starts the run from InvoiceReceived.
    return UploadResponse(file_id=record.id, duplicate=duplicate)


@router.get("/{file_id}")
async def get_file(file_id: UUID, p: CallerDep, files: FilesDep) -> FileRecord:
    """The caller's FileRecord; another entity's file is 404."""
    record = await files.get(file_id, p)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return record
