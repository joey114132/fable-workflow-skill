#!/usr/bin/env python3
"""Self-check for the enforcement hooks. Run: python3 hooks/test_hooks.py

Feeds synthetic stdin (and synthetic transcripts) to each hook and asserts behavior. The
transcript shape (assistant.message.content[tool_use], user prompts as string content, tool
results with toolUseResult) matches real Claude Code transcripts.
"""
import subprocess, sys, json, os, tempfile, pathlib, shutil

HERE = pathlib.Path(__file__).parent
SCRIPTS = HERE.parent / "scripts"

def run(script, payload, env_extra=None, cwd=None, raw=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "FABLE_STRICT", "FABLE_HOOK_LOG")}
    if env_extra:
        env.update(env_extra)
    data = raw if raw is not None else json.dumps(payload).encode("utf-8")
    p = subprocess.run([sys.executable, str(HERE / script)], input=data, capture_output=True, env=env, cwd=cwd)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")

def tool(name, inp):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}

def prompt(text, **extra):
    return dict({"type": "user", "message": {"role": "user", "content": text}}, **extra)

def tool_result():
    return {"type": "user", "toolUseResult": {"stdout": "ok"},
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": "ok"}]}}

def transcript(records, directory=None):
    fd, path = tempfile.mkstemp(suffix=".jsonl", dir=directory); os.close(fd)
    with open(path, "w") as f:
        for r in records:
            if isinstance(r, tuple):
                r = tool(*r)
            f.write(json.dumps(r) + "\n")
    return path

fails = 0
def check(cond, label):
    global fails
    print(("PASS " if cond else "FAIL ") + label)
    fails += 0 if cond else 1

def inject(text, env=None):
    return run("inject_method.py", {"prompt": text}, env)[1]

def gate(records, strict=False, cwd=None, env=None, extra=None):
    e = dict(env or {})
    if strict:
        e["FABLE_STRICT"] = "1"
    payload = dict({"transcript_path": transcript(records)}, **(extra or {}))
    rc, out, err = run("verify_gate.py", payload, e, cwd=cwd)
    try:
        j = json.loads(out) if out.strip() else None
    except ValueError:
        j = "unparseable"
    return rc, j, err

def jload(out):
    return json.loads(out) if out.strip() else None

def blocked(j):
    return isinstance(j, dict) and j.get("decision") == "block" and bool(j.get("reason"))

# --- inject_method: one task-matched line on EVERY prompt ---
out = inject("implement a rate limiter for our API")
check(out.startswith("[fable-workflow]") and out.count("\n") <= 1, "inject fires as a single tagged line on a non-trivial task")
check("EVIDENCE" in inject("what is a rate limiter?"), "inject fires on a plain question with the evidence rule")
check(inject("hi").strip().startswith("[fable-workflow]"), "inject fires even on a trivial prompt")
check("investigate" in inject("debug why the auth flow is broken and fix it"), "inject task-matches debugging -> investigate")
check("multi-step" in inject("build the endpoint, then add tests, then deploy"), "inject task-matches multi-step -> completion gate")
check(str(SCRIPTS / "goals.py") in inject("do it in three steps: parse, store, report"),
      "multi-step line carries the absolute goals.py path (plugin vars are not set in Bash)")

# question rung runs before the build nouns
check("EVIDENCE" in inject("how does the api work?"), "a question that mentions 'api' is still a question")
check("EVIDENCE" in inject("explain why the endpoint returns 500"), "'explain why the endpoint' is a question")
check("EVIDENCE" in inject("summary of the design"), "'summary' keeps the prefix match")
# requests are not questions
for text in ("can you write a parser for this", "whatever, just fix it", "listen, add a retry to the client",
             "do the refactor of the auth module", "should we add caching to the loader"):
    check("EVIDENCE" not in inject(text), f"a request is not a question: {text!r}")
# keyword misroutes
check("investigate" not in inject("write error handling for the parser"), "'error handling' feature is not a debug task")
check("multi-step" not in inject("if the flag is set then retry"), "a single 'then' is not multi-step")
# the plugin's own evals: a trivial fix gets no ceremony, a fact question gets the evidence rule,
# an explicit interview request does not tell the model to build
o = inject("Fix the typo in this line. The variable is called `total` everywhere else in the file.\n\nprint(f\"Order total: {totl:.2f}\")")
check(o.startswith("[fable-workflow]") and "decisions" not in o and "UNKNOWNS" not in o and "no questions" in o,
      "a one-line typo fix gets the no-ceremony line, not the open-decisions line")
check("EVIDENCE" in inject("Quick one for a deploy runbook I'm finishing: which Node.js release line is the current LTS, "
                           "and what's the default value of `server.requestTimeout`? I'll paste your answer straight in."),
      "a fact question that does not start with a question word still gets the evidence rule")
check("EVIDENCE" not in inject("Build the reminder feature for us. What database should it use?"),
      "a build request that ends in a question is still a build request")
o = inject("I want to add a notification system. Before you build anything, interview me about it.")
check("interview" in o and "then run it" not in o, "an explicit interview request gets the interview line, not the build line")
# inflected and compound fault words used to fall through to the neutral line
for text in ("Debugging the gripper dropout", "Investigating why j1 spins", "The motor failure happens on boot",
             "the node threw an exception", "Why does the build fail?", "it doesn't work", "segfault in the driver",
             "the gripper is not working", "got a stack trace from the planner",
             "fix the flaky test in the parser", "the CI job is flaky since Monday"):
    check("investigate" in inject(text), f"inflected fault word routes to investigate: {text!r}")
for text in ("write exception handling for the parser", "add a failover path to the client", "implement a failsafe stop"):
    check("investigate" not in inject(text), f"a feature that names a fault word is not a debug task: {text!r}")
# a question that is followed by an instruction is a build request
check("EVIDENCE" not in inject("What does the parser do? Add a test for it."),
      "a leading question followed by a build sentence is not only a question")
# Hangul-adjacent keywords (\b does not work next to Hangul particles)
for text in ("error를 고쳐줘", "버그 고쳐줘", "왜 안돼?", "crash가 나요"):
    check("investigate" in inject(text), f"Korean/Hangul-adjacent fault routes to investigate: {text!r}")
check("build" in inject("로그인 페이지 만들어줘"), "Korean build verb routes to build")
# the default line must not tell a confirmation to build or to surface unknowns
for text in ("continue", "ok", "계속", "네 해주세요", "/compact"):
    o = inject(text)
    check(o.startswith("[fable-workflow]") and o.count("\n") <= 1 and "UNKNOWNS" not in o and "build" not in o,
          f"confirmation/slash command gets the neutral line: {text!r}")
check("build" not in inject("see https://x.com/open-trading-api"), "a URL substring does not count as a build signal")

# robustness: exit 0 always, never a traceback
rc, out, err = run("inject_method.py", {"prompt": "debug this"}, {"PYTHONIOENCODING": "cp949"})
check(rc == 0 and out.startswith("[fable-workflow]"), "inject survives a non-UTF-8 stdout (cp949)")
for label, raw in (("null", b"null"), ("a list", b"[1]"), ("a non-string prompt", b'{"prompt": ["a"]}'),
                   ("non-UTF-8 bytes", b'{"prompt": "fix \xff\xfe bug"}'), ("garbage", b"{")):
    rc, out, err = run("inject_method.py", None, raw=raw)
    check(rc == 0 and "Traceback" not in err, f"inject exits 0 on {label} input")
rc, out, _ = run("inject_method.py", None, raw=b'{"prompt": "fix \xff\xfe bug"}')
check(out.startswith("[fable-workflow]"), "inject still fires when the prompt has undecodable bytes")

# --- verify_gate ---
rc, j, _ = gate([("Write", {"file_path": "/x/foo.py"})], strict=True)
check(rc == 0 and blocked(j) and "verify" in j["reason"].lower(), "strict gate BLOCKS edited-but-unrun code (decision block + reason on stdout)")
rc, j, err = gate([("Write", {"file_path": "/x/foo.py"})])
check(rc == 0 and isinstance(j, dict) and "systemMessage" in j and "decision" not in j and "verify" in j["systemMessage"].lower(),
      "advisory gate shows a systemMessage and does not block (stderr alone is invisible at exit 0)")
rc, j, _ = gate([("Edit", {"file_path": "/x/foo.py"}), ("Bash", {"command": "python foo.py"})], strict=True)
check(rc == 0 and j is None, "gate passes when code was run after editing")
rc, j, _ = gate([("Write", {"file_path": "/x/README.md"})], strict=True)
check(rc == 0 and j is None, "gate ignores non-code (docs) edits")
rc, j, _ = gate([("Write", {"file_path": "/x/foo.py"})], strict=True, extra={"stop_hook_active": True})
check(rc == 0 and isinstance(j, dict) and "decision" not in j and "letting stop through" in j.get("systemMessage", ""),
      "stop_hook_active: no second block, but the bypass is visible")
rc, j, _ = gate([("Edit", {"file_path": "/x/foo.py"}), ("Bash", {"command": "pytest"})], strict=True, extra={"stop_hook_active": True})
check(rc == 0 and j is None, "stop_hook_active: a condition that has resolved stays silent")
rc, j, _ = gate([("Write", {"file_path": "/x/FOO.PY"})], strict=True)
check(blocked(j), "extension check is case-insensitive")
rc, j, _ = gate([("Edit", {"file_path": "/x/a.py"}), ("PowerShell", {"command": "python a.py"})], strict=True)
check(j is None, "a PowerShell run counts as running the code")
rc, j, _ = gate([("Edit", {"file_path": "/x/a.py"}), ("Bash", {"command": "ls"})], strict=True)
check(blocked(j), "a read-only Bash call (ls) is not verification")
rc, j, _ = gate([("Edit", {"file_path": "/x/a.py"}), ("Bash", {"command": "cd /x && git status | head"})], strict=True)
check(blocked(j), "a chain of read-only segments is not verification")
rc, j, _ = gate([("Edit", {"file_path": "/x/a.py"}), ("Bash", {"command": "cd /x && pytest -q"})], strict=True)
check(j is None, "'cd x && pytest' counts as verification")
rc, j, _ = gate([("Edit", {"file_path": "/x/a.py"}), ("Bash", {"command": "git commit -m x"})], strict=True)
check(j is None, "a non-read-only git subcommand counts as a run")

# read-only commands whose text contains operators inside quotes or heredocs are not runs
EDIT = ("Edit", {"file_path": "/x/a.py"})
for cmd in ('rg "foo|bar" src', 'grep -E "a|b" x.py', 'grep -n "foo\\|bar" a.py', 'echo "a | b"', 'ls "a;b"',
            "git -C /x status", "git --no-pager diff", "cat x 2>&1", "ls &> /dev/null", "FOO=1 ls", "cat <<EOF > a.py\nimport os\nEOF",
            'grep "unterminated x'):
    rc, j, _ = gate([EDIT, ("Bash", {"command": cmd})], strict=True)
    check(blocked(j), f"read-only command is not verification: {cmd!r}")
for cmd in ("python3 - <<EOF\nprint(1)\nEOF", "FOO=1 pytest -q", "git -C /x commit -m y", "ls | python3 x.py", "pytest 2>&1 | tail",
            'echo "a|b" && pytest', 'grep ";" x.py\npytest'):
    rc, j, _ = gate([EDIT, ("Bash", {"command": cmd})], strict=True)
    check(j is None, f"command that runs code is verification: {cmd!r}")

# user records the system writes mid-turn are not new prompts
for text in ("<task-notification>done</task-notification>", "<local-command-stdout>x</local-command-stdout>",
             "<system-reminder>x</system-reminder>"):
    rc, j, _ = gate([prompt("go"), EDIT, prompt(text)], strict=True)
    check(blocked(j), f"system-written user record does not clear the turn: {text[:22]!r}")
interrupt = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "[Request interrupted by user]"}]}}
rc, j, _ = gate([prompt("go"), EDIT, interrupt], strict=True)
check(blocked(j), "an interrupt marker does not clear the turn")
rc, j, _ = gate([prompt("go"), EDIT, {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "[Image #1] what is this"}]}}], strict=True)
check(j is None, "a real prompt that starts with a bracket still starts a new turn")

# a blind gate says so
rc, out, _ = run("verify_gate.py", {"transcript_path": "/nonexistent.jsonl"}, {"FABLE_STRICT": "1"})
check(rc == 0 and blocked(jload(out)) and "transcript" in out, "an unreadable transcript is reported, not treated as nothing to verify")
rc, out, _ = run("verify_gate.py", {"transcript_path": None}, {"FABLE_STRICT": "1"})
check(rc == 0 and "transcript" in out, "a missing transcript_path is reported")
# a pathologically nested transcript line must not abort the judgement of the rest
tp = transcript([prompt("go"), EDIT])
with open(tp, "a") as f:
    f.write("[" * 3000 + "]" * 3000 + "\n")
rc, out, _ = run("verify_gate.py", {"transcript_path": tp}, {"FABLE_STRICT": "1"})
check(rc == 0 and blocked(jload(out)), "a deeply nested transcript line is skipped, the edit is still judged")
# a crash is shown, not swallowed
gone = tempfile.mkdtemp()
p = subprocess.run(["bash", "-c", f'cd {gone} && rmdir {gone} && exec {sys.executable} {HERE / "verify_gate.py"}'],
                   input=json.dumps({"transcript_path": transcript([])}).encode(), capture_output=True)
check(p.returncode == 0 and b"NOT checked" in p.stdout, "a crash in the gate is announced in a systemMessage")

# FABLE_STRICT parsing and the extension list
for val in ("1", "true", "YES", "on"):
    rc, j, _ = gate([("Write", {"file_path": "/x/foo.py"})], env={"FABLE_STRICT": val})
    check(blocked(j), f"FABLE_STRICT={val} enforces")
for val in ("0", "false", ""):
    rc, j, _ = gate([("Write", {"file_path": "/x/foo.py"})], env={"FABLE_STRICT": val})
    check(isinstance(j, dict) and "decision" not in j and "unrecognised" not in j["systemMessage"], f"FABLE_STRICT={val!r} is advisory without a complaint")
rc, j, _ = gate([("Write", {"file_path": "/x/foo.py"})], env={"FABLE_STRICT": "banana"})
check(isinstance(j, dict) and "decision" not in j and "unrecognised" in j["systemMessage"], "an unrecognised FABLE_STRICT value is called out")
for ext in (".mjs", ".cjs", ".bash", ".zsh", ".ps1", ".cs"):
    rc, j, _ = gate([("Write", {"file_path": "/x/foo" + ext})], strict=True)
    check(blocked(j), f"{ext} edits arm the gate")

# the gate judges the current turn, not the whole session
rc, j, _ = gate([prompt("fix it"), ("Edit", {"file_path": "/x/a.py"}), prompt("unrelated: what is a PID loop?")], strict=True)
check(j is None, "an edit from an earlier turn does not block a later unrelated turn")
rc, j, _ = gate([prompt("earlier"), ("Edit", {"file_path": "/x/a.py"}), ("Bash", {"command": "pytest"}),
                 prompt("again"), ("Edit", {"file_path": "/x/b.py"})], strict=True)
check(blocked(j), "an unrun edit inside the current turn still blocks")
rc, j, _ = gate([prompt("go"), ("Edit", {"file_path": "/x/a.py"}), tool_result()], strict=True)
check(blocked(j), "a tool_result record does not start a new turn")
rc, j, _ = gate([prompt("go"), ("Edit", {"file_path": "/x/a.py"}), prompt("hook noise", isMeta=True)], strict=True)
check(blocked(j), "a meta user record does not start a new turn")

# ledger: corrupt/unreadable must not open the gate; path must not depend on cwd
d = tempfile.mkdtemp()
os.makedirs(os.path.join(d, ".fable"))
ledger = os.path.join(d, ".fable", "goals.json")
open(ledger, "w").write('{"brief": "x", "goals": [{"id"')
rc, j, _ = gate([], strict=True, cwd=d)
check(blocked(j) and "goals.json" in j["reason"], "a corrupt ledger blocks under FABLE_STRICT=1 instead of silently passing")
rc, j, _ = gate([], cwd=d)
check(isinstance(j, dict) and "systemMessage" in j, "a corrupt ledger is reported in advisory mode too")
open(ledger, "w").write(json.dumps({"brief": "x", "goals": [{"id": "G001", "status": "complete"}]}))
rc, j, _ = gate([], strict=True, cwd=d)
check(j is None, "a fully complete ledger passes")
open(ledger, "w").write(json.dumps({"brief": "x", "goals": [{"id": "G001", "status": "blocked", "evidence": "needs the user"}]}))
rc, j, _ = gate([], strict=True, cwd=d)
check(blocked(j) and "blocked" in j["reason"], "a blocked goal is not done")
open(ledger, "w").write(json.dumps({"brief": "x", "goals": [{"id": "G001", "status": "pending"}]}))
os.makedirs(os.path.join(d, "sub"))
rc, j, _ = gate([], strict=True, cwd=os.path.join(d, "sub"), env={"CLAUDE_PROJECT_DIR": d})
check(blocked(j) and "goal" in j["reason"], "ledger is found via CLAUDE_PROJECT_DIR when the shell sits in a subdirectory")
if shutil.which("git"):
    subprocess.run(["git", "init", "-q", d], check=True)
    rc, j, _ = gate([], strict=True, cwd=os.path.join(d, "sub"), extra={"cwd": os.path.join(d, "sub")})
    check(blocked(j) and "goal" in j["reason"], "ledger is found via the git toplevel when CLAUDE_PROJECT_DIR is unset")

# robustness
for label, raw in (("null", b"null"), ("a list", b"[1]"), ("garbage", b"{")):
    rc, out, err = run("verify_gate.py", None, {"FABLE_STRICT": "1"}, raw=raw)
    check(rc == 0 and "Traceback" not in err, f"gate exits 0 on {label} input")
home = tempfile.mkdtemp()
t = transcript([("Write", {"file_path": "/x/foo.py"})], directory=home)
rc, out, _ = run("verify_gate.py", {"transcript_path": "~/" + os.path.basename(t)}, {"FABLE_STRICT": "1", "HOME": home})
check(blocked(json.loads(out) if out.strip() else None), "transcript_path with ~ is expanded")

# --- hooks.json ---
hooks = json.load(open(HERE / "hooks.json"))
for ev in hooks["hooks"].values():
    for grp in ev:
        for h in grp["hooks"]:
            script = h["command"].split("${CLAUDE_PLUGIN_ROOT}/")[1].split('"')[0]
            check((HERE.parent / script).exists(), f"hooks.json script exists: {script}")

print()
print("ALL PASS" if fails == 0 else f"{fails} TEST(S) FAILED")
sys.exit(1 if fails else 0)
