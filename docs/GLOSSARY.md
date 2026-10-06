# Glossary
<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->

| Term | Meaning |
|---|---|
| Entity | A Meridian legal entity (meridian-supply, meridian-projects); every query and file is scoped to one |
| Run | One execution of the control loop for one goal, e.g. settling one invoice |
| Control | One of the 15 states of the agent control model (Intent … Goal check) |
| Control capability | A guarantee such as Idempotent actions or Human approval, delivered by controls |
| Fact source | observed (system of record), extracted (document), inferred (model or memory), assumed |
| Risk class | read, reversible_write, irreversible_write, external, money — decides admissibility and approval |
| ExpectedEffect | What a write should change, recorded before the call and diffed after |
| Standing approval | A pre-approved scope (e.g. a mail template) that lets an action run without per-item approval |
| Held | Terminal state for runs a person must review: untrusted instruction, bank mismatch, failed extraction |
| Variance | A difference between invoice, PO and receipts: quantity, price, missing PO, unmatched line |
| Three-way match | Invoice vs purchase order vs goods receipt |
| Port / adapter | A Protocol the app depends on / the one module that implements it with a framework |
