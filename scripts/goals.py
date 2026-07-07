#!/usr/bin/env python3
"""Multi-story completion gate — a ledger that refuses a groundless "done".

Decompose non-trivial work into sequential goals. Each goal completes ONLY with concrete
evidence; the final goal is a verification story that also needs a verify command AND its
result. State persists in ./.fable/goals.json so you can resume across sessions.

  goals.py create --brief "..." --goal "title::objective" --goal "..."   # last = verification
  goals.py next                                    # activate the next goal (handoff)
  goals.py checkpoint --id G001 --status complete --evidence "..."
  goals.py checkpoint --id G00N --status complete --evidence "..." \
           --verify-cmd "pytest -q" --verify-evidence "12 passed"        # final goal
  goals.py status                                  # resume / see the ledger
  goals.py reset                                   # discard the ledger

No dependencies. Exit codes: 0 ok; 1 usage/state error; 2 the gate refused.
"""
import argparse, json, os, sys
from datetime import datetime, timezone

STATE_DIR = ".fable"
STATE = os.path.join(STATE_DIR, "goals.json")

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def load():
    if not os.path.exists(STATE):
        return None
    with open(STATE, encoding="utf-8") as f:
        return json.load(f)
def save(d):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)

def cmd_create(a):
    ex = load()
    if ex and any(g["status"] in ("pending", "active") for g in ex["goals"]) and not a.force:
        die("An active ledger already exists — use `status`, or `create --force` to replace.", 1)
    if not a.goal:
        die("Need at least one --goal.", 1)
    goals = []
    for i, spec in enumerate(a.goal, 1):
        title, _, objective = spec.partition("::")
        goals.append({"id": f"G{i:03d}", "title": title.strip(),
                      "objective": objective.strip() or title.strip(),
                      "status": "pending", "evidence": "", "verify_cmd": "", "verify_evidence": "",
                      "is_verification": i == len(a.goal), "updated_at": now()})
    save({"brief": a.brief or "", "created_at": now(), "goals": goals})
    print(f"Created {len(goals)} goals. Last (G{len(goals):03d}) is the verification story.")
    cmd_status(a)

def cmd_next(a):
    d = load() or die("No ledger. Run `create` first.", 1)
    active = [g for g in d["goals"] if g["status"] == "active"]
    if active:
        g = active[0]
    else:
        pend = [g for g in d["goals"] if g["status"] == "pending"]
        if not pend:
            print("No pending goals — run `status`.")
            return
        g = pend[0]; g["status"] = "active"; g["updated_at"] = now(); save(d)
    extra = "  (VERIFICATION goal — needs --verify-cmd and --verify-evidence)" if g["is_verification"] else ""
    print(f"▶ {g['id']}: {g['title']}{extra}\n  objective: {g['objective']}\n"
          f"  → produce concrete evidence, then: "
          f"goals.py checkpoint --id {g['id']} --status complete --evidence \"...\"")

def cmd_checkpoint(a):
    d = load() or die("No ledger. Run `create` first.", 1)
    gid = a.id or next((g["id"] for g in d["goals"] if g["status"] == "active"), None)
    g = next((x for x in d["goals"] if x["id"] == gid), None)
    if not g:
        die(f"No such goal: {gid}", 1)
    if a.status == "blocked":
        g.update(status="blocked", evidence=(a.evidence or a.note or ""), updated_at=now())
        save(d); print(f"✗ {g['id']} blocked."); return
    if not (a.evidence and a.evidence.strip()):
        die(f"Refused: {g['id']} cannot complete without --evidence.", 2)
    if g["is_verification"] and not ((a.verify_cmd and a.verify_cmd.strip()) and
                                     (a.verify_evidence and a.verify_evidence.strip())):
        die(f"Refused: verification goal {g['id']} needs --verify-cmd AND --verify-evidence.", 2)
    g.update(status="complete", evidence=a.evidence.strip(),
             verify_cmd=(a.verify_cmd or "").strip(), verify_evidence=(a.verify_evidence or "").strip(),
             updated_at=now())
    save(d); print(f"✓ {g['id']} complete.")
    if all(x["status"] == "complete" for x in d["goals"]):
        print("ALL GOALS COMPLETE — verified done.")

def cmd_status(a):
    d = load()
    if not d:
        print("No active ledger.")
        return
    mark = {"complete": "✓", "active": "▶", "blocked": "✗", "pending": "·"}
    done = sum(g["status"] == "complete" for g in d["goals"])
    print(f"brief: {d.get('brief', '')}")
    for g in d["goals"]:
        ev = f" — {g['evidence'][:60]}" if g["evidence"] else ""
        v = f"  [verify: {g['verify_cmd']} → {g['verify_evidence'][:40]}]" if g["is_verification"] and g["verify_cmd"] else ""
        print(f"  {mark[g['status']]} {g['id']} {g['title']}{ev}{v}")
    remaining = [g for g in d["goals"] if g["status"] in ("pending", "active")]
    print(f"— {done}/{len(d['goals'])} complete." + ("" if not remaining else f" {len(remaining)} to go — NOT done."))

def cmd_reset(a):
    if os.path.exists(STATE):
        os.remove(STATE); print("Ledger reset.")
    else:
        print("No ledger.")

def main():
    p = argparse.ArgumentParser(description="Multi-story completion gate")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("--brief"); c.add_argument("--goal", action="append")
    c.add_argument("--force", action="store_true"); c.set_defaults(fn=cmd_create)
    sub.add_parser("next").set_defaults(fn=cmd_next)
    k = sub.add_parser("checkpoint"); k.add_argument("--id")
    k.add_argument("--status", choices=["complete", "blocked"], default="complete")
    k.add_argument("--evidence"); k.add_argument("--verify-cmd", dest="verify_cmd")
    k.add_argument("--verify-evidence", dest="verify_evidence"); k.add_argument("--note")
    k.set_defaults(fn=cmd_checkpoint)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("reset").set_defaults(fn=cmd_reset)
    a = p.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
