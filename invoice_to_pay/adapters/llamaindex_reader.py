"""PDF reading: layout-aware text and whole tables as LlamaIndex Documents."""

import asyncio
import io

import pypdf
from llama_index.core import Document
from pypdf.errors import PyPdfError

from invoice_to_pay.application.ports import StoragePort
from invoice_to_pay.contracts.intake import FileRecord
from invoice_to_pay.domain.layout import TableBlock, blocks_from_pages


def _page_texts(data: bytes) -> list[str]:
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        return [page.extract_text(extraction_mode="layout") for page in reader.pages]
    except (PyPdfError, ValueError, OSError) as exc:
        raise ValueError("file is not a readable PDF") from exc


async def read_pdf(file: FileRecord, *, storage: StoragePort) -> list[Document]:
    """Layout-aware text with page numbers; tables kept whole."""
    if file.mime_type != "application/pdf":
        raise ValueError(f"read_pdf reads PDF files only, not {file.mime_type}")
    data = await storage.get(file.object_key)
    # Text extraction is CPU work: keep it off the event loop.
    pages = await asyncio.to_thread(_page_texts, data)
    # TODO(T-111): scans and PDFs without a text layer return no Documents; OD-06 holds them.
    return [
        Document(
            text=block.text,
            metadata={
                "file_id": str(file.id),
                "pages": list(block.pages),
                "kind": "table" if isinstance(block, TableBlock) else "text",
            },
        )
        for block in blocks_from_pages(pages)
    ]
