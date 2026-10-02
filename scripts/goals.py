#!/usr/bin/env python3
"""Multi-story completion gate — a ledger that refuses a groundless "done".

Decompose non-trivial work into sequential goals. Each goal completes ONLY with concrete
evidence; the final goal is a verification story that also needs a verify command AND its
result. State persists in <project>/.fable/goals.json so you can resume across sessions. <project> is
$CLAUDE_PROJECT_DIR when set, else the git toplevel, else the current directory, so a `cd`
inside a git repo cannot fork the ledger (outside git, `create` prints the path it used).

  goals.py create --brief "..." --goal "title::objective" --goal "..."   # last = verification
  goals.py next                                    # activate the next goal (handoff)
  goals.py checkpoint --id G001 --status complete --evidence "..."
  goals.py checkpoint --id G00N --status complete --evidence "..." \
           --verify-cmd "pytest -q" --verify-evidence "12 passed"        # final goal
  goals.py status                                  # resume / see the ledger
  goals.py reset                                   # discard the ledger

No dependencies. Exit codes: 0 ok; 1 usage/state error; 2 the gate refused.
"""
import argparse, contextlib, json, os, subprocess, sys, time
from datetime import datetime, timezone

def project_root():
    """Anchor for the ledger. Keep in sync with ledger_paths() in hooks/verify_gate.py.
    ponytail: no walk-up search (a stray ledger in a parent directory would arm the gate in unrelated
    projects), so a non-git project launched outside CLAUDE_PROJECT_DIR anchors at cwd; `create` prints
    the path it used so a fork shows up."""
    d = os.environ.get("CLAUDE_PROJECT_DIR")
    if d and os.path.isdir(d):
        return d
    if d:
        print(f"warning: CLAUDE_PROJECT_DIR={d!r} is not a directory, ignoring it", file=sys.stderr)
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5).stdout.strip()
        if top:
            return top
    except (OSError, subprocess.SubprocessError):
        pass
    return os.getcwd()

STATE_DIR = os.path.join(project_root(), ".fable")
STATE = os.path.join(STATE_DIR, "goals.json")
LOCK = STATE + ".lock"
GOAL_KEYS = ("id", "title", "status", "evidence", "is_verification", "verify_cmd", "verify_evidence")
OPEN = ("pending", "active", "blocked")   # anything not complete: a blocked goal still means "not done"

def ensure_state_dir():
    """Create .fable/ with a self-ignoring .gitignore so the ledger never shows in the user's git status.
    ponytail: an existing .gitignore is the user's and is never overwritten."""
    os.makedirs(STATE_DIR, exist_ok=True)
    try:
        with open(os.path.join(STATE_DIR, ".gitignore"), "x", encoding="utf-8") as f:
            f.write("*\n")
    except FileExistsError:
        pass

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)
def load():
    if not os.path.exists(STATE):
        return None
    try:
        with open(STATE, encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d.get("goals"), list):
            raise ValueError("no goals list")
        if not all(isinstance(g, dict) and all(k in g for k in GOAL_KEYS) for g in d["goals"]):
            raise ValueError("malformed goal entry")
        return d
    except (OSError, ValueError, AttributeError) as e:
        die(f"Ledger unreadable ({STATE}: {type(e).__name__}). Fix it by hand or `goals.py reset` to discard it.", 1)
def save(d):
    """Write a temp file then os.replace, so a reader never sees a half-written ledger."""
    ensure_state_dir()
    tmp =f"{STATE}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
            f.flush()
            os.fsync(f.fileno())    # a crash must not leave a zero-length ledger behind the rename
        os.replace(tmp, STATE)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

@contextlib.contextmanager
def locked(create):
    """Serialize load-modify-save across processes with an O_EXCL lock file.
    The lock file holds its owner's token and is removed only by that owner, so a holder that overran the
    30 s stale threshold cannot delete the lock of the process that broke it.
    ponytail: a lock older than 30 s is treated as left by a killed process and broken (two
    processes breaking it at once can both proceed, and the owner check is read-then-remove);
    use fcntl/msvcrt if that ever matters."""
    if not os.path.isdir(STATE_DIR):
        if not create:
            yield        # nothing to protect yet; the command will say there is no ledger
            return
        ensure_state_dir()
    deadline = time.monotonic() + 10
    token = f"{os.getpid()}.{os.urandom(8).hex()}"
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, token.encode())
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(LOCK) > 30:
                    os.remove(LOCK)
                    continue
            except OSError:
                pass
            if time.monotonic() > deadline:
                die(f"Ledger busy: another goals.py holds {LOCK}. Remove it if none is running.", 1)
            time.sleep(0.05)
    try:
        yield
    finally:
        os.close(fd)
        try:
            with open(LOCK, encoding="utf-8") as f:
                mine = f.read() == token
            if mine:
                os.remove(LOCK)
        except OSError:
            pass

def cmd_create(a):
    ex = load()
    if ex and any(g["status"] in OPEN for g in ex["goals"]) and not a.force:
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
    print(f"Created {len(goals)} goals in {STATE}. Last (G{len(goals):03d}) is the verification story.")
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
    remaining = [g for g in d["goals"] if g["status"] in OPEN]
    stuck = sum(g["status"] == "blocked" for g in remaining)
    print(f"— {done}/{len(d['goals'])} complete." + ("" if not remaining else
          f" {len(remaining)} to go" + (f" ({stuck} blocked)" if stuck else "") + " — NOT done."))

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
    a = p.parse_args()
    sys.stdout.reconfigure(errors="replace")   # the ✓ ▶ ✗ glyphs must not crash an ASCII console after save()
    if a.cmd == "status":
        a.fn(a)
    else:
        with locked(create=a.cmd == "create"):
            a.fn(a)

if __name__ == "__main__":
    main()
