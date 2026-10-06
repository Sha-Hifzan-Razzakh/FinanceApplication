"""Builds the repository's Markdown docs from itp_data.py (the single source).

Generated files are always rewritten. Living files (PROGRESS, HANDOFF, SESSION_LOG,
DECISIONS, OPEN_QUESTIONS, DEBT, CHANGELOG, SPEC_CHANGES) are created only when
missing, so a rebuild never erases what sessions have recorded.

    python spec/build_repo_docs.py --repo .          # inside the repo
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itp_data as D  # noqa: E402

GEN = "<!-- GENERATED from spec/itp_data.py by spec/build_repo_docs.py. Do not edit: change the spec and run `make docs`. -->"
LIVING = "<!-- LIVING document: created once from the spec, maintained by every session. Rebuilds never overwrite it. -->"

# ------------------------------------------------------------------ helpers
cap_name = {c[0]: c[1] for c in D.CAPABILITIES}
task_of = {t[0]: t for t in D.TASKS}
model_by_name = {m[1]: m for m in D.MODELS}
model_order = {m[1]: i for i, m in enumerate(D.MODELS)}
split = lambda s: [x.strip() for x in s.split(",") if x.strip()]  # noqa: E731
contracts_by_task: dict[str, set[str]] = {}
for _cs in D.CODE:
    for _m in split(_cs[9]) + split(_cs[10]):
        contracts_by_task.setdefault(_cs[1], set()).add(_m)


def cell(v) -> str:
    return str(v).replace("|", "\\|").replace("\n", " ")


def table(headers, rows) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows]
    return "\n".join(out)


GROUP_OF = {t: g[0] for g in D.SESSION_GROUPS for t in split(g[2])}
GROUP = {g[0]: g for g in D.SESSION_GROUPS}


def deps(tid: str) -> list[str]:
    return split(task_of[tid][8])


def topo_order() -> list[str]:
    order, done, ids = [], set(), [t[0] for t in D.TASKS]
    while len(order) < len(ids):
        progressed = False
        for tid in ids:
            if tid not in done and all(d in done for d in deps(tid)):
                order.append(tid); done.add(tid); progressed = True
        if not progressed:
            raise ValueError("cycle in task dependencies")
    return order


def class_src(m) -> str:
    _id, name, module, kind, purpose, base, config, validators, task = m
    gen = re.match(r"(\w+)\[(\w+)\]", name)
    cname = gen.group(1) if gen else name
    lines = [f"# {module}", f"class {cname}({base}):", f'    """{purpose}."""']
    if config and config != "—":
        cfg = "SettingsConfigDict" if "BaseSettings" in base else "ConfigDict"
        lines.append(f"    model_config = {cfg}({config})")
    for f, typ, default, cons, desc in D.FIELDS[name]:
        line = f"    {f}: {typ}"
        if default != "required":
            line += f" = {default}"
        note = "; ".join(x for x in (cons, desc) if x)
        if note:
            line += f"  # {note}"
        lines.append(line)
    if validators and validators != "—":
        lines.append(f"    # invariant: {validators}")
    return "\n".join(lines)


def task_prompt(t) -> str:
    tid, inc, cap, title, obj, fw, states, ccaps, dep, days, done = t
    secs = [c for c in D.CODE if c[1] == tid]
    used = sorted(contracts_by_task.get(tid, []), key=lambda m: model_order.get(m, 999))
    own = [m for m in used if model_by_name[m][8] == tid]
    other = [m for m in used if m not in own]
    ftext = (fw + " " + " ".join(c[8] for c in secs)).lower()
    fws = [r[0] for r in D.FRAMEWORK_RULES if r[0].lower().split()[0] in ftext]
    tests = [x for x in D.TESTS if x[4] == tid]
    g = GROUP[GROUP_OF[tid]]
    L = [f"# {tid} · {title}", f"Increment {inc} · {cap} {cap_name[cap]} · group {g[0]} {g[1]} (model {g[3]}) · estimate {days} day(s)", "",
         f"Depends on: {dep or 'nothing'}.", "", "## Goal", obj, "",
         "## Frameworks and features", fw,
         ("Framework rules that apply (docs/FRAMEWORKS.md): " + ", ".join(fws)) if fws else "No framework: plain Python only.", "",
         "## Build these code sections"]
    for c in secs:
        L += [f"- {c[0]} `{c[2]}` · {c[4]} **{c[5]}**", f"  - signature: `{c[6]}`",
              f"  - responsibility: {c[7]}", f"  - framework feature: {c[8]}",
              f"  - contracts in: {c[9] or '—'} · out: {c[10] or '—'} · control state: {c[11]}"]
    if own:
        L += ["", "## Contracts defined in this task (implement exactly)"]
        for m in own:
            L += ["```python", class_src(model_by_name[m]), "```"]
    if other:
        L += ["", "## Contracts used (already defined; import, do not redefine)", ", ".join(other)]
    L += ["", "## Tests to write first (they must fail before your change)"]
    L += [f"- {x[0]} [{x[1]}] {x[2]} — {x[5]}" for x in tests] or ["- Add at least one unit test per code section; name them after the section."]
    L += ["", "## Controls delivered", f"Control states: {states} · control capabilities: {ccaps}", "",
          "## Done when", done, "", "## Out of scope",
          "Anything belonging to another task. Leave `TODO(T-xxx)` markers and list them in docs/DEBT.md.",
          "Need something not in this spec: /ask-question. Need a contract or section not shown: grep docs/CONTRACTS.md or docs/ARCHITECTURE.md; never read them whole.", "",
          "## When finished",
          f'`python3 scripts/progress.py done {tid} --evidence "<test or command proving Done when>" --tests "<TS ids>"`']
    return "\n".join(L)


# ------------------------------------------------------------------ generated docs
def plan_md() -> str:
    L = [f"# Plan", GEN, "",
         "Six increments, sixteen session groups. `python3 scripts/progress.py summary` always names the next group, so this file is rarely needed.", ""]
    L += [table(["Increment", "Name", "Goal", "Gate (done when)"], D.INCREMENTS), ""]
    grows = [(g[0], g[1], g[2], g[3], sum(task_of[t][9] for t in split(g[2])), g[4]) for g in D.SESSION_GROUPS]
    L += ["## Session groups (in this order; one branch per group)",
          table(["Group", "Name", "Tasks", "Model", "Days", "Why this model"], grows), ""]
    L += ["## Capabilities", table(["ID", "Capability", "What it does"], D.CAPABILITIES), ""]
    L += ["## Tasks in dependency order"]
    rows = []
    for i, tid in enumerate(topo_order(), 1):
        t = task_of[tid]
        rows.append((i, tid, GROUP_OF[tid], t[3], t[8] or "—", t[9], f"[spec](../tasks/{tid}.md)"))
    L += [table(["#", "Task", "Group", "Title", "Depends on", "Days", "Spec"], rows), ""]
    L += [f"Total estimate: {sum(t[9] for t in D.TASKS)} days across {len(D.TASKS)} tasks (indicative)."]
    return "\n".join(L) + "\n"


def architecture_md() -> str:
    layers: dict[str, list] = {}
    for cs in D.CODE:
        layers.setdefault(cs[3], []).append(cs)
    L = ["# Architecture", GEN, "",
         "Hexagonal: `domain/` and `application/` import no framework; each framework sits behind a port in `adapters/`; "
         "every external write passes through `control.act()`.", "",
         "## Code sections by layer"]
    for layer, items in layers.items():
        L += [f"### {layer}", table(["ID", "Task", "Module", "Kind", "Name", "Responsibility"],
                                   [(c[0], c[1], f"`{c[2]}`", c[4], c[5], c[7]) for c in items]), ""]
    L += ["## Ports and adapters", table(["Port", "Methods", "Adapter", "Framework", "Features", "Rule"], D.PORTS), "",
          "## Graphs", table(["Graph", "Node", "Code section", "Control states", "Reads", "Writes", "Edges out"], D.GRAPH), "",
          "## The 15 controls in code", table(["Control", "Meaning here", "Code sections", "Frameworks", "On failure"], D.CONTROLS), "",
          "## Tool registry", table(["Tool", "Server", "Risk", "Input", "Output", "Requires", "Idempotency key", "Verified by", "Undo", "Timeout s", "Scope"], D.TOOLS), "",
          "## API routes", table(["Method", "Path", "Request", "Response", "Dependencies", "Status codes", "Task"], D.ROUTES), "",
          "## Autonomy matrix", table(["Action", "Risk", "Runs alone when", "Needs approval when", "Never"], D.AUTONOMY), "",
          "## Recovery policy", table(["Error", "Raised by", "Response", "Limit", "Target", "After the limit"], D.RECOVERY), "",
          "## Persistence", table(["Table / store", "Technology", "Owner", "Keys", "Purpose", "Retention"], D.PERSISTENCE), "",
          "## Events", table(["Event", "Producer", "Consumers", "Transport"], D.EVENTS)]
    return "\n".join(L) + "\n"


def contracts_md() -> str:
    by_mod: dict[str, list] = {}
    for m in D.MODELS:
        by_mod.setdefault(m[2], []).append(m)
    L = ["# Contracts", GEN, "", "Implement exactly as written. Changes start in spec/itp_data.py.", ""]
    L += [table(["ID", "Model", "Module", "Kind", "Defined in"], [(m[0], m[1], f"`{m[2]}`", m[3], m[8]) for m in D.MODELS]), ""]
    for mod, ms in by_mod.items():
        L += [f"## `{mod}`", "```python", "\n\n".join(class_src(m) for m in ms), "```", ""]
    return "\n".join(L)


def frameworks_md() -> str:
    return "\n".join([
        "# Frameworks", GEN, "",
        "## Stack", table(["Layer", "Component", "Package", "Minimum line", "Purpose", "Used by", "Docs", "Note"], D.STACK), "",
        "Exact versions are in `uv.lock`; record notable upgrades in docs/DECISIONS.md.", "",
        "## Rules per framework", table(["Framework", "Import only in", "Use for", "Never for", "APIs", "You implement", "Gotchas"], D.FRAMEWORK_RULES),
    ]) + "\n"


def conventions_md() -> str:
    return "\n".join(["# Conventions", GEN, "", table(["ID", "Area", "Rule", "Example"], D.CONVENTIONS)]) + "\n"


def guardrails_md() -> str:
    return "\n".join(["# Guardrails", GEN, "", "## Never", table(["ID", "Never", "Why"], D.GUARDRAILS), "",
                      "## Definition of Done (every task)", *[f"- [ ] {r[0]} {r[1]}" for r in D.DOD]]) + "\n"


def testing_md() -> str:
    return "\n".join([
        "# Testing", GEN, "",
        "Tests are written first, from the task spec. Unit tests make no network calls; integration and scenario tests use the local stack; fakes live in `tests/fakes/`.", "",
        "## Test catalogue", table(["ID", "Type", "Name", "Target", "Task", "Given / when / then"], D.TESTS), "",
        "## Fixtures (fictitious data)", table(["Fixture", "Entity", "Values", "Used by"], D.FIXTURES), "",
        "## Commands", table(["Target", "Command", "What it does"], [c for c in D.COMMANDS if c[0].startswith(("test", "eval", "redteam", "e2e", "gate"))]),
    ]) + "\n"


def environment_md() -> str:
    env = [(f"ITP_{f.upper()}", typ, default, cons, desc) for f, typ, default, cons, desc in D.FIELDS["Settings"]]
    return "\n".join([
        "# Environment", GEN, "",
        "## Local services", table(["Service", "Image / command", "Port", "Purpose", "First needed in"], D.ENV_SERVICES), "",
        "## Environment variables", table(["Variable", "Type", "Default", "Constraints", "Meaning"], env), "",
        "## Commands", table(["Target", "Command", "What it does"], D.COMMANDS), "",
        "## Bootstrap files", table(["Path", "Created in", "Purpose", "Content"], D.BOOTSTRAP),
    ]) + "\n"


def glossary_md() -> str:
    return "\n".join(["# Glossary", GEN, "", table(["Term", "Meaning"], D.GLOSSARY)]) + "\n"


# ------------------------------------------------------------------ living docs (seed only)
def decisions_md() -> str:
    acc = [(a, b, c, "accepted") for a, b, c in D.ACCEPTED_DECISIONS]
    od = [(o[0], o[1], o[2], o[3], "open") for o in D.OPEN_DECISIONS]
    return f"""# Decisions
{LIVING}

Append records with `cat >>`; no need to read the file. Never rewrite a past decision; supersede it.

## Accepted architecture decisions
{table(["ID", "Decision", "Why", "Status"], acc)}

## Open decisions (work proceeds on the default until resolved)
{table(["ID", "Decision", "Why it matters", "Default until decided", "Status"], od)}

## Decision records
Record format: `### DR-NNN — YYYY-MM-DD — <title>` then bullets Closes · Context · Decision · Consequences · Decided by.
"""


def changelog_md() -> str:
    return f"""# Changelog
{LIVING}

One line per merged group, newest at the bottom: `YYYY-MM-DD · G-xx · name · PR`.
"""


def spec_changes_md() -> str:
    return f"""# Spec changes
{LIVING}

Append before `make docs`. Format: `### SC-NNN — YYYY-MM-DD` then bullets What changed · Why (Q/DR id) · Tasks affected.
"""


# ------------------------------------------------------------------ tooling
def claude_md() -> str:
    rules = "\n".join(f"- {r}" for r in D.CORE_RULES)
    return f"""# Invoice-to-Pay Agent
{GEN}
Meridian Supply's AP program: read invoices, validate, three-way match, resolve exceptions with approval, post once, verify, schedule, notify.
Nothing about the build lives in chat history: spec `spec/itp_data.py`, status `docs/PROGRESS.md`, next step `docs/HANDOFF.md` (below).

## Sessions
- Work in session groups (G-01…G-16), one branch per group, on the group's model (`/model sonnet` or `/model opus`). A group may take several sessions.
- `/start-session` → work → `/end-session` (always, finished or not). `/next-group` when no group is in progress.
- Status changes only through `python3 scripts/progress.py …`; never read or rewrite docs/PROGRESS.md by hand.

## Rules
{rules}

## Read on demand, never whole
tasks/T-xxx.md for the current group's tasks (each includes the contracts it needs). For anything else, grep one section of
docs/CONTRACTS.md, docs/ARCHITECTURE.md, docs/FRAMEWORKS.md or docs/GUARDRAILS.md.

## Checks
`make lint typecheck test-unit` every task · `make test-int` / `make test-scenarios` when a task names them · `python3 scripts/progress.py check` before commit.

@docs/HANDOFF.md
"""


def readme_md() -> str:
    rows = [(p, k, r, u) for p, k, r, u, _ in D.REPO_DOCS]
    return f"""# Docs map
{GEN}

**Source** is the spec. **Generated** files are rebuilt by `make docs` and never hand-edited. **Living** files are the build's memory;
rebuilds never overwrite them. A session pays only for CLAUDE.md + HANDOFF.md + a 3-line progress summary + the current task spec.

{table(["File", "Kind", "Read when", "Updated when"], rows)}
"""


def progress_md() -> str:
    L = ["# Progress", LIVING,
         "Edited only by `python3 scripts/progress.py` (start · done · block · archive). Do not read or rewrite by hand.", "",
         "## Current focus", "- Group: none", "- Branch: —", "- Since: —", ""]
    for inc in D.INCREMENTS:
        rows = [(t[0], t[3], GROUP_OF[t[0]], t[8] or "—", "todo", "", "", "") for t in D.TASKS if t[1] == inc[0]]
        L += [f"## {inc[0]} · {inc[1]}",
              table(["Task", "Title", "Group", "Depends on", "Status", "Branch / PR", "Updated", "Notes"], rows), ""]
    L += ["## Completion records", ""]
    return "\n".join(L)


def handoff_md() -> str:
    return f"""# Handoff
{LIVING}
Overwritten by /end-session. Under 200 words. Enough to continue with no other context.

Last updated: never

- Where things stand: nothing built yet.
- Group / task: none. Next is G-01 Spine (sonnet), starting with T-101.
- Branch state: none.
- Exact next step: /next-group
- Blockers: none. Decide OD-03 (model ids) before G-04.
- Uncommitted work: none.
- Tests: none yet.
"""


def session_log_md() -> str:
    return f"""# Session log
{LIVING}
Appended by `python3 scripts/progress.py log`. Entries move to docs/archive/ when an increment is archived.

"""


def open_questions_md() -> str:
    return f"""# Open questions
{LIVING}
Append rows with `cat >>`; no need to read the file.

| ID | Raised | Task | Question | Blocks | Answer | Answered |
|---|---|---|---|---|---|---|
"""


def debt_md() -> str:
    return f"""# Debt
{LIVING}
One row per `TODO(T-xxx)` or shortcut left in code. Append with `cat >>`; delete the row when its task clears it.

| ID | Added | Where (file:line) | What is missing | Cleared by task | Risk until then |
|---|---|---|---|---|---|
"""


def progress_py() -> str:
    tasks = {t[0]: {"deps": deps(t[0]), "group": GROUP_OF[t[0]], "inc": t[1], "title": t[3]} for t in D.TASKS}
    groups = {g[0]: {"name": g[1], "tasks": split(g[2]), "model": g[3]} for g in D.SESSION_GROUPS}
    here = os.path.dirname(os.path.abspath(__file__))
    tpl = open(os.path.join(here, "progress_template.py")).read()
    return (tpl.replace("__TASKS__", json.dumps(tasks, indent=1, ensure_ascii=False))
               .replace("__GROUPS__", json.dumps(groups, indent=1, ensure_ascii=False))
               .replace("__STATUSES__", json.dumps(D.STATUSES)))


COMMAND_FILES = {
    "start-session.md": """---
description: Begin a session from repo state, cheaply
---
docs/HANDOFF.md is already in context. Do not read PROGRESS.md, PLAN.md, CONTRACTS.md or ARCHITECTURE.md whole.

1. Run `python3 scripts/progress.py summary` and `git status -sb`.
2. If a group is current, read tasks/<id>.md only for its first open task. If none is current, run /next-group.
3. If the group's model differs from the one you are running on, say so first.
4. Reply in at most 5 lines (group, task, next step, blockers), then start working.
""",
    "next-group.md": """---
description: Start the next ready session group
---
1. `python3 scripts/progress.py summary` names the next group and its model. If that is not the current model, stop and ask for `/model <name>`.
2. `git switch -c g<NN>-<short-name>`, then `python3 scripts/progress.py start G-<NN> --branch <branch>`.
3. Take the group's tasks in the listed order. For each: read tasks/<id>.md, write its tests, see them fail, implement,
   run `make lint typecheck test-unit`, then `python3 scripts/progress.py done <id> --evidence "<proof of Done when>" --tests "<TS ids>"`.
""",
    "end-session.md": """---
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
""",
    "ask-question.md": """---
description: Record a question the spec does not answer instead of guessing
---
Question: $ARGUMENTS

1. Append a row to docs/OPEN_QUESTIONS.md with `cat >>` (next id: `grep -c '^| Q-' docs/OPEN_QUESTIONS.md` + 1).
2. If it blocks the current task: `python3 scripts/progress.py block <id> --note "Q-NNN"`, then continue with an unblocked task in the group.
""",
    "record-decision.md": """---
description: Append a decision record
---
Decision: $ARGUMENTS

1. Append `### DR-NNN — <date> — <title>` with bullets Closes · Context · Decision · Consequences · Decided by to docs/DECISIONS.md with `cat >>`.
2. If it changes the spec: append to docs/SPEC_CHANGES.md, edit spec/itp_data.py, run `make docs`, commit spec and docs together, then change code.
""",
}


def settings_json() -> str:
    return json.dumps({
        "permissions": {
            "allow": ["Bash(python3 scripts/progress.py:*)", "Bash(uv run:*)", "Bash(uv sync)", "Bash(make:*)",
                      "Bash(git status:*)", "Bash(git diff:*)", "Bash(git add:*)", "Bash(git commit:*)", "Bash(git switch:*)",
                      "Bash(docker compose ps)", "Bash(docker compose logs:*)"],
            "deny": ["Bash(git push --force:*)", "Bash(rm -rf:*)", "Read(.env)", "Read(**/*.pem)"],
        },
        "hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "python3 scripts/progress.py summary || true"}]}]},
    }, indent=2) + "\n"


# ------------------------------------------------------------------ build
GENERATED = {
    "CLAUDE.md": claude_md, "docs/README.md": readme_md, "docs/PLAN.md": plan_md,
    "docs/ARCHITECTURE.md": architecture_md, "docs/CONTRACTS.md": contracts_md, "docs/FRAMEWORKS.md": frameworks_md,
    "docs/CONVENTIONS.md": conventions_md, "docs/GUARDRAILS.md": guardrails_md, "docs/TESTING.md": testing_md,
    "docs/ENVIRONMENT.md": environment_md, "docs/GLOSSARY.md": glossary_md,
    "scripts/progress.py": progress_py, ".claude/settings.json": settings_json,
}
LIVING_DOCS = {
    "docs/PROGRESS.md": progress_md, "docs/HANDOFF.md": handoff_md, "docs/SESSION_LOG.md": session_log_md,
    "docs/DECISIONS.md": decisions_md, "docs/OPEN_QUESTIONS.md": open_questions_md, "docs/DEBT.md": debt_md,
    "docs/CHANGELOG.md": changelog_md, "docs/SPEC_CHANGES.md": spec_changes_md,
}


def build(repo: str) -> dict[str, int]:
    written = {"generated": 0, "living_created": 0, "living_kept": 0}

    def put(rel, text):
        path = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    for rel, fn in GENERATED.items():
        put(rel, fn()); written["generated"] += 1
    for name, text in COMMAND_FILES.items():
        put(f".claude/commands/{name}", text); written["generated"] += 1
    for t in D.TASKS:
        put(f"tasks/{t[0]}.md", f"{GEN}\n\n{task_prompt(t)}\n"); written["generated"] += 1
    for rel, fn in LIVING_DOCS.items():
        if os.path.exists(os.path.join(repo, rel)):
            written["living_kept"] += 1
        else:
            put(rel, fn()); written["living_created"] += 1
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    print(build(ap.parse_args().repo))
