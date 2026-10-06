# Docs map
<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->

**Source** is the spec. **Generated** files are rebuilt by `make docs` and never hand-edited. **Living** files are the build's memory;
rebuilds never overwrite them. A session pays only for CLAUDE.md + HANDOFF.md + a 3-line progress summary + the current task spec.

| File | Kind | Read when | Updated when |
|---|---|---|---|
| CLAUDE.md | generated | Auto-loaded every session (~500 tokens) | Spec rebuild |
| docs/HANDOFF.md | living | Auto-loaded every session (imported by CLAUDE.md) | Rewritten at session end (keep under 200 words) |
| docs/PROGRESS.md | living | Never read whole; use scripts/progress.py | Only through scripts/progress.py |
| tasks/T-xxx.md | generated | For the tasks of the current group only | Spec rebuild |
| docs/PLAN.md | generated | Rarely: progress.py already prints the next group | Spec rebuild |
| docs/OPEN_QUESTIONS.md | living | When blocked | /ask-question |
| docs/DECISIONS.md | living | Before a design choice | /record-decision |
| docs/SESSION_LOG.md | living | Rarely (history) | Session end: append 3 lines |
| docs/DEBT.md | living | Before closing an increment | When a TODO(T-xxx) is added or cleared |
| docs/CHANGELOG.md | living | Reviewing what shipped | Merge: one line |
| docs/SPEC_CHANGES.md | living | Before make docs | When the spec changes |
| docs/archive/INC-n.md | living | Only for history | progress.py archive INC-n |
| docs/CONVENTIONS.md | generated | On demand, by grep | Spec rebuild |
| docs/GUARDRAILS.md | generated | On demand, by grep | Spec rebuild |
| docs/ARCHITECTURE.md | generated | On demand, grep a section; never whole | Spec rebuild |
| docs/CONTRACTS.md | generated | On demand, grep a model; never whole | Spec rebuild |
| docs/FRAMEWORKS.md | generated | On demand, grep a framework | Spec rebuild |
| docs/TESTING.md | generated | On demand | Spec rebuild |
| docs/ENVIRONMENT.md | generated | Setup and debugging | Spec rebuild |
| docs/GLOSSARY.md | generated | When a term is unclear | Spec rebuild |
| docs/README.md | generated | First time in the repo | Spec rebuild |
| scripts/progress.py | generated | Run, never read | Spec rebuild |
| .claude/settings.json | generated | Claude Code start | Spec rebuild |
| .claude/commands/*.md | generated | Typed as slash commands | Spec rebuild |
| spec/itp_data.py + builders | source | Changing the spec | Spec change |
