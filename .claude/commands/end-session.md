---
description: Record the session so the next one continues from the repo alone
---
Run before stopping, finished or not. Do not read PROGRESS.md or SESSION_LOG.md.

1. Run the checks the open task needs; note the results.
2. Finished tasks: `python3 scripts/progress.py done <id> --evidence "..." --tests "..."`. Stuck: `python3 scripts/progress.py block <id> --note "Q-NNN ..."`.
3. Each new TODO(T-xxx) in code: append a row to docs/DEBT.md with `cat >>`.
4. `python3 scripts/progress.py log --done "<one line>" --next "<one line>"`.
5. Overwrite docs/HANDOFF.md (under 200 words), keeping its bullets; set `Last updated:` to today; make "Exact next step" actionable with no other context.
6. `python3 scripts/progress.py check`, then commit code and docs: `docs(G-NN): handoff`.
7. Increment finished: `python3 scripts/progress.py archive INC-n`. Branch merged: append one line to docs/CHANGELOG.md.
