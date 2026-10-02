#!/usr/bin/env python3
"""Self-check for the completion gate (goals.py) + its Stop-hook integration.
Run: python3 scripts/test_goals.py
"""
import subprocess, sys, os, json, tempfile, pathlib, shutil, time

HERE = pathlib.Path(__file__).parent
GOALS = str(HERE / "goals.py")
VGATE = str(HERE.parent / "hooks" / "verify_gate.py")

def env_for(extra=None):
    e = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "FABLE_STRICT")}
    e.update(extra or {})
    return e

def run(args, cwd, env=None):
    p = subprocess.run([sys.executable, GOALS] + args, cwd=cwd, capture_output=True, text=True, env=env_for(env))
    return p.returncode, p.stdout + p.stderr

fails = 0
def check(cond, label):
    global fails
    print(("PASS " if cond else "FAIL ") + label)
    fails += 0 if cond else 1

d = tempfile.mkdtemp()
rc, o = run(["create", "--brief", "x", "--goal", "A::do a", "--goal", "B::verify"], d)
check(rc == 0 and "2 goals" in o, "create makes 2 goals (last = verification)")
rc, o = run(["checkpoint", "--id", "G001", "--status", "complete"], d)
check(rc == 2, "refuse complete without --evidence")
rc, o = run(["checkpoint", "--id", "G001", "--status", "complete", "--evidence", "did a"], d)
check(rc == 0, "complete with evidence ok")
rc, o = run(["checkpoint", "--id", "G002", "--status", "complete", "--evidence", "ran"], d)
check(rc == 2, "refuse verification goal without verify-cmd/evidence")
rc, o = run(["checkpoint", "--id", "G002", "--status", "complete", "--evidence", "ran",
             "--verify-cmd", "pytest", "--verify-evidence", "5 passed"], d)
check(rc == 0 and "ALL GOALS COMPLETE" in o, "verification goal completes with verify evidence")
rc, o = run(["status"], d)
check(rc == 0 and "2/2" in o, "status shows all complete")
rc, o = run(["next"], d)
check(rc == 0 and "No pending goals" in o, "next on a finished ledger reports nothing pending")
rc, o = run(["reset"], d)
check(rc == 0 and not os.path.exists(os.path.join(d, ".fable", "goals.json")), "reset removes the ledger")
check(sorted(os.listdir(os.path.join(d, ".fable"))) == [".gitignore"], "no temp or lock files are left behind")

def gate(cwd, env=None, data=None):
    tp = os.path.join(cwd, "t.jsonl"); open(tp, "w").write("")       # empty transcript (no code edits)
    p = subprocess.run([sys.executable, VGATE], input=json.dumps(dict({"transcript_path": tp}, **(data or {}))),
                       capture_output=True, text=True, cwd=cwd, env=env_for(dict({"FABLE_STRICT": "1"}, **(env or {}))))
    try:
        return p.returncode, json.loads(p.stdout) if p.stdout.strip() else None
    except ValueError:
        return p.returncode, "unparseable"

# Stop-hook integration: an OPEN ledger should trip the gate (strict: block)
d2 = tempfile.mkdtemp()
run(["create", "--goal", "A::x", "--goal", "V::verify"], d2)   # 2 pending goals
rc, j = gate(d2)
check(rc == 0 and isinstance(j, dict) and j.get("decision") == "block" and "goal" in j.get("reason", ""),
      "Stop gate blocks while goals are open")

# the ledger path must not fork with the shell's cwd (the Bash tool keeps its cwd across calls)
d3 = tempfile.mkdtemp()
os.makedirs(os.path.join(d3, "src", "deep"))
rc, o = run(["create", "--goal", "A::x", "--goal", "V::verify"], d3, {"CLAUDE_PROJECT_DIR": d3})
sub = os.path.join(d3, "src", "deep")
rc, o = run(["status"], sub, {"CLAUDE_PROJECT_DIR": d3})
check(rc == 0 and "0/2" in o, "CLAUDE_PROJECT_DIR anchors the ledger from a subdirectory")
rc, o = run(["create", "--goal", "Z::z"], sub, {"CLAUDE_PROJECT_DIR": d3})
check(rc == 1 and not os.path.exists(os.path.join(sub, ".fable")), "create from a subdirectory does not start a second ledger")
if shutil.which("git"):
    d4 = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", d4], check=True)
    os.makedirs(os.path.join(d4, "pkg"))
    run(["create", "--goal", "A::x", "--goal", "V::verify"], d4)
    rc, o = run(["status"], os.path.join(d4, "pkg"))
    check(rc == 0 and "0/2" in o, "without CLAUDE_PROJECT_DIR the git toplevel anchors the ledger")
    rc, j = gate(os.path.join(d4, "pkg"))
    check(isinstance(j, dict) and j.get("decision") == "block", "the Stop gate finds the same ledger from the subdirectory")
rc, j = gate(d3, {"CLAUDE_PROJECT_DIR": d3})
check(isinstance(j, dict) and j.get("decision") == "block", "the Stop gate honors CLAUDE_PROJECT_DIR")

# a corrupt ledger is an error message, not a traceback, and the gate must not pass it
d5 = tempfile.mkdtemp()
os.makedirs(os.path.join(d5, ".fable"))
open(os.path.join(d5, ".fable", "goals.json"), "w").write('{"brief": "x", "goals": [{"id"')
rc, o = run(["status"], d5)
check(rc == 1 and "Traceback" not in o and "reset" in o, "corrupt ledger: status explains it instead of a traceback")
rc, j = gate(d5)
check(isinstance(j, dict) and j.get("decision") == "block", "corrupt ledger: strict Stop gate blocks")
rc, o = run(["reset"], d5)
check(rc == 0, "corrupt ledger: reset still discards it")

# a ledger whose goal entries are not goal dicts is just as corrupt as invalid JSON
for bad in ('{"goals": [{"id": "G001"}]}', '{"goals": [1]}'):
    d6 = tempfile.mkdtemp()
    os.makedirs(os.path.join(d6, ".fable"))
    open(os.path.join(d6, ".fable", "goals.json"), "w").write(bad)
    for cmd in (["status"], ["next"], ["checkpoint", "--id", "G001", "--evidence", "e"]):
        rc, o = run(cmd, d6)
        check(rc == 1 and "Traceback" not in o and "reset" in o, f"malformed goal entry {bad}: {cmd[0]} explains it instead of a traceback")

# concurrent checkpoints must not lose updates (the race is probabilistic, so run several rounds)
n = 16
lost = []
for rnd in range(4):
    d6 = tempfile.mkdtemp()
    run(["create"] + sum((["--goal", f"T{i}::t"] for i in range(n + 1)), []), d6)
    procs = [subprocess.Popen([sys.executable, GOALS, "checkpoint", "--id", f"G{i:03d}", "--status", "complete",
                               "--evidence", f"e{i}"], cwd=d6, env=env_for(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             for i in range(1, n + 1)]
    codes = [p.wait() for p in procs]
    rc, o = run(["status"], d6)
    if not (all(c == 0 for c in codes) and f"{n}/{n + 1} complete" in o):
        lost.append(rnd)
check(not lost, f"4 rounds of {n} parallel checkpoints all land (rounds that lost updates: {lost})")
check(sorted(os.listdir(os.path.join(d6, ".fable"))) == [".gitignore", "goals.json"], "no temp or lock files after parallel writers")

# a lock left by a killed process must not wedge the ledger forever
d7 = tempfile.mkdtemp()
run(["create", "--goal", "A::x", "--goal", "V::v"], d7)
lock = os.path.join(d7, ".fable", "goals.json.lock")
open(lock, "w").close()
old = time.time() - 3600
os.utime(lock, (old, old))
rc, o = run(["checkpoint", "--id", "G001", "--evidence", "e"], d7)
check(rc == 0 and "complete" in o, "a stale lock file is broken")

# output glyphs must not crash a non-UTF-8 stdout after the ledger was already saved
d8 = tempfile.mkdtemp()
rc, o = run(["create", "--goal", "A::x"], d8, {"PYTHONIOENCODING": "ascii"})
check(rc == 0 and os.path.exists(os.path.join(d8, ".fable", "goals.json")), "create survives an ASCII stdout")
rc, o = run(["status"], d8, {"PYTHONIOENCODING": "ascii"})
check(rc == 0, "status survives an ASCII stdout")

# a blocked goal means the task is not done
d9 = tempfile.mkdtemp()
run(["create", "--goal", "A::x", "--goal", "V::v"], d9)
run(["checkpoint", "--id", "G001", "--status", "blocked", "--note", "waiting on the user"], d9)
run(["checkpoint", "--id", "G002", "--status", "blocked", "--note", "same"], d9)
rc, o = run(["status"], d9)
check("NOT done" in o, "status: an all-blocked ledger is NOT done")
rc, o = run(["create", "--goal", "Z::z"], d9)
check(rc == 1 and "force" in o, "create does not silently replace a ledger that has blocked goals")
rc, j = gate(d9)
check(isinstance(j, dict) and j.get("decision") == "block" and "blocked" in j.get("reason", ""),
      "Stop gate blocks on blocked goals and says so")

# a fork must be visible: create names the ledger it wrote, a bad CLAUDE_PROJECT_DIR is called out
d10 = tempfile.mkdtemp()
rc, o = run(["create", "--goal", "A::x"], d10)
check(os.path.join(os.path.realpath(d10), ".fable", "goals.json") in os.path.realpath(o) or os.path.join(d10, ".fable", "goals.json") in o,
      "create prints the ledger path it wrote")
rc, o = run(["status"], d10, {"CLAUDE_PROJECT_DIR": "/nonexistent-dir-for-fable"})
check("CLAUDE_PROJECT_DIR" in o and "not a directory" in o, "an invalid CLAUDE_PROJECT_DIR is reported, not silently ignored")

# a slow holder whose lock was broken must not delete the new holder's lock when it finishes
import importlib.util
d11 = tempfile.mkdtemp()
os.environ["CLAUDE_PROJECT_DIR"] = d11
spec = importlib.util.spec_from_file_location("goals_under_test", GOALS)
goals = importlib.util.module_from_spec(spec); spec.loader.exec_module(goals)
del os.environ["CLAUDE_PROJECT_DIR"]
holder_a = goals.locked(create=True); holder_a.__enter__()
old = time.time() - 40
os.utime(goals.LOCK, (old, old))
holder_b = goals.locked(create=True); holder_b.__enter__()          # breaks A's stale lock, takes its own
holder_a.__exit__(None, None, None)                                # A finishes late
check(os.path.exists(goals.LOCK), "a late holder does not remove the lock that now belongs to someone else")
holder_b.__exit__(None, None, None)
check(not os.path.exists(goals.LOCK), "the rightful holder still removes its own lock")

# the ledger directory ignores itself, so a user's repository never shows it in git status
d12 = tempfile.mkdtemp()
if shutil.which("git"):
    subprocess.run(["git", "init", "-q", d12], check=True)
    rc, o = run(["create", "--goal", "A::x", "--goal", "V::verify"], d12)
    gi = os.path.join(d12, ".fable", ".gitignore")
    check(rc == 0 and os.path.exists(gi) and open(gi).read().strip() == "*", "create writes .fable/.gitignore containing '*'")
    st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=d12, capture_output=True, text=True).stdout
    check(st == "", f"git status shows nothing from .fable (got {st!r})")
    rc, o = run(["checkpoint", "--id", "G001", "--evidence", "e"], d12)
    st = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=d12, capture_output=True, text=True).stdout
    check(rc == 0 and st == "", "git status stays clean after later writes")
# an existing .gitignore is the user's; create must not overwrite it
d13 = tempfile.mkdtemp()
os.makedirs(os.path.join(d13, ".fable"))
open(os.path.join(d13, ".fable", ".gitignore"), "w").write("custom\n")
rc, o = run(["create", "--goal", "A::x"], d13)
check(rc == 0 and open(os.path.join(d13, ".fable", ".gitignore")).read() == "custom\n", "an existing .fable/.gitignore is left alone")

print()
print("ALL PASS" if fails == 0 else f"{fails} TEST(S) FAILED")
sys.exit(1 if fails else 0)
