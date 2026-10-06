# Conventions
<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->

| ID | Area | Rule | Example |
|---|---|---|---|
| C-01 | Layout | Hexagonal: domain/ and application/ import no framework; adapters/ hold one framework each | domain/matching.py imports only stdlib + contracts |
| C-02 | Typing | Full type hints; mypy strict on domain, contracts, control, application | def three_way_match(inv: Invoice, ...) -> MatchResult |
| C-03 | Money | Decimal everywhere; quantize to 2 places at boundaries; never float | Decimal('48300.00') |
| C-04 | Time | Timezone-aware UTC datetimes; dates as date; Asia/Dubai only for display and payment-run calendars | datetime.now(UTC) |
| C-05 | IDs | UUIDv7 for internal ids; ERP ids kept as strings | uuid7() |
| C-06 | Idempotency keys | entity:invoice_number:action[:n] | meridian-supply:INV-88213:post |
| C-07 | Async | async all the way for I/O; no blocking calls in the event loop; CPU-heavy work in workers | await erp.get_po(...) |
| C-08 | Errors | Raise typed DomainError subclasses from control/errors.py; never bare Exception; routes map them via one handler | raise Inadmissible('validation not passed') |
| C-09 | Logging | structlog JSON with run_id, entity, trace_id; no print; no payload bodies or secrets | log.info('posted', posting_id=...) |
| C-10 | Naming | snake_case modules and functions; PascalCase models; graph node names = function names | post_and_schedule |
| C-11 | Contracts | Implement models exactly as on Contracts / Contract Fields; changes go through the data module first | No extra fields on Invoice |
| C-12 | Prompts | Prompts live in prompts/ as versioned files, loaded by id via PromptRegistry; no inline prompt strings | prompts/extract_invoice/v1.md |
| C-13 | Writes | Every external write goes through control.act() with an ExpectedEffect | await act(state, 'post_invoice', env, expected) |
| C-14 | Tests | Tests first for every task; unit tests have no network; integration tests use the local stack; fakes in tests/fakes | tests/unit/domain/test_matching.py |
| C-15 | Docstrings | One-line docstring per public function stating the responsibility from Code Sections | """Deterministic match with typed variances.""" |
| C-16 | Commits | One task per branch and PR: feat(T-206): three-way match | Branch t-206-three-way-match |
| C-17 | Config | All thresholds and URLs from Settings; no magic numbers in code | settings.post_alone_max_aed |
| C-18 | Migrations | Every table change via Alembic; never create tables at app start (except LangGraph checkpointer setup) | alembic revision -m 'approvals' |
