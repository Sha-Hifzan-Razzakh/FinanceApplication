# Open questions
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->
Append rows with `cat >>`; no need to read the file.

| ID | Raised | Task | Question | Blocks | Answer | Answered |
|---|---|---|---|---|---|---|
| Q-001 | 2026-10-05 | T-102 | Which identity provider issues bearer tokens (issuer, key rotation, token URL for OpenAPI)? | — |  |  |
| Q-002 | 2026-10-05 | T-101 | Which task owns /health readiness (503 when Postgres or Redis is down)? | — |  |  |
| Q-003 | 2026-10-05 | T-106 | Keep the S3 endpoint and credentials in standard AWS_* variables, or add ITP_OBJECT_ENDPOINT to Settings (C-17)? | — |  |  |
| Q-004 | 2026-10-05 | T-109 | Should doc_type_threshold, line_map_threshold and near_duplicate_threshold be constrained to (0, 1]? | — |  |  |
| Q-005 | 2026-10-06 | T-213 | Confirm T-213 (durable resume) also re-opens a run whose "received" ledger entry is missing (DEBT-006) | — |  |  |
| Q-006 | 2026-10-06 | T-109 | Should readability get its own threshold (ITP_READABLE_THRESHOLD) instead of reusing doc_type_threshold? | — |  |  |
