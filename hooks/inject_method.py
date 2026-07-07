#!/usr/bin/env python3
"""UserPromptSubmit hook — inject ONLY the smallest matching discipline on a non-trivial task
(token-lean: one short line, not a fixed blob; task-matched like fablize's router). Trivial
prompts and plain questions get nothing. stdout is added to context; exit 0 always.

Set env FABLE_HOOK_LOG=<path> to record each firing (opt-in debug; off by default).
"""
import sys, json, re, os

def _firelog(name):
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

def discipline(low):
    """Return the single most-relevant one-liner for this task (smallest matching discipline)."""
    if re.search(r"\b(debug|bug|error|traceback|crash|failing|root cause|investigate|regress)\b", low):
        return "investigate — reproduce, compete 3+ hypotheses, trace the full causal chain, verify before & after."
    if re.search(r"\b(steps?|stories|phases?|milestones?|then|and then|multiple|several)\b", low):
        return "multi-step — decompose with the completion gate (goals.py): evidence per goal, final goal verifies."
    if re.search(r"\b(html|svg|chart|game|ui|render|page|component|app|endpoint|api|script|function|migrat)\w*", low):
        return "build then VERIFY — run it / write the smallest check, observe the output; don't assert it works."
    return "surface the UNKNOWNS this leaves open (sensible defaults if you can't ask), then build and verify."

def main():
    _firelog("UserPromptSubmit/inject_method")
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    p = (data.get("prompt") or "").strip()
    if not p:
        return 0
    low = p.lower()
    if re.match(r"^\s*(what|why|how|who|when|where|explain|define|tell me|show me|list|summar)", low):
        return 0  # plain question / explanation — not a build task
    nontrivial = re.search(
        r"\b(build|implement|create|add|write|fix|debug|refactor|design|migrate|integrate|"
        r"optimi[sz]e|architect|scaffold|feature|endpoint|pipeline|schema|deploy|set up)\b", low)
    if not (nontrivial or len(p) > 280):
        return 0
    print("[fable-workflow] " + discipline(low))  # ponytail: one matched line; tune the regexes if it mis-routes
    return 0

if __name__ == "__main__":
    sys.exit(main())
