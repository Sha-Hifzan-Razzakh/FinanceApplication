---
description: Record a question the spec does not answer instead of guessing
---
Question: $ARGUMENTS

1. Append a row to docs/OPEN_QUESTIONS.md with `cat >>` (next id: `grep -c '^| Q-' docs/OPEN_QUESTIONS.md` + 1).
2. If it blocks the current task: `python3 scripts/progress.py block <id> --note "Q-NNN"`, then continue with an unblocked task in the group.
