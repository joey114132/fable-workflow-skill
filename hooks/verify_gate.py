#!/usr/bin/env python3
"""Stop hook — the teeth for the Verify step. If code was written/edited this session but
no command ran after the last edit, the Verify step was skipped ("edited but never run").

- Default: advisory — prints a reminder to stderr, exit 0 (does NOT block).
- FABLE_STRICT=1: enforce — exit 2 with the reason, which blocks the stop and feeds the
  reason back to the model so it must verify before finishing.

Heuristic and conservative on purpose (fablize's early-stop hook warns these misfire); the
transcript walk is schema-tolerant so it survives Claude Code transcript-format changes.
"""
import sys, json, os

CODE_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb",
            ".c", ".cc", ".cpp", ".h", ".sh", ".kt", ".swift", ".php", ".lua")

def walk_tools(obj, out):
    """Recursively collect (tool_name, input_dict) in document order — tolerant of schema."""
    if isinstance(obj, dict):
        name = obj.get("name")
        if isinstance(name, str) and (obj.get("type") == "tool_use" or "input" in obj):
            out.append((name, obj.get("input") if isinstance(obj.get("input"), dict) else {}))
        for v in obj.values():
            walk_tools(v, out)
    elif isinstance(obj, list):
        for v in obj:
            walk_tools(v, out)

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("stop_hook_active"):   # avoid loops: we already fired once
        return 0
    tpath = data.get("transcript_path")
    if not tpath or not os.path.exists(tpath):
        return 0

    tools = []
    try:
        with open(tpath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    walk_tools(json.loads(line), tools)
                except Exception:
                    continue
    except Exception:
        return 0

    edited_code = False
    ran_after_edit = False
    for name, inp in tools:
        if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            fp = str(inp.get("file_path") or inp.get("notebook_path") or "")
            if fp.endswith(CODE_EXT):
                edited_code = True
                ran_after_edit = False       # reset: a later run must follow the LAST edit
        elif name == "Bash" and edited_code:
            ran_after_edit = True

    if edited_code and not ran_after_edit:
        msg = ("[fable-workflow] Verify gate: code was edited this session but no command ran "
               "after the last edit — the Verify step wasn't done. Exercise it (run it / smallest "
               "check) before finishing, or state why verification isn't applicable.")
        if os.environ.get("FABLE_STRICT") == "1":
            print(msg, file=sys.stderr)
            return 2   # block the stop; reason goes back to the model
        print(msg, file=sys.stderr)  # advisory only
        return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
