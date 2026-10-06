# Decisions
<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->

Append records with `cat >>`; no need to read the file. Never rewrite a past decision; supersede it.

## Accepted architecture decisions
| ID | Decision | Why | Status |
|---|---|---|---|
| ADR-001 | Hexagonal layout; frameworks only in adapters/, agents/, api/, mcp_servers/, evals/ | Every framework stays swappable; domain logic is testable without them | accepted |
| ADR-002 | LangGraph is the only orchestrator of a flow; AutoGen only inside review_team | One owner of control flow, checkpoints and interrupts | accepted |
| ADR-003 | Every external write goes through control.act() with an ExpectedEffect | Admissibility, budget, escalation, idempotency and verification in one place | accepted |
| ADR-004 | Money is Decimal; times are timezone-aware UTC | No rounding or timezone errors in payments | accepted |
| ADR-005 | Jev sits behind DecisionPort with an LLM structured-output fallback | An early-access dependency must not block the build | accepted |
| ADR-006 | spec/itp_data.py is the specification; workbook and generated docs are rebuilt from it | One source of truth; code follows the spec | accepted |
| ADR-007 | docs/PROGRESS.md owns build status and is edited only through scripts/progress.py | Status travels with the code; the model never rewrites the file | accepted |
| ADR-008 | One Claude Code session per session group, on the group's suggested model | Fixed per-session cost paid 16 times, not 56; opus only where mistakes are costly | accepted |

## Open decisions (work proceeds on the default until resolved)
| ID | Decision | Why it matters | Default until decided | Status |
|---|---|---|---|---|
| OD-01 | Which ERP and which API endpoints? | Defines the ERP MCP server tools' internals | Build against tests/fakes/erp_api with the tool contracts as the interface | open |
| OD-02 | Mail provider and MCP mail server (Microsoft Graph, Gmail, IMAP) | Mailbox intake and sending | Fake mail MCP server in tests; real one at T-502 | open |
| OD-03 | LLM provider and pinned model ids for extract and reason roles | LangChain provider package and costs | Settings fields llm_extract_model, llm_reason_model; choose before T-111 | open |
| OD-04 | Jev API access, request/response shape, pinned model id | JevDecisions adapter | DecisionPort with an LLM-structured-output fallback adapter until access is confirmed | open |
| OD-05 | AutoGen vs Microsoft Agent Framework for the review team | AutoGen is in maintenance mode | AutoGen behind review_team only; swap later without touching the graph | open |
| OD-06 | OCR for scans: local (e.g. Tesseract via LlamaIndex reader) or a hosted parser | Reading quality and data residency | PDF text layer first; scans held for review until decided | open |
| OD-07 | Approval console UI technology | E2E tests and SSE client | Minimal server-rendered pages; API is the contract | open |
| OD-08 | Hosting and vault (Azure Key Vault vs HashiCorp Vault) | Vault adapter and deployment | HashiCorp Vault dev mode locally | open |
| OD-09 | Job queue: Arq or Celery | Worker code | Arq (async, Redis already present) | open |
| OD-10 | Telephony source for voicemail webhooks | T-503 intake | Upload endpoint for audio files until decided | open |

## Decision records
Record format: `### DR-NNN — YYYY-MM-DD — <title>` then bullets Closes · Context · Decision · Consequences · Decided by.

### DR-001 — 2026-10-05 — Base DomainError and one error envelope ahead of T-306
- Closes: gap between CS-005 (T-101) and CS-081 (T-306)
- Context: domain_error_handler needs DomainError, but the hierarchy belongs to T-306.
- Decision: control/errors.py defines only DomainError with class attribute status_code (default 400); the handler returns {"error": {"type", "message"}} with that status.
- Consequences: T-306 adds the subclasses and sets their status codes. SC-001.
- Decided by: Claude in T-101 (PR #1, merged by Hifzan)

### DR-002 — 2026-10-05 — import-linter is a dev dependency
- Closes: G-09 gap (make lint and D-05 need it; it was not on the Stack)
- Context: Framework Rules are enforced by lint-imports.
- Decision: import-linter 2.x in the dev group; contracts in pyproject.toml, one per framework boundary.
- Consequences: Stack row added. SC-002.
- Decided by: Claude in T-101 (PR #1, merged by Hifzan)

### DR-003 — 2026-10-05 — Each dependency is added by the task that first needs it
- Closes: Bootstrap pyproject note ("deps from the Stack sheet")
- Context: locking all ~25 Stack packages at T-101 slows sync and pulls unused frameworks.
- Decision: pyproject gets a Stack package in the task that first imports it; uv.lock records the resolved version.
- Consequences: Bootstrap row reworded. SC-003.
- Decided by: Claude in T-101 (PR #1, merged by Hifzan)

### DR-004 — 2026-10-05 — Lazy module-level app for fastapi-cli
- Closes: `fastapi dev invoice_to_pay/main.py` needs a module attribute; create_app is a factory
- Decision: main.py exposes `app` through PEP 562 __getattr__/__dir__, so importing main needs no environment.
- Consequences: none for the spec.
- Decided by: Claude in T-101 (PR #1, merged by Hifzan)

### DR-005 — 2026-10-05 — Bearer tokens: PyJWT, RS256 public key, claim mapping
- Closes: T-102 gaps (no JWT library, no verification settings, no claim mapping)
- Decision: pyjwt[crypto] only in api/deps.py; RS256 verified with Settings.auth_public_key (PEM, \n escapes accepted), auth_issuer, auth_audience; iss, aud, exp, sub required; claims sub→subject, entity→entity, roles (list)→roles, scope (space-separated string)→scopes, kind→kind (default user); any failure is 401.
- Consequences: three required ITP_AUTH_* settings; Stack row for PyJWT; identity provider still open (Q-001). SC-002, SC-004.
- Decided by: Hifzan

### DR-006 — 2026-10-05 — Another entity's resource answers 404
- Closes: T-102 / T-107 cross-entity status
- Decision: entity filtering lives in the query, so a resource of another entity reads as absent (404, not 403).
- Consequences: GET /invoices/{file_id} documents it. SC-004.
- Decided by: Hifzan

### DR-007 — 2026-10-05 — Ledger hash covers every column; table is append-only in the database
- Closes: conflict between LedgerEntry.hash "sha256(prev_hash + body)" and T-104 "Done when: editing any row fails"
- Decision: hash = sha256(prev_hash + canonical JSON of run_id, seq, kind, body, trace_id, at); body holds JSON values only (dict[str, Any]); triggers refuse UPDATE, DELETE and TRUNCATE on itp.run_ledger; appends take a per-run advisory lock.
- Consequences: deleting a run's last rows is caught by the triggers, not by the chain. SC-005.
- Decided by: Hifzan (hash scope); Claude (triggers, lock)

### DR-008 — 2026-10-05 — Tracing layout: bridge in the LangChain adapter, logs and trace helpers in observability
- Closes: CS-014 "LangChain callback bridge" vs Framework Rules (LangChain only in adapters/langchain_llm.py); structlog listed under T-105 without a code section
- Decision: the OpenTelemetry callback bridge moves to LangChainLLM (CS-027, T-111); observability/tracing.py adds setup_logging, current_trace_id, inject_trace and attached_trace (CS-108); RunLedger takes a required trace_id provider because control/ imports no OpenTelemetry; run_span continues the active trace.
- Consequences: SC-005, SC-006.
- Decided by: Claude in T-105 (PR #5)

### DR-009 — 2026-10-05 — Intake contracts: UploadMeta, (record, duplicate), entity-first object keys
- Closes: T-106 gaps (UploadMeta undefined; TS-04 duplicate flag; object key format; InvoiceReceived timing; UUIDv7)
- Decision: UploadMeta(channel, sender, untrusted_text_id), frozen, extra='forbid', no entity field; FileService.put returns (FileRecord, duplicate); objects stored at {entity}/{sha256} (FileRecord rule wins over the Persistence row); InvoiceReceived defined in T-106 because CS-018 emits it; contracts/common.uuid7 implements RFC 9562; S3 credentials and endpoint come from the standard AWS_* variables.
- Consequences: new contract M-59. SC-007.
- Decided by: Hifzan (UploadMeta, return shape); Claude (key format, uuid7, AWS_* — to confirm, Q-003)

### DR-010 — 2026-10-05 — FileRecordStore and EventPublisher ports; emit on every put
- Closes: application layer cannot import SQLAlchemy or the queue
- Decision: FileRecordStore (get_by_hash, get, insert with first-insert-wins) and EventPublisher (publish) in application/ports.py, with SqlFileRecordStore and, from T-108, ArqEventPublisher; put emits InvoiceReceived on duplicates too, so a lost first emit cannot strand a file; T-108 dedupes runs.
- Consequences: SC-007.
- Decided by: Hifzan

### DR-011 — 2026-10-06 — Agent identity and run status vocabulary
- Closes: T-108 gaps (no principal in the worker; runs.status and terminal undefined)
- Decision: Settings.agent_subject (ITP_AGENT_SUBJECT, default agent:invoice-to-pay); runs act as Principal(agent_subject, agent, evt.entity); status in running|paused|finished; terminal in Succeeded|Failed|Stopped|Abandoned|Held|Rejected, set only when finished; UNIQUE(thread_id) with thread_id = entity:file_id; RunStore and LedgerWriter ports.
- Consequences: tool scopes for the agent come with T-202/T-210. SC-004, SC-008.
- Decided by: Hifzan

### DR-012 — 2026-10-06 — OD-09 closed: Arq
- Closes: OD-09
- Decision: Arq on Redis for jobs (ArqEventPublisher, workers/settings.py WorkerSettings); the job carries the W3C trace context.
- Consequences: Stack Redis row lists T-108. SC-002, SC-008.
- Decided by: Hifzan (accepted the default by asking for T-108)

### DR-013 — 2026-10-06 — G-01 and G-02 were built as per-task PRs
- Context: G-01/G-02 were built before the session-group workflow arrived, as one stacked branch and PR per task (#1–#8).
- Decision: keep #2–#8 as they are and record them per task in PROGRESS; from G-03, one branch per group via /next-group.
- Decided by: Hifzan

### DR-014 — 2026-10-06 — InvoiceDraft is defined in T-112, not T-111
- Closes: contradiction between M-07 "defined in T-111" and CS-030/CS-031 (T-112), where T-111 depends on T-112
- Context: T-112 builds contracts/invoice.py with InvoiceLine, InvoiceDraft and Invoice (CS-030) and draft_to_invoice(d: InvoiceDraft, …) (CS-031); InvoiceDraft cannot wait for the later task.
- Decision: M-07 InvoiceDraft is defined in T-112; T-111 imports it. "Every non-null field has an entry in field_quotes" covers the scalar fields; lines are quoted by InvoiceLine.source. draft_to_invoice raises ValueError (contracts/ cannot import control/); T-111 maps it to ExtractionInvalid.
- Consequences: SC-009. TS-02 (catalogued under T-111, target CS-031) is covered by the CS-031 tests in T-112 and is re-checked in T-111.
- Decided by: Claude in G-03 (confirm in review)

### DR-015 — 2026-10-06 — T-109 builds the port, the contract and the routing rule; the Jev adapter and the intent node move
- Closes: T-109 could not be finished as written (OD-04 open: no Jev request/response shape; CS-024 needs InvoiceRunState and GoalSpec from G-07; the listed "already defined" contracts come from T-204, T-205, T-403, T-504, T-207)
- Context: asked in the G-03 session; DecisionPort's only real implementation is the Jev adapter or the LLM fallback (needs LLMPort, T-111).
- Decision: T-109 delivers CS-022 DecisionPort, M-09 DocumentClassification and the pure domain function route_classification (CS-117). CS-023 JevDecisions moves to T-204, the first task that needs a real decision source, unless OD-04 is decided earlier. CS-024 intent moves to T-208 (run graph skeleton), where InvoiceRunState and GoalSpec exist.
- Consequences: SC-010. DEBT-008, DEBT-009. OD-04 stays open and now blocks T-204.
- Decided by: Hifzan (build the rule now; port + schema only, adapter after OD-04); Claude (target tasks T-204 and T-208)

### DR-016 — 2026-10-06 — Classification routing rules
- Closes: T-109 "Done when" (statements and reminders never reach extraction; low confidence goes to a person) had no stated thresholds or outcomes
- Decision: route_classification(c, min_confidence) returns hold when doc_type_p or readable_p is below min_confidence (inclusive at the threshold), else extract for an invoice and reject for every other type (credit notes belong to another goal type). Callers pass Settings.doc_type_threshold for both probabilities.
- Consequences: no separate readability setting (Q-006). The rule is a domain function, so the later intent node only wires it.
- Decided by: Claude in G-03 (confirm in review)
