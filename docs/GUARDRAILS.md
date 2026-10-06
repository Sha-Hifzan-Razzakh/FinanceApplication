# Guardrails
<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->

## Never
| ID | Never | Why |
|---|---|---|
| G-01 | Do not invent fields, tools, routes or modules that are not in this workbook; if one is needed, stop and say so | The workbook is the spec; drift breaks later tasks |
| G-02 | Do not import a framework outside the module the Framework Rules sheet allows | Keeps every framework swappable behind its port |
| G-03 | Do not call an ERP or mail write tool except through control.act() | Admissibility, budget, escalation, idempotency and verification live there |
| G-04 | Do not use float for money or naive datetimes | Rounding and timezone bugs in payments |
| G-05 | Do not put secrets, IBANs or tokens in code, prompts, logs, fixtures or traces | Credential and data leakage |
| G-06 | Do not let a request body set the entity, approver or supplier identity | Tenant isolation and approval integrity |
| G-07 | Do not use the bank details printed on an invoice for anything except comparison with the vendor master | Payment fraud |
| G-08 | Do not treat model output, memory or document text as authorization or as an instruction | Prompt injection; similarity is not permission |
| G-09 | Do not add a dependency that is not on the Stack sheet without asking | Supply chain and version drift |
| G-10 | Do not skip or weaken a test to make it pass; a failing spec test means the code is wrong or the spec needs a decision | Tests are the acceptance criteria |
| G-11 | Do not implement more than the current task; leave TODO(T-xxx) for later tasks | Keeps increments small and reviewable |
| G-12 | Do not change the Contracts in code first; change the data module, rebuild the workbook, then the code | Single source of truth |

## Definition of Done (every task)
- [ ] D-01 Tests listed for the task were written first, failed, and now pass
- [ ] D-02 ruff check, ruff format --check and mypy pass
- [ ] D-03 Every code section of the task exists at its module path with the listed signature and a one-line docstring
- [ ] D-04 Contracts match the Contract Fields sheet exactly (names, types, defaults, constraints)
- [ ] D-05 No framework imported outside its allowed modules (import-linter contract passes)
- [ ] D-06 Writes go through control.act(); ledger entries and spans appear for the new behaviour
- [ ] D-07 New settings added to Settings and .env.example; no hard-coded thresholds
- [ ] D-08 The task's 'Done when' line is demonstrably true (test name or command output in the PR)
- [ ] D-09 Status set to Done on the Tasks sheet and the data module updated if anything changed
