# Handoff
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->
Overwritten by /end-session. Under 200 words. Enough to continue with no other context.

Last updated: 2026-10-06

- Where things stand: G-01, G-02, G-03 built (T-101–T-110, T-112); INC-1 needs only G-04. T-109 delivered the port, contract and routing rule; the Jev adapter moved to T-204, the intent node to T-208.
- Group / task: none current. Next is G-04 Extraction (sonnet): T-111, T-113.
- Branch state: T-101 merged. Open stack, each on the one before: #2 (t-102) … #8 (t-108), #9 (docs-session-workflow), #10 (g03-invoice-contracts-and-reading). Merge in order, retargeting each next PR to main.
- Exact next step: Hifzan decides OD-03 (LLM provider, pinned model ids, embedding model); then, once the stack merges, /start-session and /next-group for G-04.
- Blockers: OD-03 blocks T-111. OD-04 (Jev API shape) blocks T-204.
- Uncommitted work: none.
- Tests: 280 unit pass. Integration (Postgres 16, Redis, S3/moto) last passed at G-02.
