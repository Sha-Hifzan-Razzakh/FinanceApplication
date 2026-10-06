# Handoff
Overwritten by /end-session. Under 200 words. Enough to continue with no other context.

Last updated: 2026-10-06

- Where things stand: G-01 to G-04 built (T-101–T-113, 13 of 56); INC-1 archived. OD-03 closed (DR-018): providers anthropic/openai/deepseek by `provider:model` ids, OpenAI embeddings. read_invoice node (CS-029) moved to T-208; extract_invoice use case (CS-119) is built.
- Group / task: none current. Next is G-05 ERP over MCP (sonnet): T-201, T-202, T-212. OD-01 (ERP API) uses tests/fakes/erp_api by default.
- Branch state: T-101 merged. Open stack, each on the one before: #2 … #8, #9, #10 (g03), then g04-extraction (this group; PR to open, base g03). Merge in order, retargeting each next PR to main.
- Exact next step: Hifzan merges the stack; then /start-session and /next-group for G-05. Also run `make eval` once with provider keys (DEBT-016).
- Blockers: OD-04 (Jev API shape) blocks T-204. T-203 must supply resolve_supplier (DEBT-015).
- Uncommitted work: none.
- Tests: 400 unit pass. Integration last passed at G-02. Live extraction eval never run.
