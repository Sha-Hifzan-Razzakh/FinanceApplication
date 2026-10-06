"""Text blocks and whole tables from the layout-mode text of PDF pages (pure, no PDF library)."""

import re
from collections.abc import Sequence
from dataclasses import dataclass

_GAP = re.compile(r"\s{3,}")
_PAGE_FURNITURE = re.compile(r"^\s*page\s+\d+(\s+of\s+\d+)?\s*$", re.IGNORECASE)
_MIN_CELLS = 3
_MIN_TABLE_ROWS = 2
_MAX_BLANK_LINES_IN_TABLE = 2


@dataclass(frozen=True)
class TextBlock:
    """Consecutive non-table lines of one page."""

    pages: tuple[int, ...]
    lines: tuple[str, ...]

    @property
    def text(self) -> str:
        """The block as plain text, one line per line."""
        return "\n".join(self.lines)


@dataclass(frozen=True)
class TableBlock:
    """A table, whole even when it runs across pages: its rows and the pages it covers."""

    pages: tuple[int, ...]
    rows: tuple[tuple[str, ...], ...]

    @property
    def columns(self) -> int:
        """Number of cells in the header row."""
        return len(self.rows[0])

    @property
    def text(self) -> str:
        """The table as pipe-separated rows, one per line."""
        return "\n".join(" | ".join(row) for row in self.rows)


Block = TextBlock | TableBlock


def _cells(line: str) -> tuple[str, ...]:
    return tuple(_GAP.split(line.strip()))


def _is_row(line: str) -> bool:
    return len(_cells(line)) >= _MIN_CELLS


def _tidy(line: str) -> str:
    return _GAP.sub("   ", line.strip())


def _parse_page(text: str, page: int) -> list[Block]:
    """Split one page into text blocks and tables (rows of 3+ cells, up to 2 blank lines apart)."""
    lines = [ln for ln in text.splitlines() if not _PAGE_FURNITURE.match(ln)]
    blocks: list[Block] = []
    texts: list[str] = []
    rows: list[tuple[str, ...]] = []
    blanks = 0

    def flush_text() -> None:
        if texts:
            blocks.append(TextBlock(pages=(page,), lines=tuple(texts)))
            texts.clear()

    def flush_rows() -> None:
        if len(rows) >= _MIN_TABLE_ROWS:
            flush_text()
            blocks.append(TableBlock(pages=(page,), rows=tuple(rows)))
        else:  # a lone wide line is just text
            texts.extend(" ".join(r) for r in rows)
        rows.clear()

    for line in lines:
        if not line.strip():
            blanks += 1
            continue
        if _is_row(line):
            if rows and blanks > _MAX_BLANK_LINES_IN_TABLE:
                flush_rows()
            rows.append(_cells(line))
        else:
            flush_rows()
            texts.append(_tidy(line))
        blanks = 0
    flush_rows()
    flush_text()
    return blocks


def _same_header(a: tuple[str, ...], b: tuple[str, ...]) -> bool:
    return [c.casefold() for c in a] == [c.casefold() for c in b]


def _continuation(previous: Block | None, page_blocks: list[Block], page: int) -> TableBlock | None:
    """The table on this page that continues `previous` from the page before, if any."""
    if not isinstance(previous, TableBlock) or previous.pages[-1] != page - 1:
        return None
    for i, block in enumerate(page_blocks):
        if not isinstance(block, TableBlock):
            continue
        if block.columns != previous.columns:
            return None
        # Only a repeated header proves a continuation when text comes first (a caption).
        if i == 0 or _same_header(block.rows[0], previous.rows[0]):
            return block
        return None
    return None


def blocks_from_pages(page_texts: Sequence[str]) -> list[Block]:
    """Blocks in reading order; a table split across pages comes back as one block."""
    blocks: list[Block] = []
    for page, text in enumerate(page_texts, start=1):
        page_blocks = _parse_page(text, page)
        previous = blocks[-1] if blocks else None
        continued = _continuation(previous, page_blocks, page)
        if isinstance(previous, TableBlock) and continued is not None:
            page_blocks.remove(continued)
            extra = continued.rows
            if _same_header(extra[0], previous.rows[0]):
                extra = extra[1:]
            blocks[-1] = TableBlock(pages=(*previous.pages, page), rows=previous.rows + extra)
        blocks.extend(page_blocks)
    return blocks
