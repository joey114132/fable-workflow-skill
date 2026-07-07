#!/usr/bin/env python3
"""Self-check for the enforcement hooks. Run: python3 hooks/test_hooks.py

Feeds synthetic stdin (and synthetic transcripts) to each hook and asserts behavior.
NOTE: the transcript is a plausible Claude Code shape; verify_gate walks it tolerantly, but
if the live transcript schema differs, adjust walk_tools — this test pins the *logic*.
"""
import subprocess, sys, json, os, tempfile, pathlib

HERE = pathlib.Path(__file__).parent

def run(script, payload, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, str(HERE / script)],
                       input=json.dumps(payload), capture_output=True, text=True, env=env)
    return p.returncode, p.stdout, p.stderr

def transcript(tools):
    fd, path = tempfile.mkstemp(suffix=".jsonl"); os.close(fd)
    with open(path, "w") as f:
        for name, inp in tools:
            f.write(json.dumps({"type": "assistant", "message": {
                "content": [{"type": "tool_use", "name": name, "input": inp}]}}) + "\n")
    return path

fails = 0
def check(cond, label):
    global fails
    print(("PASS " if cond else "FAIL ") + label)
    fails += 0 if cond else 1

# --- inject_method ---
rc, out, _ = run("inject_method.py", {"prompt": "implement a rate limiter for our API"})
check(rc == 0 and "fable-workflow" in out, "inject fires on a non-trivial task")
rc, out, _ = run("inject_method.py", {"prompt": "what is a rate limiter?"})
check(rc == 0 and out.strip() == "", "inject stays silent on a plain question")

# --- verify_gate ---
t = transcript([("Write", {"file_path": "/x/foo.py"})])
rc, _, err = run("verify_gate.py", {"transcript_path": t}, {"FABLE_STRICT": "1"})
check(rc == 2 and "verify" in err.lower(), "strict gate BLOCKS edited-but-unrun code")
rc, _, _ = run("verify_gate.py", {"transcript_path": t})
check(rc == 0, "advisory gate does not block (default)")
t = transcript([("Edit", {"file_path": "/x/foo.py"}), ("Bash", {"command": "python foo.py"})])
rc, _, _ = run("verify_gate.py", {"transcript_path": t}, {"FABLE_STRICT": "1"})
check(rc == 0, "gate passes when code was run after editing")
t = transcript([("Write", {"file_path": "/x/README.md"})])
rc, _, _ = run("verify_gate.py", {"transcript_path": t}, {"FABLE_STRICT": "1"})
check(rc == 0, "gate ignores non-code (docs) edits")
rc, _, _ = run("verify_gate.py", {"transcript_path": t, "stop_hook_active": True}, {"FABLE_STRICT": "1"})
check(rc == 0, "gate respects stop_hook_active guard")

print()
print("ALL PASS" if fails == 0 else f"{fails} TEST(S) FAILED")
sys.exit(1 if fails else 0)
