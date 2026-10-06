# Plan
<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->

Six increments, sixteen session groups. `python3 scripts/progress.py summary` always names the next group, so this file is rarely needed.

| Increment | Name | Goal | Gate (done when) |
|---|---|---|---|
| INC-1 | Walking skeleton | Upload a PDF, get a typed invoice, with ledger and trace | 20 labelled invoices extract with every amount correct |
| INC-2 | Clean invoices post themselves | Validate, match and post matched invoices under the limit, verified | A clean invoice posts once even when the post call is retried |
| INC-3 | Exceptions wait for approval | Variances produce a proposal; the run pauses for a signed approval | The INV-88213 run passes end to end |
| INC-4 | Evidence and answers | Contract answers with citations; analyst-auditor team; supplier memory | Every resolution claim cites its evidence; Ragas baseline recorded |
| INC-5 | Every channel, every supplier | Portals, mailbox, voicemail; supplier replies under standing approval | One invoice arriving twice is processed once; bank-change requests routed away |
| INC-6 | Assurance and operations | Trace-derived tests, red team, E2E, dashboards, release gate | Red-team suite blocks merges; dashboards live |

## Session groups (in this order; one branch per group)
| Group | Name | Tasks | Model | Days | Why this model |
|---|---|---|---|---|---|
| G-01 | Spine | T-101, T-102, T-103, T-104, T-105 | sonnet | 3.5 | Scaffolding, settings, contracts, ledger, tracing: well-known patterns |
| G-02 | File intake | T-106, T-107, T-108 | sonnet | 2.0 | Storage port, upload route, job handler |
| G-03 | Invoice contracts and reading | T-112, T-109, T-110 | sonnet | 2.5 | Models with validators, Jev adapter, PDF reader |
| G-04 | Extraction | T-111, T-113 | sonnet | 2.5 | Structured output + eval set; move to opus only if the eval keeps failing |
| G-05 | ERP over MCP | T-201, T-202, T-212 | sonnet | 4.0 | FastMCP server and client: mechanical once contracts exist |
| G-06 | Validation and match | T-203, T-204, T-205, T-206 | sonnet | 3.5 | Pure functions with exhaustive unit tests |
| G-07 | Run core | T-207, T-209, T-208, T-213 | opus | 4.0 | Graph, state, reducer, predicates, durable resume: design-critical |
| G-08 | Control layer | T-210, T-211, T-214 | opus | 4 | control.act(): every money write passes here |
| G-09 | Escalation and approvals | T-301, T-302, T-303, T-304 | opus | 4.0 | Autonomy matrix, two-person rule, interrupt/resume with revalidation |
| G-10 | Resolution and recovery | T-305, T-306, T-307, T-308 | opus | 4.0 | Recovery policy, compensation, the end-to-end scenario |
| G-11 | Contract knowledge | T-401, T-402 | sonnet | 3.0 | Ingestion and retriever with filters |
| G-12 | Cited answers | T-403, T-404, T-405, T-406 | opus | 3.5 | Claim verification and entity isolation through a tool |
| G-13 | Memory and review team | T-407, T-408, T-409, T-410 | sonnet | 4.5 | Mem0 adapter, Send fan-out, AutoGen node, Ragas baseline |
| G-14 | Channels | T-501, T-502, T-503 | sonnet | 3.5 | Playwright collector, mail intake, transcription |
| G-15 | Supplier communication | T-504, T-505, T-506 | opus | 2.0 | Untrusted input, bank-change routing, supplier isolation |
| G-16 | Assurance | T-601, T-602, T-603, T-604, T-605 | sonnet | 4.5 | Test suites, red team config, dashboards, CI gate |

## Capabilities
| ID | Capability | What it does |
|---|---|---|
| CAP-0 | Spine | Identity, entity, settings, ledger, tracing, contracts shared by every capability |
| CAP-1 | Invoice intake | Collect invoices from mailbox, portals and scans; store each file once with provenance |
| CAP-2 | Invoice reading | Turn a PDF or scan into a typed, validated Invoice with a source quote per field |
| CAP-3 | Validation and duplicate check | Vendor active, bank equals master, tax number valid, not a duplicate |
| CAP-4 | Three-way match | Invoice vs purchase order vs goods receipts, within tolerances; typed variances |
| CAP-5 | Exception resolution | Evidence, a proposal per variance, analyst-auditor review, human approval |
| CAP-6 | Policy and contract answers | Cited answers from contracts and AP policy; used as a tool by CAP-5 |
| CAP-7 | Posting and payment scheduling | Post once, verify by re-read, schedule per terms, register the undo |
| CAP-8 | Supplier communication | Status replies, credit-note requests, voicemail intake; never bank changes |
| CAP-9 | Assurance and operations | Eval suites, red team, E2E, dashboards, release gate |

## Tasks in dependency order
| # | Task | Group | Title | Depends on | Days | Spec |
|---|---|---|---|---|---|---|
| 1 | T-101 | G-01 | Project skeleton and settings | — | 0.5 | [spec](../tasks/T-101.md) |
| 2 | T-102 | G-01 | Principal and entity dependency | T-101 | 1 | [spec](../tasks/T-102.md) |
| 3 | T-103 | G-01 | Common contracts | T-101 | 0.5 | [spec](../tasks/T-103.md) |
| 4 | T-104 | G-01 | Run ledger | T-101 | 1 | [spec](../tasks/T-104.md) |
| 5 | T-105 | G-01 | Tracing | T-101 | 0.5 | [spec](../tasks/T-105.md) |
| 6 | T-106 | G-02 | File service and storage port | T-103 | 1 | [spec](../tasks/T-106.md) |
| 7 | T-107 | G-02 | Upload route | T-102, T-106 | 0.5 | [spec](../tasks/T-107.md) |
| 8 | T-108 | G-02 | Intake job handler | T-106 | 0.5 | [spec](../tasks/T-108.md) |
| 9 | T-109 | G-03 | Document classification | T-103 | 0.5 | [spec](../tasks/T-109.md) |
| 10 | T-110 | G-03 | PDF reading | T-106 | 1 | [spec](../tasks/T-110.md) |
| 11 | T-112 | G-03 | Invoice contracts and validators | T-103 | 1 | [spec](../tasks/T-112.md) |
| 12 | T-201 | G-05 | ERP MCP server: read tools | T-103 | 1.5 | [spec](../tasks/T-201.md) |
| 13 | T-202 | G-05 | ERP port and MCP client adapter | T-201 | 1 | [spec](../tasks/T-202.md) |
| 14 | T-203 | G-06 | Validation rules | T-202 | 1 | [spec](../tasks/T-203.md) |
| 15 | T-204 | G-06 | Duplicate detection | T-202 | 1 | [spec](../tasks/T-204.md) |
| 16 | T-205 | G-06 | Line mapping | T-202 | 0.5 | [spec](../tasks/T-205.md) |
| 17 | T-206 | G-06 | Three-way match | T-205 | 1 | [spec](../tasks/T-206.md) |
| 18 | T-207 | G-07 | Goal spec, limits and predicates | T-103 | 1 | [spec](../tasks/T-207.md) |
| 19 | T-209 | G-07 | Run state and reducer | T-103 | 1 | [spec](../tasks/T-209.md) |
| 20 | T-210 | G-08 | Tool registry | T-202 | 1 | [spec](../tasks/T-210.md) |
| 21 | T-211 | G-08 | control.act() | T-210, T-209 | 2 | [spec](../tasks/T-211.md) |
| 22 | T-212 | G-05 | ERP write tools | T-201 | 1.5 | [spec](../tasks/T-212.md) |
| 23 | T-214 | G-08 | Posting and scheduling nodes | T-211, T-212 | 1 | [spec](../tasks/T-214.md) |
| 24 | T-301 | G-09 | Autonomy matrix and escalation | T-211 | 1 | [spec](../tasks/T-301.md) |
| 25 | T-302 | G-09 | Approvals store and API | T-102, T-301 | 1.5 | [spec](../tasks/T-302.md) |
| 26 | T-305 | G-10 | Resolution proposal (single agent) | T-206 | 1.5 | [spec](../tasks/T-305.md) |
| 27 | T-307 | G-10 | Compensation registry | T-212 | 0.5 | [spec](../tasks/T-307.md) |
| 28 | T-401 | G-11 | Contract ingestion | T-106 | 1.5 | [spec](../tasks/T-401.md) |
| 29 | T-402 | G-11 | Hybrid retriever with guards | T-401 | 1.5 | [spec](../tasks/T-402.md) |
| 30 | T-403 | G-12 | Answer graph | T-402 | 1.5 | [spec](../tasks/T-403.md) |
| 31 | T-404 | G-12 | Claim verifier | T-403 | 1 | [spec](../tasks/T-404.md) |
| 32 | T-405 | G-12 | Ask route | T-403 | 0.5 | [spec](../tasks/T-405.md) |
| 33 | T-406 | G-12 | ask_policy as a tool | T-403, T-210 | 0.5 | [spec](../tasks/T-406.md) |
| 34 | T-407 | G-13 | Supplier memory | T-209 | 1 | [spec](../tasks/T-407.md) |
| 35 | T-408 | G-13 | Resolution subgraph | T-305 | 1 | [spec](../tasks/T-408.md) |
| 36 | T-409 | G-13 | Analyst–auditor team | T-408 | 1.5 | [spec](../tasks/T-409.md) |
| 37 | T-410 | G-13 | Grounding baseline | T-405 | 1 | [spec](../tasks/T-410.md) |
| 38 | T-501 | G-14 | Portal collector | T-106 | 1.5 | [spec](../tasks/T-501.md) |
| 39 | T-502 | G-14 | Mailbox intake | T-106 | 1 | [spec](../tasks/T-502.md) |
| 40 | T-503 | G-14 | Voicemail transcription | T-106 | 1 | [spec](../tasks/T-503.md) |
| 41 | T-504 | G-15 | Supplier query classification | T-503 | 0.5 | [spec](../tasks/T-504.md) |
| 42 | T-505 | G-15 | Supplier replies | T-504, T-301 | 1 | [spec](../tasks/T-505.md) |
| 43 | T-506 | G-15 | Supplier isolation filter | T-505 | 0.5 | [spec](../tasks/T-506.md) |
| 44 | T-603 | G-16 | Approval console E2E | T-302 | 1 | [spec](../tasks/T-603.md) |
| 45 | T-604 | G-16 | Dashboards and alerts | T-105 | 1 | [spec](../tasks/T-604.md) |
| 46 | T-111 | G-04 | Invoice extraction | T-110, T-112 | 1.5 | [spec](../tasks/T-111.md) |
| 47 | T-113 | G-04 | Extraction test set | T-111 | 1 | [spec](../tasks/T-113.md) |
| 48 | T-208 | G-07 | Run graph skeleton | T-207, T-209 | 1.5 | [spec](../tasks/T-208.md) |
| 49 | T-213 | G-07 | Checkpointer and durable resume | T-208 | 0.5 | [spec](../tasks/T-213.md) |
| 50 | T-303 | G-09 | Interrupt and resume | T-302, T-213 | 1 | [spec](../tasks/T-303.md) |
| 51 | T-304 | G-09 | Run event stream | T-208 | 0.5 | [spec](../tasks/T-304.md) |
| 52 | T-306 | G-10 | Recovery policy and node | T-208 | 1 | [spec](../tasks/T-306.md) |
| 53 | T-308 | G-10 | Scenario: INV-88213 | T-303, T-306 | 1 | [spec](../tasks/T-308.md) |
| 54 | T-601 | G-16 | Trace-derived tests | T-308 | 1 | [spec](../tasks/T-601.md) |
| 55 | T-602 | G-16 | Red-team suite | T-308 | 1 | [spec](../tasks/T-602.md) |
| 56 | T-605 | G-16 | Release gate | T-601, T-602, T-603 | 0.5 | [spec](../tasks/T-605.md) |

Total estimate: 55.0 days across 56 tasks (indicative).
