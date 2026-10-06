"""Twenty labelled invoices (fictitious suppliers), rendered as text-layer PDFs.

Every label is computed once and printed in the PDF, so the expected amounts and the document
cannot drift apart. TS-34 grows this set to 200 later.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from tests.fakes.pdfs import Line, make_pdf

D = Decimal
_CENT = D("0.01")
_COLS = (50, 250, 330, 430)
_HEADER = ("Description", "Qty", "Unit price", "Amount")
_ROWS_PER_PAGE = 6


@dataclass(frozen=True)
class LabelLine:
    """One labelled invoice line."""

    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


@dataclass(frozen=True)
class LabelledInvoice:
    """What the document says; the extraction must reproduce the amounts exactly."""

    case_id: str
    supplier_name: str
    number: str
    issued_on: date
    currency: str
    vat_rate: Decimal
    lines: tuple[LabelLine, ...]
    subtotal: Decimal
    vat: Decimal
    total: Decimal


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def _case(
    index: int,
    supplier: str,
    currency: str,
    rate: str,
    items: list[tuple[str, str, str]],
) -> LabelledInvoice:
    lines = tuple(
        LabelLine(desc, D(qty), D(price), _money(D(qty) * D(price))) for desc, qty, price in items
    )
    subtotal = sum((line.amount for line in lines), D("0"))
    vat = _money(subtotal * D(rate))
    return LabelledInvoice(
        case_id=f"INV-{index:02d}",
        supplier_name=supplier,
        number=f"{supplier.split()[0][:3].upper()}-{70000 + index * 37}",
        issued_on=date(2026, 9, 1) + timedelta(days=index * 3),
        currency=currency,
        vat_rate=D(rate),
        lines=lines,
        subtotal=subtotal,
        vat=vat,
        total=subtotal + vat,
    )


_SPECS: list[tuple[str, str, str, list[tuple[str, str, str]]]] = [
    ("Gulf Steel Trading LLC", "AED", "0.05", [("HEB 200 beam 6m", "120", "400.00")]),
    (
        "Al Noor Packaging",
        "AED",
        "0.05",
        [("Carton box 40x30x20", "2500", "1.85"), ("Packing tape 48mm", "300", "4.20")],
    ),
    (
        "Desert Fuel Supplies",
        "AED",
        "0.05",
        [("Diesel delivery litres", "8000", "2.7600")],
    ),
    (
        "Harbour Logistics FZE",
        "USD",
        "0",
        [("Container 40ft haulage", "3", "1250.00"), ("Port handling fee", "3", "310.50")],
    ),
    (
        "Meridian Office Mart",
        "AED",
        "0.05",
        [
            ("A4 paper 80gsm ream", "400", "12.50"),
            ("Ballpoint pen blue box", "60", "9.90"),
            ("Stapler heavy duty", "12", "34.75"),
        ],
    ),
    (
        "Falcon Safety Equipment",
        "AED",
        "0.05",
        [("Hard hat white", "150", "18.25"), ("Safety vest class 2", "150", "11.40")],
    ),
    (
        "Oasis Cleaning Services",
        "AED",
        "0.05",
        [("Monthly cleaning contract", "1", "14500.00")],
    ),
    (
        "Baltic Fasteners GmbH",
        "EUR",
        "0",
        [
            ("Anchor bolt M20", "4000", "0.8350"),
            ("Hex nut M20", "4000", "0.1120"),
            ("Washer M20", "8000", "0.0450"),
        ],
    ),
    (
        "Crescent Electrical",
        "AED",
        "0.05",
        [
            ("Copper wire 2.5mm per m", "1500", "3.4125"),
            ("Circuit breaker 32A", "40", "58.00"),
            ("Junction box IP65", "75", "21.30"),
            ("Cable tray 3m", "60", "46.80"),
        ],
    ),
    ("Skyline Scaffolding", "AED", "0.05", [("Scaffold hire per week", "6", "2150.00")]),
    (
        "Nile Paints Trading",
        "USD",
        "0.05",
        [("Exterior paint 20L", "85", "64.90"), ("Primer 20L", "40", "48.25")],
    ),
    (
        "Pearl Catering Co",
        "AED",
        "0.05",
        [("Lunch boxes site team", "1200", "17.50"), ("Water bottles 500ml", "5000", "0.65")],
    ),
    (
        "Gulf Steel Trading LLC",
        "AED",
        "0.05",
        [
            ("Plate 10mm 2x1m", "30", "1180.00"),
            ("Angle 50x50x5 6m", "200", "96.40"),
            ("Round bar 16mm 12m", "350", "71.15"),
            ("Flat bar 40x5 6m", "180", "38.90"),
            ("Channel 100 6m", "90", "162.20"),
            ("Pipe 2in 6m", "120", "88.75"),
            ("Beam 150 12m", "25", "945.00"),
            ("Mesh 6mm sheet", "60", "212.30"),
        ],
    ),
    (
        "Lotus Hydraulics",
        "EUR",
        "0.05",
        [("Hydraulic hose 3/4in", "250", "9.8000"), ("Coupling DN20", "500", "3.6500")],
    ),
    (
        "Dune Transport Services",
        "AED",
        "0",
        [("Truck hire per day", "14", "950.00")],
    ),
    (
        "Mirage IT Solutions",
        "USD",
        "0.05",
        [
            ("Laptop 14in business", "25", "1149.00"),
            ("Docking station", "25", "189.50"),
            ("Monitor 27in", "25", "279.90"),
        ],
    ),
    (
        "Palm Garden Maintenance",
        "AED",
        "0.05",
        [("Landscaping monthly", "1", "8200.00"), ("Irrigation repair", "4", "375.25")],
    ),
    (
        "Alpine Tools AG",
        "EUR",
        "0",
        [
            ("Cordless drill 18V", "20", "129.90"),
            ("Drill bit set 25pc", "60", "17.45"),
            ("Angle grinder 125mm", "15", "84.60"),
            ("Cutting disc 125mm", "800", "0.9250"),
            ("Safety goggles", "100", "5.15"),
            ("Work gloves pair", "200", "3.80"),
            ("Tool bag large", "20", "42.00"),
        ],
    ),
    (
        "Zenith Concrete Works",
        "AED",
        "0.05",
        [("Concrete C40 per m3", "320", "285.00"), ("Pump hire per day", "5", "1450.00")],
    ),
    (
        "Tidewater Marine Services",
        "USD",
        "0.05",
        [("Crane barge hire per day", "3", "4200.00"), ("Mooring fees", "3", "380.75")],
    ),
]

LABELLED: list[LabelledInvoice] = [
    _case(index, *spec) for index, spec in enumerate(_SPECS, start=1)
]


def _row(y: int, cells: tuple[str, ...]) -> Line:
    return (y, list(zip(_COLS, cells, strict=True)))


def _price(case: LabelledInvoice, value: Decimal) -> str:
    places = 4 if value.as_tuple().exponent == -4 else 2
    return f"{value:,.{places}f}"


def render_pdf(case: LabelledInvoice) -> bytes:
    """The invoice as a text-layer PDF; a long one runs its table onto a second page."""
    rows = [
        _row(
            0,
            (
                line.description,
                f"{line.quantity:,}",
                _price(case, line.unit_price),
                f"{line.amount:,.2f}",
            ),
        )
        for line in case.lines
    ]
    chunks = [rows[i : i + _ROWS_PER_PAGE] for i in range(0, len(rows), _ROWS_PER_PAGE)]
    pages: list[list[Line]] = []
    for number, chunk in enumerate(chunks, start=1):
        if number == 1:
            page: list[Line] = [
                (740, [(50, case.supplier_name), (400, f"Invoice {case.number}")]),
                (720, [(50, f"Date {case.issued_on.isoformat()}  Currency {case.currency}")]),
            ]
        else:
            page = [(740, [(50, f"Invoice {case.number} (continued)")])]
        page.append(_row(680, _HEADER))
        page += [(680 - 20 * (i + 1), cells) for i, (_, cells) in enumerate(chunk)]
        if number == len(chunks):
            y = 680 - 20 * (len(chunk) + 2)
            page += [
                (y, [(330, "Subtotal"), (430, f"{case.subtotal:,.2f}")]),
                (y - 20, [(330, f"VAT {case.vat_rate * 100:.0f}%"), (430, f"{case.vat:,.2f}")]),
                (y - 40, [(330, f"Total {case.currency}"), (430, f"{case.total:,.2f}")]),
            ]
        page.append((60, [(250, f"Page {number} of {len(chunks)}")]))
        pages.append(page)
    return make_pdf(pages)
