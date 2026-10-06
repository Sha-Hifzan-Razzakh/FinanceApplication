---
description: Start the next ready session group
---
1. `python3 scripts/progress.py summary` names the next group and its model. If that is not the current model, stop and ask for `/model <name>`.
2. `git switch -c g<NN>-<short-name>`, then `python3 scripts/progress.py start G-<NN> --branch <branch>`.
3. Take the group's tasks in the listed order. For each: read tasks/<id>.md, write its tests, see them fail, implement,
   run `make lint typecheck test-unit`, then `python3 scripts/progress.py done <id> --evidence "<proof of Done when>" --tests "<TS ids>"`.
