#!/usr/bin/env python3
"""Self-check for the completion gate (goals.py) + its Stop-hook integration.
Run: python3 scripts/test_goals.py
"""
import subprocess, sys, os, json, tempfile, pathlib

HERE = pathlib.Path(__file__).parent
GOALS = str(HERE / "goals.py")
VGATE = str(HERE.parent / "hooks" / "verify_gate.py")

def run(args, cwd):
    p = subprocess.run([sys.executable, GOALS] + args, cwd=cwd, capture_output=True, text=True)
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

# Stop-hook integration: an OPEN ledger should trip the gate (strict → block)
d2 = tempfile.mkdtemp()
run(["create", "--goal", "A::x", "--goal", "V::verify"], d2)   # 2 pending goals
tp = os.path.join(d2, "t.jsonl"); open(tp, "w").write("")       # empty transcript (no code edits)
p = subprocess.run([sys.executable, VGATE], input=json.dumps({"transcript_path": tp}),
                   capture_output=True, text=True, cwd=d2, env=dict(os.environ, FABLE_STRICT="1"))
check(p.returncode == 2 and "goal" in (p.stdout + p.stderr).lower(),
      "Stop gate blocks while goals are open")

print()
print("ALL PASS" if fails == 0 else f"{fails} TEST(S) FAILED")
sys.exit(1 if fails else 0)
