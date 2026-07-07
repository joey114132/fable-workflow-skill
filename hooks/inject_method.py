#!/usr/bin/env python3
"""UserPromptSubmit hook — deterministically inject the fable-workflow method on
non-trivial tasks, so the discipline fires every time instead of relying on the model
to auto-trigger the skill. Trivial prompts and plain questions get nothing.

stdout is added to the model's context by Claude Code; exit 0 always (never blocks a prompt).
"""
import sys, json, re

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return 0
    low = prompt.lower()

    # Plain question / explanation → not a build task, stay silent.
    if re.match(r"^\s*(what|why|how|who|when|where|explain|define|tell me|show me|list|summar)", low):
        return 0

    # Non-trivial build/change signals, or a long multi-step request.
    nontrivial = re.search(
        r"\b(build|implement|create|add|write|fix|debug|refactor|design|migrate|integrate|"
        r"optimi[sz]e|architect|scaffold|feature|endpoint|pipeline|schema|deploy|set up)\b", low)
    if not (nontrivial or len(prompt) > 280):
        return 0  # ponytail: crude signal; tune the verb list if it over/under-fires

    print(
        "[fable-workflow] Non-trivial task — apply the method: "
        "(1) surface the UNKNOWNS this request leaves open (pick sensible defaults with reasons "
        "if you can't ask); (2) build the smallest thing that could work; "
        "(3) VERIFY — exercise the result (run it / check the output), don't just assert it works; "
        "(4) log assumptions and report what you actually verified. Skip only if genuinely trivial."
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
