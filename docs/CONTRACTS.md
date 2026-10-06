# Contracts
<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->

Implement exactly as written. Changes start in spec/itp_data.py.

| ID | Model | Module | Kind | Defined in |
|---|---|---|---|---|
| M-01 | Quote | `contracts/common.py` | Value object | T-103 |
| M-02 | Fact[T] | `contracts/common.py` | Value object (generic) | T-103 |
| M-03 | Principal | `contracts/common.py` | Value object | T-102 |
| M-04 | FileRecord | `contracts/intake.py` | Persistence record | T-106 |
| M-05 | UploadResponse | `contracts/intake.py` | API response | T-107 |
| M-59 | UploadMeta | `contracts/intake.py` | Service input | T-106 |
| M-06 | InvoiceLine | `contracts/invoice.py` | Document value | T-112 |
| M-07 | InvoiceDraft | `contracts/invoice.py` | LLM output schema | T-111 |
| M-08 | Invoice | `contracts/invoice.py` | Domain document | T-112 |
| M-09 | DocumentClassification | `contracts/decisions.py` | Decision schema (Jev) | T-109 |
| M-10 | Vendor | `contracts/erp.py` | Tool output (ERP mirror) | T-201 |
| M-11 | PurchaseOrderLine | `contracts/erp.py` | Tool output (ERP mirror) | T-201 |
| M-12 | PurchaseOrder | `contracts/erp.py` | Tool output (ERP mirror) | T-201 |
| M-13 | GoodsReceiptLine | `contracts/erp.py` | Tool output (ERP mirror) | T-201 |
| M-14 | GoodsReceipt | `contracts/erp.py` | Tool output (ERP mirror) | T-201 |
| M-15 | PostingRecord | `contracts/erp.py` | Tool output (ERP mirror) | T-212 |
| M-16 | PaymentScheduleEntry | `contracts/erp.py` | Tool output (ERP mirror) | T-212 |
| M-17 | FindInvoicesInput | `contracts/erp.py` | Tool input | T-201 |
| M-18 | RuleOutcome | `contracts/validation.py` | Domain value | T-203 |
| M-19 | ValidationResult | `contracts/validation.py` | Domain value | T-203 |
| M-20 | DuplicateScores | `contracts/decisions.py` | Decision schema (Jev) | T-204 |
| M-21 | Tolerance | `contracts/matching.py` | Configuration value | T-206 |
| M-22 | LineMapping | `contracts/decisions.py` | Decision schema (Jev) | T-205 |
| M-23 | QuantityVariance | `contracts/matching.py` | Variance (union member) | T-206 |
| M-24 | PriceVariance | `contracts/matching.py` | Variance (union member) | T-206 |
| M-25 | MissingPO | `contracts/matching.py` | Variance (union member) | T-206 |
| M-26 | UnmatchedLine | `contracts/matching.py` | Variance (union member) | T-206 |
| M-27 | MatchResult | `contracts/matching.py` | Domain value | T-206 |
| M-28 | Evidence | `contracts/resolution.py` | Domain value | T-305 |
| M-29 | ExpectedEffect | `contracts/posting.py` | Control record | T-211 |
| M-30 | ResolutionProposal | `contracts/resolution.py` | LLM output schema | T-305 |
| M-31 | AskRequest | `contracts/answers.py` | API request | T-405 |
| M-32 | Citation | `contracts/answers.py` | Domain value | T-403 |
| M-33 | Claim | `contracts/answers.py` | LLM output schema | T-404 |
| M-34 | AnswerWithCitations | `contracts/answers.py` | API response / LLM output | T-403 |
| M-35 | ScopeDecision | `contracts/decisions.py` | Decision schema (Jev) | T-403 |
| M-36 | PostInvoiceInput | `contracts/posting.py` | Tool input | T-212 |
| M-37 | SchedulePaymentInput | `contracts/posting.py` | Tool input | T-212 |
| M-38 | HoldInput | `contracts/posting.py` | Tool input | T-212 |
| M-39 | SupplierQuery | `contracts/supplier.py` | Domain value | T-503 |
| M-40 | QueryClassification | `contracts/decisions.py` | Decision schema (Jev) | T-504 |
| M-41 | SupplierReply | `contracts/supplier.py` | LLM output schema | T-505 |
| M-42 | SendMessageInput | `contracts/supplier.py` | Tool input | T-505 |
| M-43 | Scope | `contracts/run.py` | Value object | T-207 |
| M-44 | GoalSpec | `contracts/run.py` | Control record | T-207 |
| M-45 | RunLimits | `contracts/run.py` | Control record | T-207 |
| M-46 | InvoiceRunState | `agents/state.py` | Graph state | T-209 |
| M-47 | ToolEnvelope[I] | `contracts/run.py` | Tool-call envelope | T-210 |
| M-48 | Observation | `contracts/run.py` | Control record | T-211 |
| M-49 | ToolSpec | `control/registry.py` | Registry record | T-210 |
| M-50 | ApprovalRequest | `contracts/approvals.py` | Control record | T-302 |
| M-51 | ApprovalDecision | `contracts/approvals.py` | API request | T-302 |
| M-52 | LedgerEntry | `contracts/run.py` | Control record | T-104 |
| M-53 | RecoveryRule | `control/recovery.py` | Configuration value | T-306 |
| M-54 | InvoiceReceived | `contracts/events.py` | Event | T-106 |
| M-55 | ApprovalRequested | `contracts/events.py` | Event | T-302 |
| M-56 | InvoicePosted | `contracts/events.py` | Event | T-214 |
| M-57 | RunFinished | `contracts/events.py` | Event | T-208 |
| M-58 | Settings | `config/settings.py` | Settings | T-101 |

## `contracts/common.py`
```python
# contracts/common.py
class Quote(BaseModel):
    """Where a value was read from in a document."""
    model_config = ConfigDict(frozen=True)
    page: int  # ge=1; Page number in the source file
    text: str  # max_length=300; Verbatim text the value came from
    bbox: tuple[float,float,float,float] | None = None  # Box on the page, when the parser gives one

# contracts/common.py
class Fact(BaseModel, Generic[T]):
    """A belief with its provenance; every run-state fact is one."""
    model_config = ConfigDict(frozen=True)
    value: T  # The value itself
    source: Literal['observed','extracted','inferred','assumed']  # observed = system of record; extracted = document; inferred = model/memory
    observation_id: UUID | None = None  # required if observed; Observation row backing the fact
    observed_at: datetime  # tz-aware; When it was read
    quote: Quote | None = None  # Document quote for extracted facts
    # invariant: observation_id required when source='observed'

# contracts/common.py
class Principal(BaseModel):
    """Who is acting: user or agent, entity, roles, scopes."""
    model_config = ConfigDict(frozen=True)
    subject: str  # User id or agent principal id
    kind: Literal['user','agent']  # Who is acting
    entity: Literal['meridian-supply','meridian-projects']  # Legal entity; every query is filtered by it
    roles: list[str] = []  # e.g. ap_clerk, ap_lead, treasury
    scopes: list[str] = []  # Tool scopes, e.g. erp.read, erp.post
```

## `contracts/intake.py`
```python
# contracts/intake.py
class FileRecord(BaseModel):
    """One stored file with its provenance."""
    model_config = ConfigDict(extra='forbid')
    id: UUID
    entity: EntityId
    sha256: str  # pattern ^[a-f0-9]{64}$; Dedupe key
    channel: Literal['email','portal','scan']  # Where it came from
    sender: str | None = None  # Email sender or portal name
    object_key: str  # starts with entity/; Key in object storage
    mime_type: Literal['application/pdf','image/png','image/jpeg','image/tiff']
    size_bytes: int  # gt=0, le=MAX_UPLOAD_BYTES (20_000_000)
    untrusted_text_id: UUID | None = None  # Email body / transcript stored as untrusted text
    received_at: datetime
    status: Literal['stored','processing','done','held','rejected'] = 'stored'
    # invariant: sha256 is 64 lowercase hex

# contracts/intake.py
class UploadResponse(BaseModel):
    """Result of POST /invoices/upload."""
    file_id: UUID
    run_id: UUID | None = None  # Set when a run started
    duplicate: bool = False  # True if the hash was already stored

# contracts/intake.py
class UploadMeta(BaseModel):
    """What the caller knows about an incoming file; the entity comes from the Principal."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    channel: Literal['email','portal','scan']  # Where it came from
    sender: str | None = None  # Email sender or portal name
    untrusted_text_id: UUID | None = None  # Email body / transcript stored as untrusted text
```

## `contracts/invoice.py`
```python
# contracts/invoice.py
class InvoiceLine(BaseModel):
    """One invoice line with its source quote."""
    model_config = ConfigDict(extra='forbid')
    description: str  # max_length=300; Line text as printed
    sku: str | None = None  # Filled by line mapping
    quantity: Decimal  # gt=0
    unit_price: Decimal  # ge=0, decimal_places≤4
    amount: Decimal  # ge=0; Line net amount
    vat_rate: Decimal = Decimal('0.05')  # ge=0, le=1; UAE standard 5%
    source: Quote  # Where this line was read
    # invariant: amount == quantity × unit_price (±0.01)

# contracts/invoice.py
class InvoiceDraft(BaseModel):
    """What the model fills; loose, quoted, not yet trusted."""
    model_config = ConfigDict(extra='forbid')
    supplier_name: str | None = None
    supplier_trn: str | None = None  # Tax registration number
    number: str | None = None
    issued_on: date | None = None
    due_on: date | None = None
    currency: str | None = None
    po_number: str | None = None
    lines: list[InvoiceLine] = []
    subtotal: Decimal | None = None
    vat: Decimal | None = None
    total: Decimal | None = None
    printed_iban: str | None = None  # Never used to pay
    field_quotes: dict[str, Quote] = {}  # Quote per filled field
    # invariant: every non-null field has an entry in field_quotes

# contracts/invoice.py
class Invoice(BaseModel):
    """The validated invoice the run works on."""
    model_config = ConfigDict(extra='forbid', frozen=True)
    entity: EntityId
    file_id: UUID
    supplier_id: str  # Resolved against vendor master
    number: str  # min_length=1
    issued_on: date
    due_on: date | None = None  # ≥ issued_on
    currency: Literal['AED','USD','EUR']
    po_number: str | None = None
    lines: list[InvoiceLine]  # min_length=1
    subtotal: Decimal  # ge=0
    vat: Decimal  # ge=0
    total: Decimal  # gt=0
    printed_iban: str | None = None  # Compared with master only
    # invariant: adds_up: Σlines = subtotal; subtotal + vat = total; due_on ≥ issued_on
```

## `contracts/decisions.py`
```python
# contracts/decisions.py
class DocumentClassification(BaseModel):
    """Document type and readability, typed."""
    doc_type: Literal['invoice','credit_note','statement','reminder','other']  # Jev choice
    doc_type_p: float  # 0–1; Probability of the chosen type
    readable_p: float  # 0–1; Probability the document is legible
    # invariant: probabilities in [0,1]

# contracts/decisions.py
class DuplicateScores(BaseModel):
    """Near-duplicate and lookalike-supplier probabilities."""
    near_duplicate_p: float  # 0–1
    lookalike_supplier_p: float  # 0–1
    # invariant: probabilities in [0,1]

# contracts/decisions.py
class LineMapping(BaseModel):
    """Invoice line → PO SKU with probability."""
    line_index: int  # ge=0
    sku: str | None  # None below threshold
    p: float  # 0–1
    # invariant: sku None when p below threshold

# contracts/decisions.py
class ScopeDecision(BaseModel):
    """Is the question about AP policy or contracts?."""
    in_scope_p: float  # 0–1
    topic: Literal['payment_terms','tolerance','vat','credit_notes','other']
    # invariant: probabilities in [0,1]

# contracts/decisions.py
class QueryClassification(BaseModel):
    """Type of supplier query and embedded-instruction score."""
    query_type: Literal['status','dispute','bank_change','other']
    query_type_p: float  # 0–1
    instruction_p: float  # 0–1; Embedded-instruction score
```

## `contracts/erp.py`
```python
# contracts/erp.py
class Vendor(BaseModel):
    """Vendor master record."""
    model_config = ConfigDict(frozen=True)
    supplier_id: str
    name: str
    trn: str  # 15 digits
    iban: str  # Master bank account
    status: Literal['active','blocked']
    payment_terms_days: int  # ge=0; e.g. 45
    category: str  # Selects the tolerance row
    contact_email: EmailStr  # Only address replies may go to
    contact_phone: str  # Used to identify voicemail callers
    # invariant: iban normalised (no spaces, upper)

# contracts/erp.py
class PurchaseOrderLine(BaseModel):
    """One ordered item."""
    model_config = ConfigDict(frozen=True)
    sku: str
    description: str
    quantity: Decimal  # gt=0
    unit_price: Decimal  # ge=0

# contracts/erp.py
class PurchaseOrder(BaseModel):
    """Purchase order with version for consistency."""
    model_config = ConfigDict(frozen=True)
    number: str
    entity: EntityId
    supplier_id: str
    status: Literal['open','closed','cancelled']  # cancelled ⇒ run fails
    currency: str
    lines: list[PurchaseOrderLine]  # min_length=1
    version: int  # ge=1; For revalidation after approval
    # invariant: line_for(sku) raises if absent

# contracts/erp.py
class GoodsReceiptLine(BaseModel):
    """Received quantity of one item."""
    model_config = ConfigDict(frozen=True)
    sku: str
    quantity: Decimal  # ge=0

# contracts/erp.py
class GoodsReceipt(BaseModel):
    """Goods receipt against a PO."""
    model_config = ConfigDict(frozen=True)
    id: str
    po_number: str
    received_on: date
    lines: list[GoodsReceiptLine]
    version: int  # ge=1
    # invariant: qty_for(sku) returns 0 if absent

# contracts/erp.py
class PostingRecord(BaseModel):
    """An AP posting as the ERP holds it."""
    model_config = ConfigDict(frozen=True)
    posting_id: str
    invoice_number: str
    supplier_id: str
    amount_payable: Decimal
    amount_blocked: Decimal = Decimal(0)
    gl_account: str
    due_on: date
    status: Literal['posted','reversed']
    idempotency_key: str  # Key the posting was created with

# contracts/erp.py
class PaymentScheduleEntry(BaseModel):
    """A scheduled payment line."""
    model_config = ConfigDict(frozen=True)
    posting_id: str
    run_date: date
    amount: Decimal
    status: Literal['scheduled','locked','paid','unscheduled']  # locked ⇒ no longer reversible

# contracts/erp.py
class FindInvoicesInput(BaseModel):
    """Query for possible duplicates."""
    model_config = ConfigDict(extra='forbid')
    supplier_id: str
    amount: Decimal
    around: date
    window_days: int = 30  # le=120
    # invariant: window_days ≤ 120
```

## `contracts/validation.py`
```python
# contracts/validation.py
class RuleOutcome(BaseModel):
    """Result of one validation rule with evidence."""
    model_config = ConfigDict(frozen=True)
    rule: Literal['vendor_active','iban_matches_master','trn_valid','entity_matches','not_duplicate']
    passed: bool
    evidence: str  # max_length=300; Human-readable reason
    observation_ids: list[UUID] = []

# contracts/validation.py
class ValidationResult(BaseModel):
    """All rule outcomes and the hold reason, if any."""
    model_config = ConfigDict(frozen=True)
    invoice_number: str
    outcomes: list[RuleOutcome]
    hold_reason: Literal['bank_mismatch','vendor_blocked','lookalike_supplier'] | None = None  # Sends the run to Held
    reject_reason: Literal['duplicate','not_invoice'] | None = None  # Sends the run to Rejected
    # invariant: passed is computed: all outcomes passed
```

## `contracts/matching.py`
```python
# contracts/matching.py
class Tolerance(BaseModel):
    """Price and quantity tolerances per supplier category."""
    model_config = ConfigDict(frozen=True)
    category: str
    price_pct: Decimal = Decimal('0.01')  # ge=0; 1%
    price_abs: Decimal = Decimal('50')  # ge=0; AED 50
    qty_exact: bool = True  # Exact for stock items
    # invariant: price_ok(inv, po) method

# contracts/matching.py
class QuantityVariance(BaseModel):
    """Invoiced quantity differs from received."""
    model_config = ConfigDict(frozen=True)
    kind: Literal['quantity'] = 'quantity'  # Discriminator
    line: int
    invoiced: Decimal
    received: Decimal
    # invariant: kind='quantity'

# contracts/matching.py
class PriceVariance(BaseModel):
    """Invoiced price outside tolerance of PO price."""
    model_config = ConfigDict(frozen=True)
    kind: Literal['price'] = 'price'  # Discriminator
    line: int
    invoiced: Decimal
    ordered: Decimal
    # invariant: kind='price'

# contracts/matching.py
class MissingPO(BaseModel):
    """Invoice has no or unknown PO number."""
    model_config = ConfigDict(frozen=True)
    kind: Literal['missing_po'] = 'missing_po'  # Discriminator
    po_number: str | None = None
    # invariant: kind='missing_po'

# contracts/matching.py
class UnmatchedLine(BaseModel):
    """Invoice line could not be mapped to a PO item."""
    model_config = ConfigDict(frozen=True)
    kind: Literal['unmatched_line'] = 'unmatched_line'  # Discriminator
    line: int
    # invariant: kind='unmatched_line'

# contracts/matching.py
class MatchResult(BaseModel):
    """Outcome of the three-way match."""
    model_config = ConfigDict(frozen=True)
    status: Literal['matched','variances','wait']  # wait = receipt not booked yet
    variances: list[Annotated[Variance, Field(discriminator='kind')]] = []
    po_version: int | None = None
    receipt_versions: list[int] = []
    # invariant: status='matched' iff variances empty (except 'wait')
```

## `contracts/resolution.py`
```python
# contracts/resolution.py
class Evidence(BaseModel):
    """One piece of evidence a proposal may cite."""
    model_config = ConfigDict(frozen=True)
    id: str  # e.g. clause:GS-2026:7.2
    kind: Literal['clause','receipt','po','observation','memory']
    ref: str  # Pointer to the source
    summary: str  # max_length=300
    admissible_for_money: bool  # False for memory
    # invariant: kind='memory' ⇒ admissible_for_money=False

# contracts/resolution.py
class ResolutionProposal(BaseModel):
    """Proposed resolution for one variance."""
    model_config = ConfigDict(extra='forbid')
    variance_index: int
    action: Literal['pay_received_request_credit','accept_price_per_clause','hold_for_po','reject_invoice']
    pay_amount: Decimal  # ge=0; Incl. VAT
    block_amount: Decimal  # ge=0
    credit_note_amount: Decimal | None = None
    rationale: str  # max_length=600
    evidence_ids: list[str]  # min_length=1
    expected_effect: ExpectedEffect
    reviewers_agree: bool  # Analyst and auditor agree
    # invariant: pay_amount + block_amount = invoice total; ≥1 evidence id
```

## `contracts/posting.py`
```python
# contracts/posting.py
class ExpectedEffect(BaseModel):
    """What a write should change; written before the call, diffed after."""
    model_config = ConfigDict(frozen=True)
    target: Literal['posting','schedule','hold','message','reversal']
    invoice_number: str
    amount_payable: Decimal | None = None
    amount_blocked: Decimal | None = None
    gl_account: str | None = None
    due_on: date | None = None
    run_date: date | None = None
    idempotency_key: str

# contracts/posting.py
class PostInvoiceInput(BaseModel):
    """Arguments to post_invoice."""
    model_config = ConfigDict(extra='forbid')
    entity: EntityId
    invoice_number: str
    supplier_id: str
    amount_payable: Decimal  # ge=0
    amount_blocked: Decimal = Decimal(0)  # ge=0
    gl_account: str
    due_on: date
    dry_run: bool = False
    idempotency_key: str  # pattern entity:invoice:post
    # invariant: amount_payable + amount_blocked = invoice total

# contracts/posting.py
class SchedulePaymentInput(BaseModel):
    """Arguments to schedule_payment."""
    model_config = ConfigDict(extra='forbid')
    posting_id: str
    run_date: date  # Monday
    idempotency_key: str
    # invariant: run_date is a Monday

# contracts/posting.py
class HoldInput(BaseModel):
    """Arguments to place_on_hold."""
    model_config = ConfigDict(extra='forbid')
    invoice_number: str
    reason: str  # max_length=200
    idempotency_key: str
```

## `contracts/answers.py`
```python
# contracts/answers.py
class AskRequest(BaseModel):
    """A clerk's question; entity comes from the token, not the body."""
    model_config = ConfigDict(extra='forbid')
    question: str  # 3–500 chars
    supplier_id: str | None = None  # Narrows retrieval to one supplier's contracts
    # invariant: question stripped, 3–500 chars

# contracts/answers.py
class Citation(BaseModel):
    """A clause an answer cites."""
    model_config = ConfigDict(frozen=True)
    clause_id: str
    contract_id: str
    version: str
    effective_from: date
    page: int  # ge=1

# contracts/answers.py
class Claim(BaseModel):
    """One factual claim and the clauses supporting it."""
    text: str  # max_length=400
    citation_ids: list[str]  # min_length=1
    supported: bool | None = None  # Set by the verifier
    # invariant: citation_ids min length 1

# contracts/answers.py
class AnswerWithCitations(BaseModel):
    """Answer, claims, citations and status."""
    status: Literal['answered','no_evidence','out_of_scope']
    answer: str | None = None
    claims: list[Claim] = []
    citations: list[Citation] = []
    # invariant: status='answered' ⇒ all claims supported
```

## `contracts/supplier.py`
```python
# contracts/supplier.py
class SupplierQuery(BaseModel):
    """An inbound supplier question; text stored untrusted."""
    model_config = ConfigDict(frozen=True)
    id: UUID
    channel: Literal['email','voicemail']
    supplier_id: str  # From sender address / caller number
    text_id: UUID  # Untrusted text row
    received_at: datetime
    # invariant: supplier_id resolved from sender/caller, never from text

# contracts/supplier.py
class SupplierReply(BaseModel):
    """Reply drafted into an approved template."""
    model_config = ConfigDict(extra='forbid')
    template_id: str  # From the template registry
    supplier_id: str
    invoice_numbers: list[str]  # Must belong to supplier_id
    variables: dict[str,str] = {}
    free_text: str | None = None  # Needs approval when present
    # invariant: free_text None unless approval required; no IBAN pattern

# contracts/supplier.py
class SendMessageInput(BaseModel):
    """Arguments to send_message."""
    model_config = ConfigDict(extra='forbid')
    to: EmailStr  # Vendor contact only
    subject: str  # max_length=150
    body: str  # max_length=4000
    idempotency_key: str
    # invariant: to must equal vendor contact_email
```

## `contracts/run.py`
```python
# contracts/run.py
class Scope(BaseModel):
    """What a run may touch, and what it must not."""
    model_config = ConfigDict(frozen=True)
    supplier_id: str
    invoice_file_id: UUID | None = None
    invoice_number: str | None = None
    po_number: str | None = None
    must_not_touch: list[str] = ['vendor_master','other_suppliers','locked_payment_runs']

# contracts/run.py
class GoalSpec(BaseModel):
    """The run's compiled goal."""
    model_config = ConfigDict(extra='forbid', frozen=True)
    goal_type: Literal['ap.settle_invoice','ap.answer_question','ap.reply_supplier']
    entity: EntityId
    scope: Scope
    constraints: list[str] = []  # Merged from entity policy
    autonomy: Literal['suggest','approve','act'] = 'approve'
    # invariant: goal_type registered for the agent

# contracts/run.py
class RunLimits(BaseModel):
    """Stop conditions."""
    model_config = ConfigDict(frozen=True)
    max_steps: int = 25  # ge=1
    max_wait_days: int = 5  # Waiting for receipts
    max_tokens: int = 60_000
    max_cost_usd: Decimal = Decimal('0.50')
    max_money_moved_aed: Decimal | None = None  # Per run ceiling; daily cap in settings

# contracts/run.py
class ToolEnvelope(BaseModel, Generic[I]):
    """Tool input plus mandatory justification and sub-goal."""
    model_config = ConfigDict(extra='forbid')
    input: I  # The tool's own input model
    justification: str  # 10–300 chars; Why this call, linked to the sub-goal
    sub_goal_id: str
    # invariant: justification 10–300 chars

# contracts/run.py
class Observation(BaseModel):
    """A validated tool result with provenance."""
    model_config = ConfigDict(frozen=True)
    id: UUID
    run_id: UUID
    tool: str
    body: dict  # Validated output model dump
    source_system: Literal['erp','mail','portal','document','memory']
    trust: Literal['trusted','untrusted']
    at: datetime

# contracts/run.py
class LedgerEntry(BaseModel):
    """One hash-chained ledger row."""
    model_config = ConfigDict(frozen=True)
    run_id: UUID
    seq: int  # ge=1
    kind: str  # e.g. decision, action, observation, approval
    body: dict[str, Any]  # JSON values only
    prev_hash: str | None
    hash: str  # sha256(prev_hash + canonical JSON of run_id, seq, kind, body, trace_id, at)
    trace_id: str
    at: datetime
```

## `agents/state.py`
```python
# agents/state.py
class InvoiceRunState(BaseModel):
    """LangGraph state for one invoice run."""
    run_id: UUID
    goal: GoalSpec
    version: int = 0  # Belief version
    file: FileRecord
    classification: DocumentClassification | None = None
    invoice: Fact[Invoice] | None = None
    vendor: Fact[Vendor] | None = None
    validation: ValidationResult | None = None
    po: Fact[PurchaseOrder] | None = None
    receipts: list[Fact[GoodsReceipt]] = []
    match: MatchResult | None = None
    proposals: Annotated[list[ResolutionProposal], operator.add] = []  # reducer: add; Merged from Send branches
    approval: ApprovalDecision | None = None
    posting: Fact[PostingRecord] | None = None
    schedule: Fact[PaymentScheduleEntry] | None = None
    messages_sent: list[str] = []
    steps: int = 0
    terminal: Literal['succeeded','rejected','held','stopped','failed','abandoned'] | None = None
    # invariant: version increments on every reducer apply
```

## `control/registry.py`
```python
# control/registry.py
class ToolSpec(BaseModel):
    """One tool's governance metadata."""
    model_config = ConfigDict(frozen=True)
    name: str
    server: Literal['erp','mail','portal','ask','memory']
    risk: Literal['read','reversible_write','irreversible_write','external','money']
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    requires: list[str] = []  # Facts that must be present and fresh
    guard: Callable[[InvoiceRunState], bool] | None = None  # Extra precondition
    timeout_s: float = 10.0
    cost_usd: Decimal = Decimal(0)
    supports_dry_run: bool = False
    verify_with: str | None = None  # Re-read tool
    undo: str | None = None  # Compensation tool
    scope: str  # Vault scope, e.g. erp.post
    # invariant: irreversible ⇒ undo and supports_dry_run required
```

## `contracts/approvals.py`
```python
# contracts/approvals.py
class ApprovalRequest(BaseModel):
    """A paused proposal waiting for approval."""
    id: UUID
    run_id: UUID
    entity: EntityId
    proposals: list[ResolutionProposal] = []
    expected_effect: ExpectedEffect
    approvers_required: Literal[1,2]
    state_digest: str  # For revalidation
    expires_at: datetime  # 24 h default
    status: Literal['pending','approved','declined','expired'] = 'pending'
    # invariant: approvers_required in {1,2}

# contracts/approvals.py
class ApprovalDecision(BaseModel):
    """A signed approve/decline."""
    model_config = ConfigDict(extra='forbid')
    approval_id: UUID
    decision: Literal['approve','decline']
    approver: str  # Filled from the token, not the body
    comment: str | None = None  # required on decline
    signed_at: datetime
    # invariant: approver taken from token; comment required on decline
```

## `control/recovery.py`
```python
# control/recovery.py
class RecoveryRule(BaseModel):
    """Error type → response, limit, target."""
    model_config = ConfigDict(frozen=True)
    error: str  # Typed error class name
    response: Literal['retry','wait','re_extract','replan','hold','stop','abandon']
    limit: int
    target: str  # Node to route to
```

## `contracts/events.py`
```python
# contracts/events.py
class InvoiceReceived(BaseModel):
    """A new file is stored and ready for a run."""
    model_config = ConfigDict(frozen=True)
    event_id: UUID
    entity: EntityId
    file_id: UUID
    sha256: str
    channel: str
    occurred_at: datetime

# contracts/events.py
class ApprovalRequested(BaseModel):
    """A run paused for approval."""
    model_config = ConfigDict(frozen=True)
    event_id: UUID
    approval_id: UUID
    run_id: UUID
    approvers_required: int
    occurred_at: datetime

# contracts/events.py
class InvoicePosted(BaseModel):
    """A posting was verified."""
    model_config = ConfigDict(frozen=True)
    event_id: UUID
    run_id: UUID
    posting_id: str
    amount_payable: Decimal
    occurred_at: datetime

# contracts/events.py
class RunFinished(BaseModel):
    """A run reached a terminal state."""
    model_config = ConfigDict(frozen=True)
    event_id: UUID
    run_id: UUID
    terminal: str
    steps: int
    cost_usd: Decimal
    occurred_at: datetime
```

## `config/settings.py`
```python
# config/settings.py
class Settings(BaseSettings):
    """Typed configuration from env and vault."""
    model_config = SettingsConfigDict(env_prefix='ITP_', extra='forbid')
    database_url: PostgresDsn
    redis_url: RedisDsn
    object_bucket: str
    vault_url: HttpUrl
    erp_mcp_url: HttpUrl
    mail_mcp_url: HttpUrl
    llm_extract_model: str  # Pinned id
    llm_reason_model: str  # Pinned id
    jev_model: str  # not 'jev-latest'; Pinned version
    embedding_model: str  # Pinned; stored with every vector
    post_alone_max_aed: Decimal = Decimal('25000')  # gt=0
    two_approver_min_aed: Decimal = Decimal('250000')  # gt=0
    daily_autonomous_cap_aed: Decimal = Decimal('500000')  # gt=0
    doc_type_threshold: float = 0.9
    line_map_threshold: float = 0.9
    near_duplicate_threshold: float = 0.7
    approval_ttl_hours: int = 24
    otel_endpoint: HttpUrl | None = None
    auth_issuer: str  # Expected iss claim of bearer tokens
    auth_audience: str  # Expected aud claim of bearer tokens
    auth_public_key: str  # PEM; \n escapes accepted; Public key that verifies RS256 tokens
    agent_subject: str = 'agent:invoice-to-pay'  # Principal subject the agent runs as
    # invariant: thresholds positive; two_approver_min > post_alone_max
```
