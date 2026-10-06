# Debt
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->
One row per `TODO(T-xxx)` or shortcut left in code. Append with `cat >>`; delete the row when its task clears it.

| ID | Added | Where (file:line) | What is missing | Cleared by task | Risk until then |
|---|---|---|---|---|---|
| DEBT-001 | 2026-10-05 | invoice_to_pay/control/errors.py:10 | DomainError subclasses (CS-081) and their status codes | T-306 | Routes can only raise the base DomainError (400) |
| DEBT-003 | 2026-10-06 | invoice_to_pay/main.py:44 | Open the ERP MCP client session in lifespan | T-202 | None until ERP tools exist |
| DEBT-004 | 2026-10-06 | invoice_to_pay/main.py:45 | LangGraph AsyncPostgresSaver checkpointer in lifespan | T-213 | Runs are not durable across restarts |
| DEBT-005 | 2026-10-06 | invoice_to_pay/application/use_cases/settle_invoice.py:49 | Invoke run_graph with thread_id | T-208 | A started run stops after "received" |
| DEBT-006 | 2026-10-06 | invoice_to_pay/application/use_cases/settle_invoice.py:24 | A worker crash between the run row and the "received" ledger entry leaves a run without its first entry; a redelivery sees the run as started | T-213 | Rare missing first ledger entry (Q-005) |
| DEBT-007 | 2026-10-05 | invoice_to_pay/main.py:26 | /health returns 503 when the database or Redis is down | none yet (Q-002) | Liveness only; no readiness signal |
| DEBT-008 | 2026-10-06 | adapters/jev_decisions.py (not created) | JevDecisions adapter: Jev request/response shape and httpx dependency | T-204 (after OD-04) | No real DecisionPort until OD-04 is decided |
| DEBT-009 | 2026-10-06 | agents/nodes/intent.py (not created) | intent node: classify, compile GoalSpec, reject or hold per route_classification, pre-flight predicates | T-208 | Documents are not routed in a run until the graph exists |
| DEBT-010 | 2026-10-06 | invoice_to_pay/contracts/decisions.py:6 | DuplicateScores, LineMapping, ScopeDecision, QueryClassification | T-204, T-205, T-403, T-504 | None until their tasks start |
| DEBT-011 | 2026-10-06 | invoice_to_pay/adapters/llamaindex_reader.py:30 | A PDF with no text layer (a scan) returns no Documents; the read node must hold it for review | T-111 | A scan reaches the read node as an empty list |
| DEBT-012 | 2026-10-06 | invoice_to_pay/application/ports.py (LLMPort) | LLMPort.chat_with_tools and its ToolCall/message contracts | T-305 if it needs tool calling, else drop the method (no task names bind_tools) | No tool-calling model path |
| DEBT-013 | 2026-10-06 | agents/nodes/read.py (not created) | read_invoice node (CS-029): wires extract_invoice into the graph state | T-208 | Extraction is not part of a run until the graph exists |
| DEBT-014 | 2026-10-06 | invoice_to_pay/adapters/langchain_llm.py | Token usage goes to a callback, not yet to BudgetMeter | T-211 | Model usage is not counted against the run budget |
| DEBT-015 | 2026-10-06 | invoice_to_pay/application/use_cases/extract_invoice.py | resolve_supplier: no vendor-master lookup exists yet; the caller supplies one | T-203 (ERP get_vendor) | Without it every read is held for "supplier not found" |
| DEBT-016 | 2026-10-06 | evals/deepeval/test_extraction.py | The live extraction eval has not been run: this session had no provider key. Offline tests cover the dataset, the exact-amount scorer and the judge mapping; the first real score is unknown | T-601 (CI eval job with provider keys; also grows the set to 200) | Prompt or model problems show only when someone runs `make eval` with keys |
