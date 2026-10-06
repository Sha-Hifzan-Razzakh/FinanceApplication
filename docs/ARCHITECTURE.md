# Architecture
<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->

Hexagonal: `domain/` and `application/` import no framework; each framework sits behind a port in `adapters/`; every external write passes through `control.act()`.

## Code sections by layer
### config
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-001 | T-101 | `config/settings.py` | class | Settings | Load and validate all configuration once at startup |
| CS-002 | T-101 | `config/settings.py` | function | get_settings | Single cached settings instance for Depends |

### api
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-003 | T-101 | `main.py` | function | create_app | App factory: routers, middleware, exception handlers |
| CS-004 | T-101 | `main.py` | function | lifespan | Open DB pool, Redis, MCP sessions, checkpointer; close on shutdown |
| CS-005 | T-101 | `api/errors.py` | function | domain_error_handler | Map typed domain errors to one error envelope {error: {type, message}}; status from DomainError.status_code (default 400) |
| CS-006 | T-102 | `api/deps.py` | dependency | get_principal | Validate RS256 JWT (iss, aud, exp, sub required); claims sub/entity/roles/scope/kind → Principal; any failure 401 |
| CS-007 | T-102 | `api/deps.py` | dependency | require_role | Dependency factory that refuses callers without a role |
| CS-019 | T-107 | `api/routers/intake.py` | route | POST /invoices/upload | Accept scan/PDF; 413 above MAX_UPLOAD_BYTES; 415 unless sniffed bytes are an allowed MimeType; FileService.put; 202 |
| CS-073 | T-302 | `api/routers/approvals.py` | route | GET /approvals, POST /approvals/{id}/approve\|decline | List pending; signed decisions; resume the run |
| CS-076 | T-304 | `api/streaming.py` | route | GET /runs/{id}/events | SSE: step, approval_required, held, finished |
| CS-090 | T-405 | `api/routers/ask.py` | route | POST /ask | Run the answer graph under the caller's entity |
| CS-112 | T-107 | `api/routers/intake.py` | route | GET /invoices/{file_id} | The caller's FileRecord; another entity's file is 404 |

### application
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-008 | T-102 | `application/context.py` | contextvar | current_principal | Carry the principal into graph nodes, adapters and tools |
| CS-016 | T-106 | `application/ports.py` | port | StoragePort | put/get/delete/presign bytes |
| CS-018 | T-106 | `files/service.py` | method | FileService.put | sha256, sniff mime, dedupe per entity, store at {entity}/{sha256}, write FileRecord, emit InvoiceReceived (also on duplicates); returns (record, duplicate) |
| CS-021 | T-108 | `application/use_cases/settle_invoice.py` | use case | start_settle_run | Create run row, ledger open, invoke run_graph with thread_id |
| CS-022 | T-109 | `application/ports.py` | port | DecisionPort | Typed decisions without text generation |
| CS-026 | T-111 | `application/ports.py` | port | LLMPort | The only way the app reaches a language model |
| CS-028 | T-111 | `prompts/registry.py` | class | PromptRegistry | Versioned prompts as data; id + version written to the ledger |
| CS-038 | T-202 | `application/ports.py` | port | ErpPort | Typed ERP operations the app depends on |
| CS-072 | T-302 | `approvals/service.py` | class | ApprovalService | Persist requests; enforce distinct approvers, roles, expiry; emit ApprovalRequested |
| CS-075 | T-303 | `application/use_cases/resume_run.py` | use case | resume_run | Resume the thread with the signed decision |
| CS-092 | T-407 | `application/ports.py` | port | MemoryPort | Supplier memory behind a port |
| CS-109 | T-106 | `application/ports.py` | port | FileRecordStore / EventPublisher | Persist FileRecords; hand events to their transport |
| CS-113 | T-108 | `application/ports.py` | port | RunStore / LedgerWriter | Run rows and ledger appends behind ports |

### contracts
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-009 | T-103 | `contracts/common.py` | model | Quote / Fact[T] / Principal | Provenance-carrying value types |
| CS-010 | T-103 | `contracts/common.py` | type alias | EntityId | One definition of the legal entities |
| CS-030 | T-112 | `contracts/invoice.py` | model | InvoiceLine / InvoiceDraft / Invoice | Typed invoice with arithmetic validators |
| CS-031 | T-112 | `contracts/invoice.py` | function | draft_to_invoice | Promote a draft once every required field is present and quoted |
| CS-047 | T-207 | `contracts/run.py` | model | Scope / GoalSpec / RunLimits | Compiled goal and stop conditions |
| CS-111 | T-106 | `contracts/common.py` | function | uuid7 | UUIDv7 (RFC 9562) with sub-millisecond counter for internal ids (C-05) |

### control
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-011 | T-104 | `control/ledger.py` | class | RunLedger | Append-only hash-chained ledger per run; trace_id provider injected (control/ imports no OpenTelemetry) |
| CS-012 | T-104 | `control/ledger.py` | method | RunLedger.append | Per-run advisory lock; hash every column with the previous hash; insert |
| CS-013 | T-104 | `control/ledger.py` | method | RunLedger.verify_chain | Recompute every hash; detect edits |
| CS-053 | T-210 | `control/registry.py` | class | ToolRegistry | Governance metadata for every tool |
| CS-054 | T-210 | `control/registry.py` | data | TOOLS | The registry entries (see Tool Registry sheet) |
| CS-055 | T-211 | `control/act.py` | function | act | Admissibility → budget → escalation → actuation → perception → belief update → effect check |
| CS-056 | T-211 | `control/admissibility.py` | function | admissible | Facts present and fresh; guard holds; not a stuck repeat; inferred facts not used for money |
| CS-057 | T-211 | `control/budget.py` | class | BudgetMeter | Atomic per-run and per-day counters; money-moved reservation |
| CS-058 | T-211 | `control/executor.py` | class | ToolExecutor | Only caller of tools: vault creds, timeout, idempotency key, dry run first if irreversible |
| CS-059 | T-211 | `control/perception.py` | function | perceive | Validate against output model; stamp source and trust; quarantine untrusted text |
| CS-060 | T-211 | `control/effects.py` | function | verify_effect | Re-read system of record; diff field by field; raise Mismatch |
| CS-071 | T-301 | `control/escalation.py` | function | escalate_if_needed | Raise Escalated with an ApprovalRequest when the matrix requires |
| CS-079 | T-306 | `control/recovery.py` | data | POLICY | Recovery policy table (see Recovery Policy sheet) |
| CS-081 | T-306 | `control/errors.py` | classes | DomainError hierarchy | Typed errors every control raises |
| CS-082 | T-307 | `control/compensation.py` | class | CompensationRegistry | Undo actions for irreversible steps, run in reverse and verified |

### observability
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-014 | T-105 | `observability/tracing.py` | function | setup_tracing | One provider per process; OTLP exporter when configured; resource attributes |
| CS-015 | T-105 | `observability/tracing.py` | context manager | run_span | Root span per run with run.id and entity attributes; continues the active trace; binds run_id/entity to logs |
| CS-108 | T-105 | `observability/tracing.py` | function | setup_logging / current_trace_id / inject_trace / attached_trace | structlog JSON with run_id, entity, trace_id; trace id for ledger entries; trace context across the job queue |
| CS-106 | T-604 | `observability/metrics.py` | module | metrics | Business and cost metrics |

### adapters
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-017 | T-106 | `adapters/s3_storage.py` | adapter | S3Storage | Object storage implementation with entity-prefixed keys |
| CS-023 | T-204 | `adapters/jev_decisions.py` | adapter | JevDecisions | Translate a Pydantic decision schema into Jev typed questions; pinned model |
| CS-025 | T-110 | `adapters/llamaindex_reader.py` | adapter | read_pdf | Layout-aware text with page numbers; tables kept whole: Documents in reading order with metadata file_id, pages and kind (text or table); a table that spans pages is one Document |
| CS-027 | T-111 | `adapters/langchain_llm.py` | adapter | LangChainLLM | init_chat_model per role; with_structured_output; usage → budget meter; OpenTelemetry callback bridge |
| CS-039 | T-202 | `adapters/erp_mcp_client.py` | adapter | ErpMcpClient | ClientSession.call_tool; validate structured result into output models |
| CS-040 | T-202 | `adapters/vault.py` | adapter | VaultCredentials | Short-lived credentials at call time; never in prompts |
| CS-085 | T-401 | `adapters/llamaindex_ingest.py` | adapter | ContractIngestor | Parse by clause; attach entity, supplier, version, effective dates, access group; refuse missing metadata |
| CS-086 | T-402 | `adapters/llamaindex_retrieval.py` | adapter | ContractRetriever | Fusion of vector + BM25 with mandatory entity/access filters |
| CS-087 | T-402 | `adapters/llamaindex_retrieval.py` | postprocessor | VersionGuard / AccessRecheck | Keep only the contract in force; re-check access live |
| CS-093 | T-407 | `adapters/mem0_memory.py` | adapter | Mem0Memory | Scoped user_id = entity:supplier; PII filter before add; results as inferred Evidence |
| CS-097 | T-501 | `adapters/playwright_portal.py` | adapter | PortalCollector | Fresh context per run; vault login; download new invoices; allowed domains |
| CS-098 | T-502 | `adapters/mail_mcp_client.py` | adapter | MailboxIntake | list_new_messages → attachments to FileService; bodies stored untrusted |
| CS-099 | T-503 | `adapters/whisper_speech.py` | adapter | WhisperTranscriber | faster-whisper with VAD; language; segments; stored untrusted |
| CS-110 | T-106 | `adapters/sql_file_records.py` | adapter | SqlFileRecordStore | file_records on Postgres; first insert wins per (entity, sha256) |
| CS-114 | T-108 | `adapters/sql_runs.py` | adapter | SqlRunStore | runs on Postgres; one run per thread_id |
| CS-115 | T-108 | `adapters/arq_events.py` | adapter | ArqEventPublisher | Enqueue InvoiceReceived with the caller's trace context |

### workers
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-020 | T-108 | `workers/intake.py` | job | handle_invoice_received | Start one run per file hash (idempotent); acts as the agent principal (Settings.agent_subject) for evt.entity |
| CS-116 | T-108 | `workers/settings.py` | config | WorkerSettings | Arq worker: functions, startup (DB pool, IntakeDeps), shutdown |

### agents
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-024 | T-208 | `agents/nodes/intent.py` | graph node | intent | Classify document; compile GoalSpec; reject non-invoices; pre-flight predicates |
| CS-029 | T-111 | `agents/nodes/read.py` | graph node | read_invoice | read_pdf → LLM InvoiceDraft → Invoice; one retry with errors; else Held for review |
| CS-042 | T-203 | `agents/nodes/validate.py` | graph node | validate | Fetch vendor and history; call validate_invoice; route ok / held / rejected |
| CS-044 | T-205 | `agents/nodes/map_lines.py` | graph node | map_lines | Jev maps each line to a PO SKU; below threshold leaves sku None |
| CS-046 | T-206 | `agents/nodes/match.py` | graph node | match | Fetch PO/receipts; call three_way_match; 'wait' if receipt not yet booked |
| CS-049 | T-208 | `agents/run_graph.py` | graph | build_run_graph | Nodes, conditional edges, compile with checkpointer |
| CS-050 | T-208 | `agents/routes.py` | function | route_validation / route_match / route_goal | Pure routing functions for conditional edges |
| CS-051 | T-209 | `agents/state.py` | model | InvoiceRunState | Typed run state with reducers |
| CS-066 | T-213 | `agents/checkpoint.py` | function | make_checkpointer | Durable checkpoints; thread_id = entity:file_id |
| CS-067 | T-214 | `agents/nodes/post.py` | graph node | post_and_schedule | Build ExpectedEffect; act(post_invoice); act(schedule_payment); emit InvoicePosted |
| CS-069 | T-214 | `agents/nodes/goal_check.py` | graph node | goal_check | Evaluate predicates; checkpoint; finish or loop |
| CS-074 | T-303 | `agents/nodes/escalate.py` | graph node | escalate | interrupt(ApprovalRequest); on resume revalidate digest, receipts, PO version |
| CS-077 | T-305 | `agents/nodes/resolve.py` | graph node | propose_resolution | Gather Evidence; LLM fills ResolutionProposal; enforce ≥1 evidence and totals |
| CS-080 | T-306 | `agents/nodes/recover.py` | graph node | recover | Look up rule; increment durable counter; route or abandon |
| CS-088 | T-403 | `agents/answer_graph.py` | graph | build_answer_graph | scope → retrieve → assemble → generate → verify (one regenerate) |
| CS-089 | T-404 | `agents/nodes/verify_claims.py` | graph node | verify_claims | Check each claim against its cited clause; citation ids must be in context |
| CS-091 | T-406 | `agents/tools/ask_policy.py` | tool | ask_policy | Answer graph as a read tool under the run's principal |
| CS-094 | T-408 | `agents/resolution_graph.py` | graph | build_resolution_graph | Send one branch per variance; merge proposals by reducer |
| CS-095 | T-409 | `agents/review_team.py` | graph node | review_team | Analyst proposes, auditor challenges; ≤6 messages; disagreement kept |
| CS-100 | T-504 | `agents/nodes/classify_query.py` | graph node | classify_query | Jev query type; bank_change → vendor-master queue |
| CS-101 | T-505 | `agents/nodes/reply.py` | graph node | draft_and_send_reply | Draft SupplierReply into template; act(send_message) under standing approval |

### evals
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-032 | T-113 | `evals/deepeval/test_extraction.py` | test module | test_extraction_amounts | Exact amount fields; GEval for descriptions |
| CS-096 | T-410 | `evals/ragas/test_grounding.py` | test module | test_contract_grounding | Faithfulness and context recall on golden questions |
| CS-103 | T-601 | `evals/deepeval/test_tool_sequences.py` | test module | test_tool_correctness | Expected tool sequence per run type |
| CS-104 | T-602 | `evals/promptfoo/promptfooconfig.yaml` | config | redteam suite | Adversarial invoices and spoofed emails; assert no post above gap, no bank change |
| CS-107 | T-605 | `.github/workflows/release-gate.yml` | config | release-gate | Block merge on any red suite |

### mcp_servers
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-033 | T-201 | `mcp_servers/erp/server.py` | server | erp_mcp | MCP server wrapping the ERP REST API |
| CS-034 | T-201 | `mcp_servers/erp/server.py` | tool | get_vendor | Vendor master record |
| CS-035 | T-201 | `mcp_servers/erp/server.py` | tool | find_invoices | Possible duplicates by supplier, amount, date window |
| CS-036 | T-201 | `mcp_servers/erp/server.py` | tool | get_po / get_receipts | PO and receipts with versions |
| CS-037 | T-201 | `mcp_servers/erp/auth.py` | middleware | verify_agent_token | Server-side scope check for every tool |
| CS-061 | T-212 | `mcp_servers/erp/server.py` | tool | post_invoice | Create AP posting; honour dry_run; return existing record for a seen key |
| CS-062 | T-212 | `mcp_servers/erp/server.py` | tool | get_posting / reverse_posting | Re-read and compensation |
| CS-063 | T-212 | `mcp_servers/erp/server.py` | tool | schedule_payment / unschedule_payment / get_payment_schedule | Payment scheduling and its undo |
| CS-064 | T-212 | `mcp_servers/erp/server.py` | tool | place_on_hold / release_hold | Protective hold and release |
| CS-065 | T-212 | `mcp_servers/erp/idempotency.py` | function | once | Server-side idempotency store keyed by request key |

### domain
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-041 | T-203 | `domain/validation.py` | function | validate_invoice | Run all rules; set hold or reject reason |
| CS-043 | T-204 | `domain/duplicates.py` | function | normalise_number / is_duplicate | Deterministic duplicate rule |
| CS-045 | T-206 | `domain/matching.py` | function | three_way_match | Deterministic match with typed variances |
| CS-048 | T-207 | `domain/predicates.py` | function | settled / impossible / must_stop | Success, failure and stop predicates over observed facts |
| CS-052 | T-209 | `domain/transitions.py` | function | apply_observation | Pure reducer: allowed fields per observation type; conflict detection; version+1 |
| CS-068 | T-214 | `domain/terms.py` | function | due_date / next_payment_run | Net terms → due date → first Monday run on/after due |
| CS-070 | T-301 | `domain/autonomy.py` | function | approvals_needed | The autonomy matrix as code |
| CS-078 | T-305 | `domain/evidence.py` | function | collect_evidence | PO lines, receipts, observations as Evidence; memory marked inadmissible |
| CS-102 | T-506 | `domain/supplier_scope.py` | function | facts_for_supplier | Drop any fact not belonging to the asking supplier |
| CS-117 | T-109 | `domain/classification.py` | function | route_classification | Hold what is unclear or illegible, reject what is not an invoice, extract the rest |
| CS-118 | T-110 | `domain/layout.py` | function | blocks_from_pages | Text blocks and tables from layout-mode page text; a table split across pages is one block (repeated header dropped, page furniture removed) |

### tests
| ID | Task | Module | Kind | Name | Responsibility |
|---|---|---|---|---|---|
| CS-083 | T-308 | `tests/scenarios/test_inv_88213.py` | test module | test_short_shipment_end_to_end | Short shipment, approval, timeout, idempotent retry, success |
| CS-084 | T-308 | `tests/fakes/stub_erp.py` | fake | StubErp | In-memory ERP that can time out after commit |
| CS-105 | T-603 | `tests/e2e/test_approval_console.py` | test module | test_approve_decline_expired | Approval console paths with page objects |

## Ports and adapters
| Port | Methods | Adapter | Framework | Features | Rule |
|---|---|---|---|---|---|
| LLMPort | structured(prompt_id, vars, schema) -> T; chat_with_tools(messages, tools) -> ToolCall | LangChainLLM | LangChain | init_chat_model, with_structured_output, bind_tools, callbacks (usage) | Only path to a model; prompt id and token usage recorded |
| DecisionPort | decide(schema: type[T], payload: str) -> T | JevDecisions | Jev | Typed choice / score / probability questions, pinned version | Fallback: LLM structured output when Jev unavailable |
| RetrieverPort | search(principal, question, k) -> list[Evidence] | ContractRetriever | LlamaIndex | BaseRetriever, QueryFusionRetriever, BM25Retriever, MetadataFilters, BaseNodePostprocessor | Entity and access filter is not optional |
| MemoryPort | recall(entity, supplier, q) / remember(...) / forget(...) | Mem0Memory | Mem0 | Memory.add, Memory.search, Memory.delete, user_id scoping | Recall returns inferred Evidence only |
| ErpPort | get_vendor, find_invoices, get_po, get_receipts, post_invoice, get_posting, reverse_posting, schedule_payment, unschedule_payment, place_on_hold | ErpMcpClient | MCP | ClientSession.call_tool, streamablehttp_client, structured content | All writes only via control.act() |
| MailPort | list_new_messages, get_attachment, send_message, get_sent | MailMcpClient | MCP | ClientSession.call_tool | Sent log is the verification source |
| BrowserPort | collect(portal) -> list[FileRecord] | PortalCollector | Playwright | async_playwright, BrowserContext, page.locator, page.expect_download | Fresh context per run |
| TranscriberPort | transcribe(audio) -> Transcript | WhisperTranscriber | Whisper | faster-whisper WhisperModel, vad_filter, initial_prompt | Output stored untrusted |
| StoragePort | put, get, delete, presign | S3Storage | Object storage SDK | boto3 / aioboto3 | Keys prefixed by entity |
| FileRecordStore | get_by_hash(entity, sha256), get(entity, file_id), insert(record) -> first record on conflict | SqlFileRecordStore | SQLAlchemy | insert … on_conflict_do_nothing | UNIQUE(entity, sha256); every read filtered by entity |
| EventPublisher | publish(event) | ArqEventPublisher | Arq | enqueue_job with _job_id, W3C trace carrier | Job id = event id; carries the caller's trace |
| RunStore | start(entity, thread_id, goal_type) -> (run_id, created) | SqlRunStore | SQLAlchemy | insert … on_conflict_do_nothing | UNIQUE(thread_id): one run per file |
| LedgerWriter | append(run_id, kind, body) -> LedgerEntry | RunLedger | SQLAlchemy | advisory lock, hash chain | Implemented by control.ledger.RunLedger |

## Graphs
| Graph | Node | Code section | Control states | Reads | Writes | Edges out |
|---|---|---|---|---|---|---|
| run_graph | intent | CS-024 | Intent, Termination | file | classification, goal | → read \| END (rejected: not an invoice) |
| run_graph | read | CS-029 | Decision, Perception | file | invoice | → validate \| recover |
| run_graph | validate | CS-042 | Admissibility, Belief update | invoice | vendor, validation | ok → map_lines · held → END · rejected → END |
| run_graph | map_lines | CS-044 | Decision | invoice, po | invoice (sku per line) | → match |
| run_graph | match | CS-046 | Belief update | invoice, po, receipts | match | matched → post · variances → resolve · wait → goal_check |
| run_graph | resolve | CS-094 | Planning, Decision | match | proposals | → escalate |
| run_graph | escalate | CS-074 | Escalation | proposals | approval | approve → post · decline → END (held for AP) |
| run_graph | post | CS-067 | Admissibility … Effect check | invoice, approval, match | posting, schedule | → notify \| recover |
| run_graph | notify | CS-101 | Actuation | posting, proposals | messages_sent | → goal_check |
| run_graph | recover | CS-080 | Recovery | error, attempts | — | Command(goto=read\|match\|post\|END) |
| run_graph | goal_check | CS-069 | Goal check | everything | terminal | done → END · loop → match (wait for receipt) |
| resolution_graph | fan_out | CS-094 | Planning | match.variances | — | Send('branch', variance) per variance |
| resolution_graph | branch | CS-077 | Context, Decision | variance | proposals (+=) | → review_team |
| resolution_graph | review_team | CS-095 | Decision | proposal, evidence | proposals | → END |
| answer_graph | scope | CS-088 | Intent | question | scope | in → retrieve · out → END (out_of_scope) |
| answer_graph | retrieve | CS-086 | Context | question, principal | nodes | evidence → assemble · weak → END (no_evidence) |
| answer_graph | assemble | CS-088 | Context | nodes | context | → generate |
| answer_graph | generate | CS-088 | Decision | context | answer | → verify |
| answer_graph | verify | CS-089 | Effect check | answer, context | claims.supported | supported → END · unsupported (once) → generate · again → END (no_evidence) |

## The 15 controls in code
| Control | Meaning here | Code sections | Frameworks | On failure |
|---|---|---|---|---|
| Received | Run row, ledger open, root span; file hash prevents a second run | CS-018, CS-020, CS-021, CS-011, CS-015 | FastAPI, job queue, OpenTelemetry | — |
| 1 Intent | Document type and GoalSpec for ap.settle_invoice; scope one invoice | CS-024, CS-047 | Jev, Pydantic | Rejected |
| 2 Termination | Success / failure / stop predicates; RunLimits | CS-047, CS-048 | Pydantic | Rejected |
| 3 Planning | Fixed plan per goal type; resolution adds branches | CS-049, CS-094, CS-095 | LangGraph, AutoGen | — |
| 4 Context | Invoice facts, PO, receipts, cited clauses, supplier memory; untrusted text wrapped | CS-078, CS-086, CS-087, CS-091, CS-093 | LlamaIndex, Mem0 | — |
| 5 Belief | Typed state; every fact with source | CS-009, CS-051 | Pydantic, LangGraph | — |
| 6 Admissibility | Preconditions, freshness, stuck guard, no inferred facts for money | CS-056, CS-053, CS-041, CS-043, CS-102 | — | Recovery → Held |
| 7 Decision | Model chooses only extraction, proposal and reply wording | CS-029, CS-077, CS-101 | LangChain | Recovery |
| 8 Budget | Tokens per run; money moved per day | CS-057 | Redis | Stopped |
| 9 Escalation | Autonomy matrix; interrupt; signed resume; revalidation | CS-070, CS-071, CS-074, CS-075, CS-072 | LangGraph, FastAPI | Escalated (paused) |
| 10 Actuation | One executor; vault creds; idempotency key; dry run first | CS-058, CS-039, CS-040, CS-061 | MCP | Recovery |
| 11 Perception | Schema-checked results; trust labels; quarantine | CS-059, CS-098, CS-099 | Pydantic, Jev | Held |
| 12 Belief update | Pure reducer; transition table; conflicts flagged | CS-052 | LangGraph reducer | Recovery (replan) |
| 13 Effect check | Re-read ERP or sent log; diff with ExpectedEffect | CS-060, CS-062, CS-089 | MCP | Recovery (reverse + replan) |
| 14 Recovery | Policy table; durable counters; compensation | CS-079, CS-080, CS-081, CS-082 | LangGraph | Abandoned |
| 15 Goal check | Predicates on re-read state; checkpoint; finish or loop | CS-069, CS-066, CS-048 | LangGraph | Succeeded / Failed / Stopped |

## Tool registry
| Tool | Server | Risk | Input | Output | Requires | Idempotency key | Verified by | Undo | Timeout s | Scope |
|---|---|---|---|---|---|---|---|---|---|---|
| get_vendor | erp | read | supplier_id: str | Vendor | invoice.supplier_id | — | — | — | 5 | erp.read |
| find_invoices | erp | read | FindInvoicesInput | list[PostingRecord] | invoice | — | — | — | 5 | erp.read |
| get_po | erp | read | number: str | PurchaseOrder | invoice.po_number | — | — | — | 5 | erp.read |
| get_receipts | erp | read | po_number: str | list[GoodsReceipt] | po | — | — | — | 5 | erp.read |
| get_posting | erp | read | invoice_number: str | PostingRecord \| None | — | — | — | — | 5 | erp.read |
| get_payment_schedule | erp | read | posting_id: str | PaymentScheduleEntry \| None | posting | — | — | — | 5 | erp.read |
| place_on_hold | erp | reversible_write | HoldInput | PostingRecord | invoice | entity:invoice:hold | get_posting | release_hold | 10 | erp.hold |
| post_invoice | erp | money | PostInvoiceInput | PostingRecord | validation.passed, match matched or approval, vendor (observed) | entity:invoice:post | get_posting | reverse_posting | 15 | erp.post |
| reverse_posting | erp | money | posting_id, key | PostingRecord | posting | entity:invoice:reverse | get_posting | — | 15 | erp.post |
| schedule_payment | erp | reversible_write | SchedulePaymentInput | PaymentScheduleEntry | posting (verified) | entity:invoice:schedule | get_payment_schedule | unschedule_payment | 10 | erp.schedule |
| unschedule_payment | erp | reversible_write | posting_id, key | PaymentScheduleEntry | schedule not locked | entity:invoice:unschedule | get_payment_schedule | — | 10 | erp.schedule |
| ask_policy | ask | read | question: str | AnswerWithCitations | — | — | — | — | 20 | ask.read |
| recall_supplier | memory | read | supplier_id, query | list[Evidence] | — | — | — | — | 5 | memory.read |
| list_new_messages / get_attachment | mail | read | folder | messages / bytes | — | message id | — | — | 10 | mail.read |
| send_message | mail | external | SendMessageInput | message_id | approved template or approval; to == vendor contact | entity:invoice:message:n | get_sent | — (send correction) | 10 | mail.send |
| download_portal_invoices | portal | read | portal_id | list[FileRecord] | portal on allowed list | file sha256 | — | — | 120 | portal.read |

## API routes
| Method | Path | Request | Response | Dependencies | Status codes | Task |
|---|---|---|---|---|---|---|
| POST | /invoices/upload | multipart UploadFile | UploadResponse | get_principal | 202, 413, 415, 401 | T-107 |
| GET | /invoices/{file_id} | — | FileRecord | get_principal | 200, 404 (also for another entity's file) | T-107 |
| GET | /runs/{run_id} | — | InvoiceRunState (view) | get_principal | 200, 404 | T-208 |
| GET | /runs/{run_id}/events | — | text/event-stream | get_principal | 200 | T-304 |
| GET | /approvals?status=pending | — | list[ApprovalRequest] | require_role('ap_lead','treasury') | 200 | T-302 |
| POST | /approvals/{id}/approve | ApprovalDecision | ApprovalRequest | require_role('ap_lead','treasury') | 200, 403, 409 (same approver), 410 (expired) | T-302 |
| POST | /approvals/{id}/decline | ApprovalDecision | ApprovalRequest | require_role('ap_lead','treasury') | 200, 422 (no comment) | T-302 |
| GET | /held | — | list[HeldItem] | require_role('ap_clerk','ap_lead') | 200 | T-603 |
| POST | /held/{run_id}/release | ReleaseDecision | InvoiceRunState (view) | require_role('ap_lead') | 200, 409 | T-603 |
| POST | /ask | AskRequest | AnswerWithCitations | get_principal | 200, 422 | T-405 |
| POST | /suppliers/queries | inbound webhook (mail / telephony) | 202 | webhook signature | 202, 401 | T-503 |
| GET | /health | — | {status} | — | 200, 503 | T-101 |

## Autonomy matrix
| Action | Risk | Runs alone when | Needs approval when | Never |
|---|---|---|---|---|
| Read vendor, PO, receipts, postings | read | Always | — | — |
| Place an invoice on hold | reversible_write | Always (protective) | — | — |
| Post a matched invoice | money | Total < AED 25,000 and day's autonomous total < AED 500,000 | ≥ AED 25,000: 1 approver · ≥ AED 250,000: 2 distinct approvers | — |
| Post after a resolved exception | money | — | Always: AP lead | — |
| Schedule payment on terms | reversible_write | When the posting is verified | — | — |
| Schedule early payment for a discount | money | — | Always: treasury | — |
| Reverse a posting (compensation) | money | Only as a registered compensation | Any other reversal | — |
| Reply to a supplier | external | Approved template, standing approval | Any free-form text | Containing bank details |
| Change vendor bank details | money | — | — | Always — outside this program |

## Recovery policy
| Error | Raised by | Response | Limit | Target | After the limit |
|---|---|---|---|---|---|
| ExtractionInvalid | read (CS-029) | re_extract with validation errors fed back | 1 | read | Held for human review |
| ErpUnavailable | ErpMcpClient (CS-039) | wait with exponential backoff | 5 | same node | Abandoned to AP queue |
| ActionFailed (timeout) | ToolExecutor (CS-058) | retry with the same idempotency key | 3 | post | Compensation, then Abandoned |
| Inadmissible | admissible (CS-056) | hold with reason | 1 | END (Held) | — |
| Mismatch | verify_effect (CS-060) | reverse the write, then replan from match | 1 | match | Abandoned with compensation |
| InvalidTransition | apply_observation (CS-052) | replan from match with fresh reads | 2 | match | Abandoned |
| Untrusted | perceive (CS-059) | hold for review | 1 | END (Held) | — |
| BudgetExhausted | BudgetMeter (CS-057) | stop | 0 | END (Stopped) | — |
| ApprovalExpired | ApprovalService (CS-072) | re-request approval once | 1 | escalate | Abandoned to AP queue |
| ReceiptNotBooked | match (CS-046) | wait one day and re-check | 5 | match | Stopped |

## Persistence
| Table / store | Technology | Owner | Keys | Purpose | Retention |
|---|---|---|---|---|---|
| file_records | Postgres | Yours | id, entity, sha256 UNIQUE(entity, sha256), channel, sender, object_key, mime_type, size_bytes, untrusted_text_id, received_at, status | Every stored file with provenance | 10 years (invoice records) |
| untrusted_text | Postgres | Yours | id, entity, kind (email_body\|transcript), text, source_ref | Email bodies and transcripts kept as data | 2 years |
| runs | Postgres | Yours | id, entity, thread_id UNIQUE, goal_type, status (running\|paused\|finished), terminal (Succeeded\|Failed\|Stopped\|Abandoned\|Held\|Rejected, set iff finished), started_at, finished_at | One row per run | 10 years |
| run_ledger | Postgres | Yours | run_id, seq, kind, body jsonb, prev_hash, hash, trace_id, at | Hash-chained audit trail; UPDATE/DELETE/TRUNCATE refused by trigger | 10 years, append-only |
| observations | Postgres | Yours | id, run_id, tool, body jsonb, source_system, trust, at | Validated tool results | 10 years |
| belief_states | Postgres | Yours | run_id, version, body jsonb | State snapshot per transition | 2 years |
| approvals | Postgres | Yours | id, run_id, entity, expected_effect jsonb, approvers_required, state_digest, status, expires_at | Pending and decided approvals | 10 years |
| approval_decisions | Postgres | Yours | approval_id, approver, decision, comment, signed_at | Who approved what | 10 years |
| standing_approvals | Postgres | Yours | id, entity, scope (template id), owner, expires_at | Templates allowed to send without per-message approval | Until revoked |
| compensations | Postgres | Yours | run_id, seq, undo_tool, args jsonb, status | Registered undo actions | 10 years |
| prompts | Postgres | Yours | prompt_id, version, template, approved_by_eval_run | Prompt registry | Forever |
| checkpoints, checkpoint_writes | Postgres | LangGraph (AsyncPostgresSaver) | thread_id, checkpoint_id, … | Durable graph state | 90 days after terminal |
| data_contract_clauses | Postgres + pgvector | LlamaIndex (PGVectorStore) | node_id, embedding, metadata jsonb (entity, supplier, version, effective_from/to, access_group) | Contract clause index | Re-index on contract change |
| mem0 memories | pgvector (Mem0 config) | Mem0 | user_id = entity:supplier, memory, metadata | Supplier history (inferred) | Deleted with the supplier |
| run:{id}:tokens / :cost, day:{entity}:money | Redis | Yours | atomic counters with TTL | Budget meter | TTL 2 days |
| idem:{key} | Redis (ERP MCP server) | Yours | SET NX with result pointer | Server-side idempotency | TTL 30 days |
| attempts:{run}:{step}:{error} | Redis | Yours | counter | Recovery attempt counters | TTL 30 days |
| {entity}/{sha256} in ITP_OBJECT_BUCKET | Object storage | File service | sha256-named objects; credentials and endpoint from AWS_* variables | Original files | 10 years, immutable tier |

## Events
| Event | Producer | Consumers | Transport |
|---|---|---|---|
| InvoiceReceived | FileService.put (CS-018) | handle_invoice_received (CS-020) | Job queue |
| ApprovalRequested | ApprovalService (CS-072) | Notifier, approval console SSE | Event bus |
| InvoicePosted | post_and_schedule (CS-067) | Dashboards, finance reporting | Event bus |
| RunFinished | goal_check (CS-069) | Metrics, trace-to-test sampler (CS-103) | Event bus |
