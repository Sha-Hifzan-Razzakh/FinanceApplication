# Session log
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->
Appended by `python3 scripts/progress.py log`. Entries move to docs/archive/ when an increment is archived.

### S-001 · 2026-10-06 · —
- Done: Built G-01 (T-101–T-105) and G-02 (T-106–T-108) as PRs #1–#8; adopted the session-group workflow: spec/, generated docs, progress.py, DR-001–DR-013, SC-001–SC-008
- Next: Merge #2–#8 then the docs PR; /start-session, then /next-group for G-03 (sonnet)
- Notes: Local Postgres 16 and Redis run via service/redis-server; MinIO is not downloadable here, S3 tests ran against a scratch moto server
### S-002 · 2026-10-06 · —
- Done: Built G-03: T-112 invoice contracts, T-109 DecisionPort + classification rule (Jev adapter and intent node moved to T-204/T-208), T-110 PDF reading (pypdf layout, tables whole). PR #10.
- Next: Decide OD-03 (LLM provider, pinned model ids); after the stack #2-#10 merges, /start-session then /next-group for G-04 (sonnet)
- Notes: Switched to sonnet for G-03 on request; asked Hifzan for T-109 and T-110 design; DR-014..017, SC-009..011, DEBT-008..011, Q-006
