#!/usr/bin/env python3
"""Build status tool: the only writer of docs/PROGRESS.md. Stdlib only. GENERATED from spec/itp_data.py.

  summary                              3 lines: counts, current group, next group + model
  start G-xx [--branch NAME]           mark the group's todo tasks in progress, set focus
  done T-xxx --evidence E --tests T [--pr PR]
  block T-xxx --note N
  log --done D --next N [--notes X]    append a session entry to SESSION_LOG.md
  archive INC-n                        move a finished increment (rows, records, log) to docs/archive/
  check                                validate; exit 1 on errors
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROG = ROOT / "docs/PROGRESS.md"
LOG = ROOT / "docs/SESSION_LOG.md"
HANDOFF = ROOT / "docs/HANDOFF.md"
ARCH = ROOT / "docs/archive"
TASKS = {
 "T-101": {
  "deps": [],
  "group": "G-01",
  "inc": "INC-1",
  "title": "Project skeleton and settings"
 },
 "T-102": {
  "deps": [
   "T-101"
  ],
  "group": "G-01",
  "inc": "INC-1",
  "title": "Principal and entity dependency"
 },
 "T-103": {
  "deps": [
   "T-101"
  ],
  "group": "G-01",
  "inc": "INC-1",
  "title": "Common contracts"
 },
 "T-104": {
  "deps": [
   "T-101"
  ],
  "group": "G-01",
  "inc": "INC-1",
  "title": "Run ledger"
 },
 "T-105": {
  "deps": [
   "T-101"
  ],
  "group": "G-01",
  "inc": "INC-1",
  "title": "Tracing"
 },
 "T-106": {
  "deps": [
   "T-103"
  ],
  "group": "G-02",
  "inc": "INC-1",
  "title": "File service and storage port"
 },
 "T-107": {
  "deps": [
   "T-102",
   "T-106"
  ],
  "group": "G-02",
  "inc": "INC-1",
  "title": "Upload route"
 },
 "T-108": {
  "deps": [
   "T-106"
  ],
  "group": "G-02",
  "inc": "INC-1",
  "title": "Intake job handler"
 },
 "T-109": {
  "deps": [
   "T-103"
  ],
  "group": "G-03",
  "inc": "INC-1",
  "title": "Document classification"
 },
 "T-110": {
  "deps": [
   "T-106"
  ],
  "group": "G-03",
  "inc": "INC-1",
  "title": "PDF reading"
 },
 "T-111": {
  "deps": [
   "T-110",
   "T-112"
  ],
  "group": "G-04",
  "inc": "INC-1",
  "title": "Invoice extraction"
 },
 "T-112": {
  "deps": [
   "T-103"
  ],
  "group": "G-03",
  "inc": "INC-1",
  "title": "Invoice contracts and validators"
 },
 "T-113": {
  "deps": [
   "T-111"
  ],
  "group": "G-04",
  "inc": "INC-1",
  "title": "Extraction test set"
 },
 "T-201": {
  "deps": [
   "T-103"
  ],
  "group": "G-05",
  "inc": "INC-2",
  "title": "ERP MCP server: read tools"
 },
 "T-202": {
  "deps": [
   "T-201"
  ],
  "group": "G-05",
  "inc": "INC-2",
  "title": "ERP port and MCP client adapter"
 },
 "T-203": {
  "deps": [
   "T-202"
  ],
  "group": "G-06",
  "inc": "INC-2",
  "title": "Validation rules"
 },
 "T-204": {
  "deps": [
   "T-202"
  ],
  "group": "G-06",
  "inc": "INC-2",
  "title": "Duplicate detection"
 },
 "T-205": {
  "deps": [
   "T-202"
  ],
  "group": "G-06",
  "inc": "INC-2",
  "title": "Line mapping"
 },
 "T-206": {
  "deps": [
   "T-205"
  ],
  "group": "G-06",
  "inc": "INC-2",
  "title": "Three-way match"
 },
 "T-207": {
  "deps": [
   "T-103"
  ],
  "group": "G-07",
  "inc": "INC-2",
  "title": "Goal spec, limits and predicates"
 },
 "T-208": {
  "deps": [
   "T-207",
   "T-209"
  ],
  "group": "G-07",
  "inc": "INC-2",
  "title": "Run graph skeleton"
 },
 "T-209": {
  "deps": [
   "T-103"
  ],
  "group": "G-07",
  "inc": "INC-2",
  "title": "Run state and reducer"
 },
 "T-210": {
  "deps": [
   "T-202"
  ],
  "group": "G-08",
  "inc": "INC-2",
  "title": "Tool registry"
 },
 "T-211": {
  "deps": [
   "T-210",
   "T-209"
  ],
  "group": "G-08",
  "inc": "INC-2",
  "title": "control.act()"
 },
 "T-212": {
  "deps": [
   "T-201"
  ],
  "group": "G-05",
  "inc": "INC-2",
  "title": "ERP write tools"
 },
 "T-213": {
  "deps": [
   "T-208"
  ],
  "group": "G-07",
  "inc": "INC-2",
  "title": "Checkpointer and durable resume"
 },
 "T-214": {
  "deps": [
   "T-211",
   "T-212"
  ],
  "group": "G-08",
  "inc": "INC-2",
  "title": "Posting and scheduling nodes"
 },
 "T-301": {
  "deps": [
   "T-211"
  ],
  "group": "G-09",
  "inc": "INC-3",
  "title": "Autonomy matrix and escalation"
 },
 "T-302": {
  "deps": [
   "T-102",
   "T-301"
  ],
  "group": "G-09",
  "inc": "INC-3",
  "title": "Approvals store and API"
 },
 "T-303": {
  "deps": [
   "T-302",
   "T-213"
  ],
  "group": "G-09",
  "inc": "INC-3",
  "title": "Interrupt and resume"
 },
 "T-304": {
  "deps": [
   "T-208"
  ],
  "group": "G-09",
  "inc": "INC-3",
  "title": "Run event stream"
 },
 "T-305": {
  "deps": [
   "T-206"
  ],
  "group": "G-10",
  "inc": "INC-3",
  "title": "Resolution proposal (single agent)"
 },
 "T-306": {
  "deps": [
   "T-208"
  ],
  "group": "G-10",
  "inc": "INC-3",
  "title": "Recovery policy and node"
 },
 "T-307": {
  "deps": [
   "T-212"
  ],
  "group": "G-10",
  "inc": "INC-3",
  "title": "Compensation registry"
 },
 "T-308": {
  "deps": [
   "T-303",
   "T-306"
  ],
  "group": "G-10",
  "inc": "INC-3",
  "title": "Scenario: INV-88213"
 },
 "T-401": {
  "deps": [
   "T-106"
  ],
  "group": "G-11",
  "inc": "INC-4",
  "title": "Contract ingestion"
 },
 "T-402": {
  "deps": [
   "T-401"
  ],
  "group": "G-11",
  "inc": "INC-4",
  "title": "Hybrid retriever with guards"
 },
 "T-403": {
  "deps": [
   "T-402"
  ],
  "group": "G-12",
  "inc": "INC-4",
  "title": "Answer graph"
 },
 "T-404": {
  "deps": [
   "T-403"
  ],
  "group": "G-12",
  "inc": "INC-4",
  "title": "Claim verifier"
 },
 "T-405": {
  "deps": [
   "T-403"
  ],
  "group": "G-12",
  "inc": "INC-4",
  "title": "Ask route"
 },
 "T-406": {
  "deps": [
   "T-403",
   "T-210"
  ],
  "group": "G-12",
  "inc": "INC-4",
  "title": "ask_policy as a tool"
 },
 "T-407": {
  "deps": [
   "T-209"
  ],
  "group": "G-13",
  "inc": "INC-4",
  "title": "Supplier memory"
 },
 "T-408": {
  "deps": [
   "T-305"
  ],
  "group": "G-13",
  "inc": "INC-4",
  "title": "Resolution subgraph"
 },
 "T-409": {
  "deps": [
   "T-408"
  ],
  "group": "G-13",
  "inc": "INC-4",
  "title": "Analyst–auditor team"
 },
 "T-410": {
  "deps": [
   "T-405"
  ],
  "group": "G-13",
  "inc": "INC-4",
  "title": "Grounding baseline"
 },
 "T-501": {
  "deps": [
   "T-106"
  ],
  "group": "G-14",
  "inc": "INC-5",
  "title": "Portal collector"
 },
 "T-502": {
  "deps": [
   "T-106"
  ],
  "group": "G-14",
  "inc": "INC-5",
  "title": "Mailbox intake"
 },
 "T-503": {
  "deps": [
   "T-106"
  ],
  "group": "G-14",
  "inc": "INC-5",
  "title": "Voicemail transcription"
 },
 "T-504": {
  "deps": [
   "T-503"
  ],
  "group": "G-15",
  "inc": "INC-5",
  "title": "Supplier query classification"
 },
 "T-505": {
  "deps": [
   "T-504",
   "T-301"
  ],
  "group": "G-15",
  "inc": "INC-5",
  "title": "Supplier replies"
 },
 "T-506": {
  "deps": [
   "T-505"
  ],
  "group": "G-15",
  "inc": "INC-5",
  "title": "Supplier isolation filter"
 },
 "T-601": {
  "deps": [
   "T-308"
  ],
  "group": "G-16",
  "inc": "INC-6",
  "title": "Trace-derived tests"
 },
 "T-602": {
  "deps": [
   "T-308"
  ],
  "group": "G-16",
  "inc": "INC-6",
  "title": "Red-team suite"
 },
 "T-603": {
  "deps": [
   "T-302"
  ],
  "group": "G-16",
  "inc": "INC-6",
  "title": "Approval console E2E"
 },
 "T-604": {
  "deps": [
   "T-105"
  ],
  "group": "G-16",
  "inc": "INC-6",
  "title": "Dashboards and alerts"
 },
 "T-605": {
  "deps": [
   "T-601",
   "T-602",
   "T-603"
  ],
  "group": "G-16",
  "inc": "INC-6",
  "title": "Release gate"
 }
}
GROUPS = {
 "G-01": {
  "name": "Spine",
  "tasks": [
   "T-101",
   "T-102",
   "T-103",
   "T-104",
   "T-105"
  ],
  "model": "sonnet"
 },
 "G-02": {
  "name": "File intake",
  "tasks": [
   "T-106",
   "T-107",
   "T-108"
  ],
  "model": "sonnet"
 },
 "G-03": {
  "name": "Invoice contracts and reading",
  "tasks": [
   "T-112",
   "T-109",
   "T-110"
  ],
  "model": "sonnet"
 },
 "G-04": {
  "name": "Extraction",
  "tasks": [
   "T-111",
   "T-113"
  ],
  "model": "sonnet"
 },
 "G-05": {
  "name": "ERP over MCP",
  "tasks": [
   "T-201",
   "T-202",
   "T-212"
  ],
  "model": "sonnet"
 },
 "G-06": {
  "name": "Validation and match",
  "tasks": [
   "T-203",
   "T-204",
   "T-205",
   "T-206"
  ],
  "model": "sonnet"
 },
 "G-07": {
  "name": "Run core",
  "tasks": [
   "T-207",
   "T-209",
   "T-208",
   "T-213"
  ],
  "model": "opus"
 },
 "G-08": {
  "name": "Control layer",
  "tasks": [
   "T-210",
   "T-211",
   "T-214"
  ],
  "model": "opus"
 },
 "G-09": {
  "name": "Escalation and approvals",
  "tasks": [
   "T-301",
   "T-302",
   "T-303",
   "T-304"
  ],
  "model": "opus"
 },
 "G-10": {
  "name": "Resolution and recovery",
  "tasks": [
   "T-305",
   "T-306",
   "T-307",
   "T-308"
  ],
  "model": "opus"
 },
 "G-11": {
  "name": "Contract knowledge",
  "tasks": [
   "T-401",
   "T-402"
  ],
  "model": "sonnet"
 },
 "G-12": {
  "name": "Cited answers",
  "tasks": [
   "T-403",
   "T-404",
   "T-405",
   "T-406"
  ],
  "model": "opus"
 },
 "G-13": {
  "name": "Memory and review team",
  "tasks": [
   "T-407",
   "T-408",
   "T-409",
   "T-410"
  ],
  "model": "sonnet"
 },
 "G-14": {
  "name": "Channels",
  "tasks": [
   "T-501",
   "T-502",
   "T-503"
  ],
  "model": "sonnet"
 },
 "G-15": {
  "name": "Supplier communication",
  "tasks": [
   "T-504",
   "T-505",
   "T-506"
  ],
  "model": "opus"
 },
 "G-16": {
  "name": "Assurance",
  "tasks": [
   "T-601",
   "T-602",
   "T-603",
   "T-604",
   "T-605"
  ],
  "model": "sonnet"
 }
}
STATUSES = ["todo", "in progress", "blocked", "done"]
ROW = re.compile(r"^\|\s*(T-\d{3})\s*\|")
COL = {"status": 4, "pr": 5, "updated": 6, "notes": 7}


def today():
    return datetime.date.today().isoformat()


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def sources():
    files = [PROG] + (sorted(ARCH.glob("INC-*.md")) if ARCH.exists() else [])
    return [(f, f.read_text()) for f in files]


def statuses():
    out, dups = {}, []
    for _, text in sources():
        for line in text.splitlines():
            m = ROW.match(line)
            if m:
                if m.group(1) in out:
                    dups.append(m.group(1))
                out[m.group(1)] = cells(line)[COL["status"]].lower()
    return out, dups


def all_text():
    return "\n".join(t for _, t in sources())


def edit_row(tid, **values):
    lines = PROG.read_text().splitlines()
    for i, line in enumerate(lines):
        if ROW.match(line) and cells(line)[0] == tid:
            c = cells(line)
            for k, v in values.items():
                c[COL[k]] = v
            lines[i] = "| " + " | ".join(c) + " |"
            PROG.write_text("\n".join(lines) + "\n")
            return
    sys.exit(f"{tid} is not an open row in PROGRESS.md (archived?)")


def set_focus(group, branch):
    text = PROG.read_text()
    text = re.sub(r"^- Group: .*$", f"- Group: {group}", text, flags=re.M)
    text = re.sub(r"^- Branch: .*$", f"- Branch: {branch}", text, flags=re.M)
    text = re.sub(r"^- Since: .*$", f"- Since: {today() if group != 'none' else '—'}", text, flags=re.M)
    PROG.write_text(text)


def deps_done(tid, st):
    return all(st.get(d) == "done" for d in TASKS[tid]["deps"])


def group_ready(g, st):
    inside = set(GROUPS[g]["tasks"])
    return all(st.get(d) == "done" for t in inside for d in TASKS[t]["deps"] if d not in inside)


def current_group(st):
    gs = sorted({TASKS[t]["group"] for t, s in st.items() if t in TASKS and s in ("in progress", "blocked")})
    return gs[0] if gs else None


def next_group(st):
    for g, info in GROUPS.items():
        if any(st.get(t) != "done" for t in info["tasks"]) and group_ready(g, st):
            return g
    return None


def cmd_summary(_):
    st, _ = statuses()
    counts = " · ".join(f"{s} {sum(1 for v in st.values() if v == s)}" for s in STATUSES)
    print(f"Progress: {counts} (of {len(TASKS)})")
    cur = current_group(st)
    if cur:
        left = [t for t in GROUPS[cur]["tasks"] if st.get(t) != "done"]
        print(f"Current: {cur} {GROUPS[cur]['name']} (model {GROUPS[cur]['model']}) · open: {', '.join(left)}")
        print("Next: finish the current group")
    else:
        print("Current: none")
        nxt = next_group(st)
        print(f"Next: {nxt} {GROUPS[nxt]['name']} (model {GROUPS[nxt]['model']}) · {', '.join(GROUPS[nxt]['tasks'])}"
              if nxt else "Next: nothing ready")


def cmd_start(a):
    st, _ = statuses()
    if a.group not in GROUPS:
        sys.exit(f"unknown group {a.group}")
    cur = current_group(st)
    if cur and cur != a.group:
        sys.exit(f"{cur} is still in progress")
    if not group_ready(a.group, st):
        sys.exit(f"{a.group} has unfinished dependencies")
    for t in GROUPS[a.group]["tasks"]:
        if st.get(t) == "todo":
            edit_row(t, status="in progress", pr=a.branch or "", updated=today())
    set_focus(a.group, a.branch or "—")
    print(f"started {a.group} · model {GROUPS[a.group]['model']}")


def cmd_done(a):
    st, _ = statuses()
    if a.task not in TASKS:
        sys.exit(f"unknown task {a.task}")
    missing = [d for d in TASKS[a.task]["deps"] if st.get(d) != "done"]
    if missing:
        sys.exit(f"{a.task}: dependencies not done: {', '.join(missing)}")
    edit_row(a.task, status="done", updated=today(), **({"pr": a.pr} if a.pr else {}))
    with PROG.open("a") as f:
        f.write(f"### {a.task} · {TASKS[a.task]['title']} · done {today()}{' · ' + a.pr if a.pr else ''}\n"
                f"- Evidence: {a.evidence}\n- Tests: {a.tests}\n")
    st, _ = statuses()
    g = TASKS[a.task]["group"]
    if all(st.get(t) == "done" for t in GROUPS[g]["tasks"]):
        set_focus("none", "—")
        print(f"{g} complete")
    print(f"{a.task} done")


def cmd_block(a):
    edit_row(a.task, status="blocked", updated=today(), notes=a.note)
    print(f"{a.task} blocked: {a.note}")


def cmd_log(a):
    n = len(re.findall(r"^### S-\d+", all_text() + "\n" + LOG.read_text(), re.M)) + 1
    st, _ = statuses()
    with LOG.open("a") as f:
        f.write(f"### S-{n:03d} · {today()} · {current_group(st) or '—'}\n- Done: {a.done}\n- Next: {a.next}\n"
                + (f"- Notes: {a.notes}\n" if a.notes else ""))
    print(f"logged S-{n:03d}")


def cmd_archive(a):
    st, _ = statuses()
    ids = [t for t, v in TASKS.items() if v["inc"] == a.inc]
    if any(st.get(t) != "done" for t in ids):
        sys.exit(f"{a.inc} is not finished")
    text = PROG.read_text()
    m = re.search(rf"^## {re.escape(a.inc)} · .*?(?=^## )", text, re.S | re.M)
    if not m:
        sys.exit(f"{a.inc} section not found (already archived?)")
    section = m.group(0)
    text = text.replace(section, "")
    recs = []
    for t in ids:
        r = re.search(rf"^### {t} · .*?(?=^### |\Z)", text, re.S | re.M)
        if r:
            recs.append(r.group(0))
            text = text.replace(r.group(0), "")
    log = LOG.read_text()
    first = re.search(r"^### S-", log, re.M)
    entries = log[first.start():] if first else ""
    if first:
        LOG.write_text(log[:first.start()])
    ARCH.mkdir(parents=True, exist_ok=True)
    (ARCH / f"{a.inc}.md").write_text(
        f"# Archive · {a.inc}\n\n{section}\n## Completion records\n\n{''.join(recs)}\n## Session log\n\n{entries}")
    PROG.write_text(text)
    print(f"archived {a.inc}")


def cmd_check(_):
    st, dups = statuses()
    text = all_text()
    errors = [f"{d} appears twice" for d in dups]
    for t in TASKS:
        if t not in st:
            errors.append(f"{t} missing")
        elif st[t] not in STATUSES:
            errors.append(f"{t} has unknown status '{st[t]}'")
    for t, s in st.items():
        if t not in TASKS:
            errors.append(f"{t} is not in the spec")
            continue
        outside = [d for d in TASKS[t]["deps"] if TASKS[d]["group"] != TASKS[t]["group"]]
        if s == "done" and not deps_done(t, st):
            errors.append(f"{t} is done but a dependency is not")
        if s == "in progress" and any(st.get(d) != "done" for d in outside):
            errors.append(f"{t} is in progress but a dependency outside its group is not done")
        if s == "done" and not re.search(rf"^### {t} ", text, re.M):
            errors.append(f"{t} is done but has no completion record")
    if len({TASKS[t]["group"] for t, s in st.items() if t in TASKS and s == "in progress"}) > 1:
        errors.append("more than one group in progress")
    if not re.search(r"^Last updated:", HANDOFF.read_text(), re.M):
        errors.append("HANDOFF.md has no 'Last updated:' line")
    for e in errors:
        print("ERROR:", e)
    print("ok" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    sub.add_parser("check")
    p = sub.add_parser("start"); p.add_argument("group"); p.add_argument("--branch")
    p = sub.add_parser("done"); p.add_argument("task"); p.add_argument("--evidence", required=True)
    p.add_argument("--tests", required=True); p.add_argument("--pr")
    p = sub.add_parser("block"); p.add_argument("task"); p.add_argument("--note", required=True)
    p = sub.add_parser("log"); p.add_argument("--done", required=True); p.add_argument("--next", required=True)
    p.add_argument("--notes")
    p = sub.add_parser("archive"); p.add_argument("inc")
    a = ap.parse_args()
    fn = {"summary": cmd_summary, "start": cmd_start, "done": cmd_done, "block": cmd_block,
          "log": cmd_log, "archive": cmd_archive, "check": cmd_check}[a.cmd]
    return fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
