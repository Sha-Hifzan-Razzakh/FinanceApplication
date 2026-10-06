# Invoice-to-Pay

An agent that settles supplier invoices for Meridian Supply: intake, reading, validation,
three-way match, approval and posting with payment scheduling. Every write it makes is
admissible, idempotent, verified and auditable.

- **Spec (source of truth):** `spec/itp_data.py`; `make docs` regenerates CLAUDE.md, `docs/`, `tasks/` and `scripts/progress.py` from it
- **Where to start:** `docs/README.md` (docs map) and `docs/HANDOFF.md`; status via `make progress`
- **Workbook view of the spec:** `docs/spec/InvoiceToPay_BuildWorkbook.xlsx`

## Quickstart

```bash
cp .env.example .env      # fill pinned model ids once OD-03 / OD-04 are decided
uv sync
make test-unit lint typecheck
make dev                  # http://localhost:8000/health
```

`make setup` also starts the local services (`docker compose up -d`) and runs migrations once they exist (T-104).

## Status

`make progress` prints the current and next session group; `docs/PROGRESS.md` holds per-task status.
