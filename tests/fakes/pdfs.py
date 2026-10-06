"""A minimal PDF writer for tests: pages of text cells at fixed positions, in a monospace font."""

from collections.abc import Sequence

# One text line: (y from the bottom of the page in points, [(x in points, text), ...]).
Line = tuple[int, Sequence[tuple[int, str]]]


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(pages: Sequence[Sequence[Line]]) -> bytes:
    """Build a valid PDF whose pages hold the given text lines (an empty page has no text)."""
    objects: list[bytes] = []

    def add(body: str | bytes) -> int:
        objects.append(body.encode() if isinstance(body, str) else body)
        return len(objects)

    catalog = add("")  # placeholder, filled once the page tree exists
    tree = add("")
    font = add("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    page_ids: list[int] = []
    for lines in pages:
        ops = ["BT", "/F1 10 Tf"]
        for y, cells in lines:
            for x, text in cells:
                ops.append(f"1 0 0 1 {x} {y} Tm ({_escape(text)}) Tj")
        ops.append("ET")
        stream = "\n".join(ops)
        content = add(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        page_ids.append(
            add(
                f"<< /Type /Page /Parent {tree} 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font} 0 R >> >> /Contents {content} 0 R >>"
            )
        )
    kids = " ".join(f"{i} 0 R" for i in page_ids)
    objects[tree - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()
    objects[catalog - 1] = f"<< /Type /Catalog /Pages {tree} 0 R >>".encode()

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    trailer = f"<< /Size {len(objects) + 1} /Root {catalog} 0 R >>"
    out += f"trailer\n{trailer}\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)
