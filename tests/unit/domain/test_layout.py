"""CS-118 blocks_from_pages: text blocks and whole tables from layout-mode page text."""

from invoice_to_pay.domain.layout import TableBlock, TextBlock, blocks_from_pages

GAP = "      "


def row(*cells: str) -> str:
    return GAP.join(cells)


HEADER = row("Description", "Qty", "Unit price", "Amount")
BEAM = row("HEB 200 beam 6m", "120", "400.00", "48000.00")
PLATE = row("Plate 10mm", "2", "50.00", "100.00")
BOLT = row("Anchor bolt M20", "40", "5.00", "200.00")


def page(*lines: str) -> str:
    return "\n".join(lines)


def tables(blocks: list[TextBlock | TableBlock]) -> list[TableBlock]:
    return [b for b in blocks if isinstance(b, TableBlock)]


# one page


def test_text_and_a_table_on_one_page() -> None:
    blocks = blocks_from_pages(
        [page("Gulf Steel Trading LLC", "", "Bill to: Meridian Supply", "", HEADER, BEAM, PLATE)]
    )
    assert [type(b) for b in blocks] == [TextBlock, TableBlock]
    text, table = blocks
    assert isinstance(text, TextBlock) and isinstance(table, TableBlock)
    assert text.lines == ("Gulf Steel Trading LLC", "Bill to: Meridian Supply")
    assert text.pages == (1,)
    assert table.pages == (1,)
    assert table.rows[0] == ("Description", "Qty", "Unit price", "Amount")
    assert table.rows[2] == ("Plate 10mm", "2", "50.00", "100.00")


def test_table_text_is_pipe_separated_rows() -> None:
    (table,) = tables(blocks_from_pages([page(HEADER, BEAM)]))
    assert (
        table.text
        == "Description | Qty | Unit price | Amount\nHEB 200 beam 6m | 120 | 400.00 | 48000.00"
    )


def test_a_two_cell_line_is_text_not_a_table() -> None:
    blocks = blocks_from_pages([page(row("Subtotal", "48300.00"), row("VAT", "2415.00"))])
    assert tables(blocks) == []
    assert len(blocks) == 1 and isinstance(blocks[0], TextBlock)


def test_a_single_wide_line_is_text_not_a_table() -> None:
    blocks = blocks_from_pages([page("Intro", row("a", "b", "c"), "Outro")])
    assert tables(blocks) == []


def test_blank_lines_inside_a_table_are_tolerated_up_to_two() -> None:
    (table,) = tables(blocks_from_pages([page(HEADER, "", BEAM, "", "", PLATE)]))
    assert len(table.rows) == 3


def test_three_blank_lines_end_the_table() -> None:
    found = tables(blocks_from_pages([page(HEADER, BEAM, "", "", "", PLATE, BOLT)]))
    assert [len(t.rows) for t in found] == [2, 2]


def test_page_number_furniture_is_dropped() -> None:
    blocks = blocks_from_pages([page("Body", "", "Page 1 of 2"), page("More", "page 2")])
    assert [b.lines for b in blocks if isinstance(b, TextBlock)] == [("Body",), ("More",)]


def test_pages_without_text_give_no_blocks() -> None:
    assert blocks_from_pages(["", "  \n \n"]) == []


# tables across pages


def test_done_when_a_two_page_table_comes_back_as_one_table_with_page_numbers() -> None:
    """Done when: a two-page line-item table comes back as one table with page numbers."""
    blocks = blocks_from_pages(
        [
            page("Invoice INV-88213", "", HEADER, BEAM, PLATE, "", "Page 1 of 2"),
            page(HEADER, BOLT, "", "Page 2 of 2"),
        ]
    )
    (table,) = tables(blocks)
    assert table.pages == (1, 2)
    assert [r[0] for r in table.rows] == [
        "Description",
        "HEB 200 beam 6m",
        "Plate 10mm",
        "Anchor bolt M20",
    ]


def test_the_repeated_header_is_dropped_but_a_missing_one_is_fine() -> None:
    (with_header,) = tables(blocks_from_pages([page(HEADER, BEAM), page(HEADER, BOLT)]))
    assert [r[0] for r in with_header.rows].count("Description") == 1
    (without,) = tables(blocks_from_pages([page(HEADER, BEAM), page(PLATE, BOLT)]))
    assert without.pages == (1, 2)
    assert len(without.rows) == 4


def test_a_caption_before_the_continued_table_is_kept_as_text() -> None:
    blocks = blocks_from_pages(
        [page(HEADER, BEAM), page("Invoice INV-88213 (continued)", "", HEADER, BOLT)]
    )
    (table,) = tables(blocks)
    assert table.pages == (1, 2)
    captions = [b for b in blocks if isinstance(b, TextBlock)]
    assert [c.lines for c in captions] == [("Invoice INV-88213 (continued)",)]
    assert captions[0].pages == (2,)


def test_a_caption_without_a_repeated_header_prevents_the_merge() -> None:
    found = tables(blocks_from_pages([page(HEADER, BEAM), page("Other section", "", PLATE, BOLT)]))
    assert [t.pages for t in found] == [(1,), (2,)]


def test_text_after_the_table_on_the_first_page_prevents_the_merge() -> None:
    found = tables(
        blocks_from_pages([page(HEADER, BEAM, "", "Subtotal 48300.00"), page(HEADER, BOLT)])
    )
    assert [t.pages for t in found] == [(1,), (2,)]


def test_a_different_column_count_prevents_the_merge() -> None:
    narrow = [row("Code", "Amount", "Note"), row("A", "1.00", "x")]
    found = tables(blocks_from_pages([page(HEADER, BEAM), page(*narrow)]))
    assert [t.pages for t in found] == [(1,), (2,)]


def test_a_table_can_run_over_three_pages() -> None:
    (table,) = tables(
        blocks_from_pages([page(HEADER, BEAM), page(HEADER, PLATE), page(HEADER, BOLT)])
    )
    assert table.pages == (1, 2, 3)
    assert len(table.rows) == 4


def test_an_empty_page_between_two_tables_prevents_the_merge() -> None:
    found = tables(blocks_from_pages([page(HEADER, BEAM), "", page(HEADER, BOLT)]))
    assert [t.pages for t in found] == [(1,), (3,)]


def test_text_blocks_record_their_page() -> None:
    blocks = blocks_from_pages([page("one"), page("two")])
    assert [(b.pages, b.lines) for b in blocks if isinstance(b, TextBlock)] == [
        ((1,), ("one",)),
        ((2,), ("two",)),
    ]
