# Debt
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->
One row per `TODO(T-xxx)` or shortcut left in code. Append with `cat >>`; delete the row when its task clears it.

| ID | Added | Where (file:line) | What is missing | Cleared by task | Risk until then |
|---|---|---|---|---|---|
| DEBT-001 | 2026-10-05 | invoice_to_pay/control/errors.py:10 | DomainError subclasses (CS-081) and their status codes | T-306 | Routes can only raise the base DomainError (400) |
| DEBT-002 | 2026-10-05 | invoice_to_pay/observability/tracing.py:43 | OpenTelemetry callback bridge for model calls | T-111 | Model calls will not appear as spans |
| DEBT-003 | 2026-10-06 | invoice_to_pay/main.py:44 | Open the ERP MCP client session in lifespan | T-202 | None until ERP tools exist |
| DEBT-004 | 2026-10-06 | invoice_to_pay/main.py:45 | LangGraph AsyncPostgresSaver checkpointer in lifespan | T-213 | Runs are not durable across restarts |
| DEBT-005 | 2026-10-06 | invoice_to_pay/application/use_cases/settle_invoice.py:49 | Invoke run_graph with thread_id | T-208 | A started run stops after "received" |
| DEBT-006 | 2026-10-06 | invoice_to_pay/application/use_cases/settle_invoice.py:24 | A worker crash between the run row and the "received" ledger entry leaves a run without its first entry; a redelivery sees the run as started | T-213 | Rare missing first ledger entry (Q-005) |
| DEBT-007 | 2026-10-05 | invoice_to_pay/main.py:26 | /health returns 503 when the database or Redis is down | none yet (Q-002) | Liveness only; no readiness signal |
| DEBT-008 | 2026-10-06 | adapters/jev_decisions.py (not created) | JevDecisions adapter: Jev request/response shape and httpx dependency | T-204 (after OD-04) | No real DecisionPort until OD-04 is decided |
| DEBT-009 | 2026-10-06 | agents/nodes/intent.py (not created) | intent node: classify, compile GoalSpec, reject or hold per route_classification, pre-flight predicates | T-208 | Documents are not routed in a run until the graph exists |
| DEBT-010 | 2026-10-06 | invoice_to_pay/contracts/decisions.py:6 | DuplicateScores, LineMapping, ScopeDecision, QueryClassification | T-204, T-205, T-403, T-504 | None until their tasks start |
