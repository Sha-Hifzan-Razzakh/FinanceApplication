"""CS-025 read_pdf: a stored PDF becomes LlamaIndex Documents in reading order."""

from datetime import UTC, datetime

import pytest
from llama_index.core import Document

from invoice_to_pay.adapters.llamaindex_reader import read_pdf
from invoice_to_pay.contracts.common import uuid7
from invoice_to_pay.contracts.intake import FileRecord
from tests.fakes.documents import PNG, TEXT
from tests.fakes.files import InMemoryStorage
from tests.fakes.pdfs import Line, make_pdf

COLS = (50, 250, 330, 430)


def _row(y: int, *cells: str) -> Line:
    return (y, list(zip(COLS, cells, strict=False)))


HEADER = ("Description", "Qty", "Unit price", "Amount")


def _file(mime: str = "application/pdf", entity: str = "meridian-supply") -> FileRecord:
    sha = "b" * 64
    return FileRecord.model_validate(
        {
            "id": uuid7(),
            "entity": entity,
            "sha256": sha,
            "channel": "email",
            "object_key": f"{entity}/{sha}",
            "mime_type": mime,
            "size_bytes": 1000,
            "received_at": datetime.now(UTC),
        }
    )


async def _read(pdf: bytes, **file_overrides: str) -> tuple[list[Document], FileRecord]:
    storage = InMemoryStorage()
    file = _file(**file_overrides)
    await storage.put(file.object_key, pdf, file.mime_type)
    return await read_pdf(file, storage=storage), file


TWO_PAGE_INVOICE = make_pdf(
    [
        [
            (740, [(50, "Gulf Steel Trading LLC"), (400, "Invoice INV-88213")]),
            _row(640, *HEADER),
            _row(620, "HEB 200 beam 6m", "120", "400.00", "48000.00"),
            _row(600, "Plate 10mm", "2", "50.00", "100.00"),
            (60, [(250, "Page 1 of 2")]),
        ],
        [
            (740, [(50, "Invoice INV-88213 (continued)")]),
            _row(700, *HEADER),
            _row(680, "Anchor bolt M20", "40", "5.00", "200.00"),
            (600, [(330, "Subtotal"), (430, "48300.00")]),
            (60, [(250, "Page 2 of 2")]),
        ],
    ]
)


async def test_done_when_a_two_page_line_item_table_is_one_table_with_page_numbers() -> None:
    """Done when: a two-page line-item table comes back as one table with page numbers."""
    docs, _ = await _read(TWO_PAGE_INVOICE)
    tables = [d for d in docs if d.metadata["kind"] == "table"]
    assert len(tables) == 1
    assert tables[0].metadata["pages"] == [1, 2]
    lines = tables[0].text.splitlines()
    assert lines[0] == "Description | Qty | Unit price | Amount"
    assert lines[1:] == [
        "HEB 200 beam 6m | 120 | 400.00 | 48000.00",
        "Plate 10mm | 2 | 50.00 | 100.00",
        "Anchor bolt M20 | 40 | 5.00 | 200.00",
    ]


async def test_cs025_returns_llamaindex_documents_in_reading_order_with_provenance() -> None:
    docs, file = await _read(TWO_PAGE_INVOICE)
    assert all(isinstance(d, Document) for d in docs)
    assert [d.metadata["kind"] for d in docs] == ["text", "table", "text", "text"]
    assert all(d.metadata["file_id"] == str(file.id) for d in docs)
    first = docs[0]
    assert first.metadata["pages"] == [1]
    assert "Gulf Steel Trading LLC" in first.text and "Invoice INV-88213" in first.text


async def test_cs025_page_furniture_and_text_after_the_table_are_handled() -> None:
    docs, _ = await _read(TWO_PAGE_INVOICE)
    joined = "\n".join(d.text for d in docs)
    assert "Page 1 of 2" not in joined and "Page 2 of 2" not in joined
    assert docs[-1].metadata == {**docs[-1].metadata, "pages": [2], "kind": "text"}
    assert "Subtotal" in docs[-1].text and "48300.00" in docs[-1].text


async def test_cs025_a_pdf_without_a_text_layer_gives_no_documents() -> None:
    docs, _ = await _read(make_pdf([[], []]))
    assert docs == []


async def test_cs025_bytes_that_are_not_a_pdf_are_refused() -> None:
    with pytest.raises(ValueError, match="PDF"):
        await _read(TEXT)


@pytest.mark.parametrize("mime", ["image/png", "image/jpeg", "image/tiff"])
async def test_cs025_images_are_not_read_here(mime: str) -> None:
    with pytest.raises(ValueError, match="PDF"):
        await _read(PNG, mime=mime)


async def test_cs025_reads_the_object_under_the_files_own_key() -> None:
    storage = InMemoryStorage()
    file = _file()
    other = _file(entity="meridian-projects")
    await storage.put(file.object_key, TWO_PAGE_INVOICE, "application/pdf")
    await storage.put(
        other.object_key, make_pdf([[(700, [(50, "Other entity")])]]), "application/pdf"
    )
    docs = await read_pdf(file, storage=storage)
    assert "Other entity" not in "".join(d.text for d in docs)
