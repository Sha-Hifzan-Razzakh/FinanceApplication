# Progress
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->
Edited only by `python3 scripts/progress.py` (start · done · block · archive). Do not read or rewrite by hand.

## Current focus
- Group: none
- Branch: —
- Since: —

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
