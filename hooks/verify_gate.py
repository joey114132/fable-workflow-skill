#!/usr/bin/env python3
"""Stop hook: the teeth for the Verify step. If code was written or edited in THIS turn but no
command ran after the last edit, the Verify step was skipped ("edited but never run"). An open
goals ledger (.fable/goals.json) also means the task is not done.

- Default: advisory. Prints {"systemMessage": ...} so the user sees the warning; exit 0, no block.
  (Plain stderr at exit 0 goes to the debug log only, so it would be invisible.)
- FABLE_STRICT=1: enforce. Prints {"decision": "block", "reason": ...}, which keeps Claude from
  stopping and feeds the reason back to the model so it must verify before finishing.

Exit 0 always. Heuristic and conservative on purpose (fablize's early-stop hook warns these
misfire); the transcript walk is schema-tolerant so it survives transcript-format changes.
"""
import sys, json, os, re, shlex, subprocess

# ponytail: executable languages only. .html/.css/.sql/.vue are checked in a browser or a database, not by a
# Bash run, so they would only make the gate cry wolf. Edits made through Bash (sed -i, cat > f) are not seen.
CODE_EXT = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".c", ".cc", ".cpp",
            ".h", ".sh", ".bash", ".zsh", ".ps1", ".cs", ".kt", ".swift", ".php", ".lua")
RUNNERS = ("Bash", "PowerShell")   # PowerShell replaces Bash on Windows without Git Bash
# ponytail: first word of each shell segment, after shlex tokenizing. A command that only looks around is
# not a "run"; anything else counts. Add words here if a read-only tool slips through.
READONLY = {"ls", "cat", "pwd", "echo", "head", "tail", "grep", "rg", "find", "wc", "which", "cd", "true", "type"}
GIT_READONLY = {"status", "diff", "log", "show"}
GIT_OPT_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
# heredoc body (only when its terminator exists), so lines of file content are not read as commands
HEREDOC = re.compile(r"(?<!<)(<<-?\s*(['\"]?)(\w+)\2[^\n]*)(?:\n.*?)?\n[ \t]*\3[ \t]*(?=\n|\Z)", re.S)
OPERATORS = set(";&|\n")
REDIRECT_AMP = re.compile(r"\d*>&\d*-?|&>>?")   # 2>&1 and &> are redirections, not the & operator
STRICT_ON = {"1", "true", "yes", "on"}
STRICT_OFF = {"", "0", "false", "no", "off"}
# user records the system writes (background task done, local command output, hook noise, Esc), not prompts
SYSTEM_TEXT = ("<task-notification", "<local-command", "<system-reminder", "[Request interrupted")

def _firelog(name):
    """Record a firing if env FABLE_HOOK_LOG is set (opt-in debug; off by default)."""
    path = os.environ.get("FABLE_HOOK_LOG")
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        from datetime import datetime, timezone
        with open(path, "a") as f:
            f.write(datetime.now(timezone.utc).isoformat(timespec="seconds") + f" {name} fired\n")
    except Exception:
        pass

def walk_tools(obj, out):
    """Recursively collect (tool_name, input_dict) in document order, tolerant of schema."""
    if isinstance(obj, dict):
        name = obj.get("name")
        if isinstance(name, str) and (obj.get("type") == "tool_use" or "input" in obj):
            out.append((name, obj.get("input") if isinstance(obj.get("input"), dict) else {}))
        for v in obj.values():
            walk_tools(v, out)
    elif isinstance(obj, list):
        for v in obj:
            walk_tools(v, out)

def is_human_prompt(rec):
    """A real user prompt: not a tool_result echo and not hook/system meta."""
    if not isinstance(rec, dict) or rec.get("type") != "user" or rec.get("isMeta") or "toolUseResult" in rec:
        return False
    msg = rec.get("message")
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, str):
        return not content.lstrip().startswith(SYSTEM_TEXT)
    if not isinstance(content, list) or any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
        return False
    texts = [b.get("text") for b in content if isinstance(b, dict) and b.get("type") == "text"]
    if any(isinstance(t, str) and t.lstrip().startswith(SYSTEM_TEXT) for t in texts):
        return False
    return any(isinstance(b, dict) and b.get("type") in ("text", "image") for b in content)

def segments(command):
    """Split a shell command on unquoted ; & | and newlines. Non-POSIX mode keeps the quotes on a token,
    so a quoted ";" is not mistaken for an operator. Raises ValueError on an unbalanced quote."""
    lex = shlex.shlex(REDIRECT_AMP.sub(">", HEREDOC.sub(r"\1", command)), posix=False, punctuation_chars=";&|\n")
    lex.whitespace, lex.whitespace_split, lex.commenters = " \t\r", True, ""
    seg = []
    for tok in lex:
        if set(tok) <= OPERATORS:
            yield seg
            seg = []
        else:
            seg.append(tok)
    yield seg

def only_inspects(words):
    while words and re.match(r"[A-Za-z_]\w*=", words[0]):    # FOO=1 cmd
        words = words[1:]
    if not words or words[0] in READONLY:
        return True
    if words[0] != "git":
        return False
    i = 1
    while i < len(words) and words[i].startswith("-"):      # git -C dir / --no-pager status
        i += 2 if words[i] in GIT_OPT_WITH_ARG else 1
    return words[i:i + 1] != [] and words[i] in GIT_READONLY

def actually_runs(command):
    """False when every segment of the command only inspects (ls, cat, git status ...). A command that
    cannot be parsed (unbalanced quote) is not credited as a run: the gate then asks for a clean one."""
    try:
        return not all(only_inspects(seg) for seg in segments(command))
    except ValueError:
        return False

def _git_toplevel(cwd):
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True,
                             text=True, timeout=3).stdout.strip()
        return out or None
    except (OSError, subprocess.SubprocessError):
        return None

def ledger_paths(cwd):
    """Where a .fable/goals.json may live. scripts/goals.py anchors to CLAUDE_PROJECT_DIR, else the
    git toplevel, else cwd; the Bash tool does not see CLAUDE_PROJECT_DIR but this hook does, so
    check every anchor instead of guessing which one goals.py used."""
    roots = [os.environ.get("CLAUDE_PROJECT_DIR"), _git_toplevel(cwd), cwd]
    seen = []
    for r in roots:
        if r and os.path.join(r, ".fable", "goals.json") not in seen:
            seen.append(os.path.join(r, ".fable", "goals.json"))
    return [p for p in seen if os.path.exists(p)]

def main():
    _firelog("Stop/verify_gate")
    try:
        sys.stdin.reconfigure(errors="replace")
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0
    again = bool(data.get("stop_hook_active"))   # already continuing because of a stop hook (maybe not ours)
    tpath = data.get("transcript_path")
    tpath = os.path.expanduser(tpath) if isinstance(tpath, str) and tpath else None
    cwd = data.get("cwd") if isinstance(data.get("cwd"), str) and os.path.isdir(data.get("cwd")) else os.getcwd()

    tools = []
    readable = False
    if tpath:
        try:
            with open(tpath, encoding="utf-8", errors="replace") as f:
                readable = True
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        found = []
                        walk_tools(rec, found)
                    except (ValueError, RecursionError):   # a line nested too deep to read: skip it
                        continue
                    if is_human_prompt(rec):   # a new turn: earlier edits were already judged
                        tools.clear()
                    tools.extend(found)
        except OSError:
            readable = False

    edited_code = False
    ran_after_edit = False
    for name, inp in tools:
        if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            fp = str(inp.get("file_path") or inp.get("notebook_path") or "")
            if fp.lower().endswith(CODE_EXT):
                edited_code = True
                ran_after_edit = False       # reset: a later run must follow the LAST edit
        elif name in RUNNERS and edited_code and actually_runs(str(inp.get("command") or "")):
            ran_after_edit = True

    reasons = []
    if not readable:
        reasons.append("transcript unreadable, cannot tell whether code was run")
    if edited_code and not ran_after_edit:
        reasons.append("code was edited but no command ran after the last edit (Verify step skipped)")

    # Completion gate: an open goals ledger means the task isn't done. A ledger we cannot read
    # must not silently open the gate, so that counts as not done too.
    for ledger in ledger_paths(cwd):
        try:
            with open(ledger, encoding="utf-8") as f:
                goals = json.load(f).get("goals", [])
            open_goals = [x for x in goals if x.get("status") in ("pending", "active", "blocked")]
            if open_goals:
                stuck = [x for x in open_goals if x.get("status") == "blocked"]
                ids = "; ".join(f"{x.get('id')}: {x.get('evidence')}" for x in stuck)
                note = f", {len(stuck)} of them blocked ({ids}): tell the user" if stuck else ""
                reasons.append(f"{len(open_goals)} of {len(goals)} goals in {ledger} are still open{note} (completion gate)")
        except Exception as e:
            reasons.append(f"could not read {ledger} ({type(e).__name__}), treat as NOT done")

    if reasons:
        flag = os.environ.get("FABLE_STRICT", "").strip().lower()
        strict = flag in STRICT_ON
        msg = ("[fable-workflow] Not done: " + "; ".join(reasons) +
               ". Verify/finish before stopping, or state why it isn't applicable.")
        if flag not in STRICT_ON | STRICT_OFF:
            msg += f" (FABLE_STRICT={flag!r} is unrecognised, so this is advisory; use 1 to enforce.)"
        if strict and again:   # the one block already went out: let the stop through, but say so
            msg = "[fable-workflow] Still not done after one block, letting stop through: " + msg.split("Not done: ", 1)[1]
        if strict and not again:
            print(json.dumps({"decision": "block", "reason": msg}))
        else:
            print(json.dumps({"systemMessage": msg}))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:   # a hook must never fail the user's turn, but a skipped check must be visible
        try:
            print(json.dumps({"systemMessage": f"[fable-workflow] verify_gate crashed ({type(e).__name__}); this turn was NOT checked."}))
        except Exception:
            pass
        sys.exit(0)
