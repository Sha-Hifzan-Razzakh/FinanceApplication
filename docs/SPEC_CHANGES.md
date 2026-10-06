# Spec changes
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->

Append before `make docs`. Format: `### SC-NNN — YYYY-MM-DD` then bullets What changed · Why (Q/DR id) · Tasks affected.

### SC-001 — 2026-10-06
- What changed: CS-005 responsibility names the error envelope and DomainError.status_code.
- Why: DR-001
- Tasks affected: T-101, T-306

### SC-002 — 2026-10-06
- What changed: Stack rows for import-linter (dev) and PyJWT; Redis row also used by T-108 (Arq).
- Why: DR-002, DR-005, DR-012
- Tasks affected: T-101, T-102, T-108

### SC-003 — 2026-10-06
- What changed: Bootstrap pyproject row: each dependency is added by the task that first needs it.
- Why: DR-003
- Tasks affected: T-101

### SC-004 — 2026-10-06
- What changed: Settings gains auth_issuer, auth_audience, auth_public_key, agent_subject; CS-006 responsibility states the claim mapping; GET /invoices/{file_id} notes 404 for another entity.
- Why: DR-005, DR-006, DR-011
- Tasks affected: T-102, T-107, T-108

### SC-005 — 2026-10-06
- What changed: LedgerEntry.body is dict[str, Any]; LedgerEntry.hash covers every column; CS-011/CS-012 describe the trace provider and lock; Persistence run_ledger notes the triggers.
- Why: DR-007, DR-008
- Tasks affected: T-104, T-105

### SC-006 — 2026-10-06
- What changed: CS-014 drops the LangChain bridge; CS-027 gains it; CS-015 continues the active trace; new CS-108 (setup_logging and trace helpers).
- Why: DR-008
- Tasks affected: T-105, T-111

### SC-007 — 2026-10-06
- What changed: new contract M-59 UploadMeta; FileRecord.size_bytes cites MAX_UPLOAD_BYTES; M-54 defined in T-106; CS-018 returns (FileRecord, bool); CS-019 states 413/415 rules; ports FileRecordStore and EventPublisher; new CS-109–CS-112; Persistence object key {entity}/{sha256} and full file_records columns; Pydantic rule counts 59 contracts.
- Why: DR-006, DR-009, DR-010
- Tasks affected: T-106, T-107

### SC-008 — 2026-10-06
- What changed: CS-020/CS-021 signatures take their dependencies; ports RunStore and LedgerWriter; new CS-113–CS-116; Persistence runs lists the status and terminal values and UNIQUE(thread_id).
- Why: DR-011, DR-012
- Tasks affected: T-108

### SC-009 — 2026-10-06
- What changed: M-07 InvoiceDraft "Defined in" T-111 → T-112.
- Why: DR-014
- Tasks affected: T-111, T-112

### SC-010 — 2026-10-06
- What changed: CS-023 JevDecisions T-109 → T-204; CS-024 intent T-109 → T-208; new CS-117 route_classification (domain/classification.py) in T-109.
- Why: DR-015, DR-016
- Tasks affected: T-109, T-204, T-208

### SC-011 — 2026-10-06
- What changed: CS-025 read_pdf takes storage as a keyword argument and states its Document shape; new CS-118 blocks_from_pages (domain/layout.py); Stack row and Framework Rules row for pypdf.
- Why: DR-017
- Tasks affected: T-110, T-111
