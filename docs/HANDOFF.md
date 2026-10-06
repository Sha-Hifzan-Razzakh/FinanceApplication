# Handoff
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->
Overwritten by /end-session. Under 200 words. Enough to continue with no other context.

Last updated: 2026-10-06

- Where things stand: G-01 Spine and G-02 File intake built and tested (T-101–T-108). Upload → file stored once → Arq job → one run row, ledger "received", one trace.
- Group / task: none current. Next is G-03 Invoice contracts and reading (sonnet): T-112, T-109, T-110.
- Branch state: T-101 merged (#1). PRs #2–#8 (t-102…t-108) are stacked per task and await merge in order, then the docs PR (docs-session-workflow, on top of #8). Retarget each next PR to main as the one below merges.
- Exact next step: after the stack merges, run /start-session, then /next-group to branch g03-invoice-contracts-and-reading from main.
- Blockers: none for G-03. Decide OD-03 (LLM provider and pinned model ids) before G-04. Open questions Q-001–Q-005 do not block G-03.
- Uncommitted work: none.
- Tests: 178 unit pass; 23 integration pass against local Postgres 16 + Redis (S3 tests need MinIO or moto on :9000).
