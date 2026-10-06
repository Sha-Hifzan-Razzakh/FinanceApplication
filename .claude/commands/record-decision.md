---
description: Append a decision record
---
Decision: $ARGUMENTS

1. Append `### DR-NNN — <date> — <title>` with bullets Closes · Context · Decision · Consequences · Decided by to docs/DECISIONS.md with `cat >>`.
2. If it changes the spec: append to docs/SPEC_CHANGES.md, edit spec/itp_data.py, run `make docs`, commit spec and docs together, then change code.
