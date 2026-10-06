# Invoice-to-Pay

An agent that settles supplier invoices for Meridian Supply: intake, reading, validation,
three-way match, approval and posting with payment scheduling. Every write it makes is
admissible, idempotent, verified and auditable.

- **Spec:** `docs/spec/InvoiceToPay_BuildWorkbook.xlsx` (the source of truth)
- **Working rules for Claude Code:** `CLAUDE.md`
- **One prompt per build task:** `tasks/T-xxx.md`, taken in increment order (INC-1 … INC-6)

## Quickstart

```bash
cp .env.example .env      # fill pinned model ids once OD-03 / OD-04 are decided
uv sync
make test-unit lint typecheck
make dev                  # http://localhost:8000/health
```

`make setup` also starts the local services (`docker compose up -d`) and runs migrations once they exist (T-104).

## Status

| Increment | Goal | State |
|---|---|---|
| INC-1 Walking skeleton | Upload a PDF, get a typed invoice, with ledger and trace | T-101 done; T-102 – T-107 in review |
| INC-2 … INC-6 | See the Increments sheet | Not started |
