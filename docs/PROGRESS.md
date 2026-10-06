# Progress
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->
Edited only by `python3 scripts/progress.py` (start · done · block · archive). Do not read or rewrite by hand.

## Current focus
- Group: G-04
- Branch: g04-extraction
- Since: 2026-10-06

## INC-1 · Walking skeleton
| Task | Title | Group | Depends on | Status | Branch / PR | Updated | Notes |
|---|---|---|---|---|---|---|---|
| T-101 | Project skeleton and settings | G-01 | — | done | #1 (merged) | 2026-10-06 |  |
| T-102 | Principal and entity dependency | G-01 | T-101 | done | #2 | 2026-10-06 |  |
| T-103 | Common contracts | G-01 | T-101 | done | #3 | 2026-10-06 |  |
| T-104 | Run ledger | G-01 | T-101 | done | #4 | 2026-10-06 |  |
| T-105 | Tracing | G-01 | T-101 | done | #5 | 2026-10-06 |  |
| T-106 | File service and storage port | G-02 | T-103 | done | #6 | 2026-10-06 |  |
| T-107 | Upload route | G-02 | T-102, T-106 | done | #7 | 2026-10-06 |  |
| T-108 | Intake job handler | G-02 | T-106 | done | #8 | 2026-10-06 |  |
| T-109 | Document classification | G-03 | T-103 | done | g03-invoice-contracts-and-reading | 2026-10-06 |  |
| T-110 | PDF reading | G-03 | T-106 | done | g03-invoice-contracts-and-reading | 2026-10-06 |  |
| T-111 | Invoice extraction | G-04 | T-110, T-112 | done | g04-extraction | 2026-10-06 |  |
| T-112 | Invoice contracts and validators | G-03 | T-103 | done | g03-invoice-contracts-and-reading | 2026-10-06 |  |
| T-113 | Extraction test set | G-04 | T-111 | in progress | g04-extraction | 2026-10-06 |  |

## INC-2 · Clean invoices post themselves
| Task | Title | Group | Depends on | Status | Branch / PR | Updated | Notes |
|---|---|---|---|---|---|---|---|
| T-201 | ERP MCP server: read tools | G-05 | T-103 | todo |  |  |  |
| T-202 | ERP port and MCP client adapter | G-05 | T-201 | todo |  |  |  |
| T-203 | Validation rules | G-06 | T-202 | todo |  |  |  |
| T-204 | Duplicate detection | G-06 | T-202 | todo |  |  |  |
| T-205 | Line mapping | G-06 | T-202 | todo |  |  |  |
| T-206 | Three-way match | G-06 | T-205 | todo |  |  |  |
| T-207 | Goal spec, limits and predicates | G-07 | T-103 | todo |  |  |  |
| T-208 | Run graph skeleton | G-07 | T-207, T-209 | todo |  |  |  |
| T-209 | Run state and reducer | G-07 | T-103 | todo |  |  |  |
| T-210 | Tool registry | G-08 | T-202 | todo |  |  |  |
| T-211 | control.act() | G-08 | T-210, T-209 | todo |  |  |  |
| T-212 | ERP write tools | G-05 | T-201 | todo |  |  |  |
| T-213 | Checkpointer and durable resume | G-07 | T-208 | todo |  |  |  |
| T-214 | Posting and scheduling nodes | G-08 | T-211, T-212 | todo |  |  |  |

## INC-3 · Exceptions wait for approval
| Task | Title | Group | Depends on | Status | Branch / PR | Updated | Notes |
|---|---|---|---|---|---|---|---|
| T-301 | Autonomy matrix and escalation | G-09 | T-211 | todo |  |  |  |
| T-302 | Approvals store and API | G-09 | T-102, T-301 | todo |  |  |  |
| T-303 | Interrupt and resume | G-09 | T-302, T-213 | todo |  |  |  |
| T-304 | Run event stream | G-09 | T-208 | todo |  |  |  |
| T-305 | Resolution proposal (single agent) | G-10 | T-206 | todo |  |  |  |
| T-306 | Recovery policy and node | G-10 | T-208 | todo |  |  |  |
| T-307 | Compensation registry | G-10 | T-212 | todo |  |  |  |
| T-308 | Scenario: INV-88213 | G-10 | T-303, T-306 | todo |  |  |  |

## INC-4 · Evidence and answers
| Task | Title | Group | Depends on | Status | Branch / PR | Updated | Notes |
|---|---|---|---|---|---|---|---|
| T-401 | Contract ingestion | G-11 | T-106 | todo |  |  |  |
| T-402 | Hybrid retriever with guards | G-11 | T-401 | todo |  |  |  |
| T-403 | Answer graph | G-12 | T-402 | todo |  |  |  |
| T-404 | Claim verifier | G-12 | T-403 | todo |  |  |  |
| T-405 | Ask route | G-12 | T-403 | todo |  |  |  |
| T-406 | ask_policy as a tool | G-12 | T-403, T-210 | todo |  |  |  |
| T-407 | Supplier memory | G-13 | T-209 | todo |  |  |  |
| T-408 | Resolution subgraph | G-13 | T-305 | todo |  |  |  |
| T-409 | Analyst–auditor team | G-13 | T-408 | todo |  |  |  |
| T-410 | Grounding baseline | G-13 | T-405 | todo |  |  |  |

## INC-5 · Every channel, every supplier
| Task | Title | Group | Depends on | Status | Branch / PR | Updated | Notes |
|---|---|---|---|---|---|---|---|
| T-501 | Portal collector | G-14 | T-106 | todo |  |  |  |
| T-502 | Mailbox intake | G-14 | T-106 | todo |  |  |  |
| T-503 | Voicemail transcription | G-14 | T-106 | todo |  |  |  |
| T-504 | Supplier query classification | G-15 | T-503 | todo |  |  |  |
| T-505 | Supplier replies | G-15 | T-504, T-301 | todo |  |  |  |
| T-506 | Supplier isolation filter | G-15 | T-505 | todo |  |  |  |

## INC-6 · Assurance and operations
| Task | Title | Group | Depends on | Status | Branch / PR | Updated | Notes |
|---|---|---|---|---|---|---|---|
| T-601 | Trace-derived tests | G-16 | T-308 | todo |  |  |  |
| T-602 | Red-team suite | G-16 | T-308 | todo |  |  |  |
| T-603 | Approval console E2E | G-16 | T-302 | todo |  |  |  |
| T-604 | Dashboards and alerts | G-16 | T-105 | todo |  |  |  |
| T-605 | Release gate | G-16 | T-601, T-602, T-603 | todo |  |  |  |

## Completion records
### T-101 · Project skeleton and settings · done 2026-10-06 · #1 (merged)
- Evidence: App boots with settings validated; missing ITP_DATABASE_URL fails at startup (test_cs003_create_app_fails_fast_without_required_settings)
- Tests: unit: tests/unit/config, tests/unit/test_main.py
### T-102 · Principal and entity dependency · done 2026-10-06 · #2
- Evidence: No token/entity -> 401; meridian-supply token reading a meridian-projects record -> 404 (test_cs006_token_for_entity_a_cannot_read_entity_b, test_cs006_tampered_entity_is_401)
- Tests: unit: tests/unit/api/test_deps.py
### T-103 · Common contracts · done 2026-10-06 · #3
- Evidence: Fact rejects unknown source; Quote rejects page < 1 (test_cs009_fact_rejects_unknown_source, test_cs009_quote_rejects_page_below_one)
- Tests: unit: tests/unit/contracts/test_common.py
### T-104 · Run ledger · done 2026-10-06 · #4
- Evidence: Editing any row (body, kind, at, trace_id, delete) makes verify_chain False on Postgres (test_cs013_editing_any_row_fails_verification)
- Tests: TS-03; integration: tests/integration/control/test_ledger.py
### T-105 · Tracing · done 2026-10-06 · #5
- Evidence: Upload request span, run span and node span share one trace id (test_done_when_upload_to_finish_shares_one_trace)
- Tests: unit: tests/unit/observability; integration: test_ledger_trace.py
### T-106 · File service and storage port · done 2026-10-06 · #6
- Evidence: Same PDF twice -> one FileRecord, duplicate=True second time; UNIQUE(entity, sha256) on Postgres
- Tests: TS-04; integration: test_sql_file_records.py, test_s3_storage.py (moto)
### T-107 · Upload route · done 2026-10-06 · #7
- Evidence: Oversized upload -> 413, non-PDF/image bytes -> 415 (test_cs019_oversized_upload_is_413, test_cs019_non_pdf_or_image_is_415); e2e via make dev
- Tests: unit: tests/unit/api/test_intake.py
### T-108 · Intake job handler · done 2026-10-06 · #8
- Evidence: Original + duplicate + redelivered job -> one run row on Redis/Arq/Postgres (test_done_when_redelivered_and_duplicate_jobs_start_one_run)
- Tests: unit: tests/unit/workers; integration: tests/integration/workers
### T-112 · Invoice contracts and validators · done 2026-10-06
- Evidence: Lines not summing to subtotal, or subtotal + VAT != total, raise ValueError (test_ts01_invoice_totals_must_add_up, test_cs030_subtotal_plus_vat_must_equal_total)
- Tests: TS-01; unit: tests/unit/contracts/test_invoice.py (45)
### T-109 · Document classification · done 2026-10-06
- Evidence: Non-invoice types never route to extraction and low confidence routes to hold (test_done_when_non_invoices_never_reach_extraction, test_done_when_low_type_confidence_goes_to_a_person); CS-023 moved to T-204 and CS-024 to T-208 (DR-015)
- Tests: unit: tests/unit/domain/test_classification.py, tests/unit/contracts/test_decisions.py, tests/unit/application/test_decision_port.py (31)
### T-110 · PDF reading · done 2026-10-06
- Evidence: A two-page line-item table comes back as one table with page numbers (test_done_when_a_two_page_line_item_table_is_one_table_with_page_numbers on generated PDFs; test_done_when_a_two_page_table_comes_back_as_one_table_with_page_numbers in the layout module)
- Tests: unit: tests/unit/domain/test_layout.py, tests/unit/adapters/test_llamaindex_reader.py (26)
### T-111 · Invoice extraction · done 2026-10-06
- Evidence: tests/unit/application/test_extract_invoice.py::test_invalid_totals_trigger_exactly_one_re_extraction and ::test_two_invalid_drafts_are_held_after_exactly_two_model_calls; TS-02 in tests/unit/contracts/test_invoice.py; make lint typecheck test-unit green (348)
- Tests: TS-02
