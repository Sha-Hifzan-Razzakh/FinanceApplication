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
TASKS = __TASKS__
GROUPS = __GROUPS__
STATUSES = __STATUSES__
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
