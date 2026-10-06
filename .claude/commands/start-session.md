---
description: Begin a session from repo state, cheaply
---
docs/HANDOFF.md is already in context. Do not read PROGRESS.md, PLAN.md, CONTRACTS.md or ARCHITECTURE.md whole.

1. Run `python3 scripts/progress.py summary` and `git status -sb`.
2. If a group is current, read tasks/<id>.md only for its first open task. If none is current, run /next-group.
3. If the group's model differs from the one you are running on, say so first.
4. Reply in at most 5 lines (group, task, next step, blockers), then start working.
