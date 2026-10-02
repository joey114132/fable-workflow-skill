#!/usr/bin/env python3
"""UserPromptSubmit hook: inject exactly one short line on EVERY prompt, matched to the task
(token-lean: one line, not a fixed blob). Questions get the answer-from-evidence rule; prompts
that match nothing (confirmations, slash commands) get that same neutral line, never a build
instruction. Rungs, first match wins: investigate, interview, evidence (questions), multi-step, small fix,
build, then the neutral evidence default. stdout is added to context; exit 0 always.

Set env FABLE_HOOK_LOG=<path> to record each firing (opt-in debug; off by default).
"""
import sys, json, re, os, shlex

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

def _w(words):
    """Word-bounded alternation. ASCII lookarounds instead of \\b: \\b does not fire between
    'error' and a Hangul particle ('error를'), because Hangul counts as a word character."""
    return r"(?<![a-z0-9_])(?:" + words + r")(?![a-z0-9_])"

URL = re.compile(r"https?://\S+")
# fail(ed|ing|ure) is spelled out so "failover" and "failsafe" stay features; "exception" needs ERROR_CONTEXT like "error"
FAULT = re.compile(_w(r"debug\w*|bugs?|traceback|stack ?trace|crash\w*|fail(?:s|ed|ing|ures?)?|broken|root cause|investigat\w*|regress\w*|segfault\w*|flak(?:y|iness)")
                   + r"|(?:n['’]t|not)\s+work(?:s|ed|ing)?(?![a-z0-9_])|error\s*:|버그|에러|오류|크래시|안\s?돼|안\s?되|실패|고장|떨려")
ERROR = re.compile(_w("errors?|exceptions?"))
ERROR_CONTEXT = re.compile(_w(r"fix|why|debug|getting|got|throws?|threw|thrown|raises?|raised") + r"|고쳐|고치|왜|해결")
QUESTION = re.compile(r"^\s*(?:" + _w(r"what|why|how|who|when|where|which|is|are|does|explain|define|tell me|show me|list|summar\w*")
                      + r"|무엇|왜|어떻게|어디|언제|누가)")
# a wh-clause that ends in "?" is a question even when the prompt opens with preamble ("Quick one for a
# runbook: which release is current?"), unless a sentence opens with a build verb ("Build X. What db?").
WH_QUESTION = re.compile(_w(r"what|what's|which|who|when|where|how (?:many|much|long|old)") + r"[^!?\n]*\?")
BUILD_REQUEST = re.compile(r"(?:^|[.!?:]\s+)(?:please\s+)?" + _w(r"build|implement|create|add|write|make|fix|refactor|design|integrate|set up|scaffold"))
INTERVIEW = re.compile(_w(r"interview me|grill me") + r"|인터뷰")
TRIVIAL = re.compile(_w(r"typos?|misspell\w*|one[- ]line|one[- ]liner") + r"|오타|한 줄")
STEPS = re.compile(_w(r"steps?|stories|phases?|milestones?|and then") + r"|단계|순서대로|그\s?다음")
BUILD = re.compile(_w(r"html|svg|chart|game|ui|render\w*|page|component|app|endpoint|api|script|function|migrat\w*"
                     r"|build|implement|create|add|write|make|fix|refactor|design|integrate|optimi[sz]e|architect"
                     r"|scaffold|deploy|set up|install") + r"|만들|구현|추가|고쳐|수정|리팩|설계|배포|설치")
GOALS_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "goals.py")

EVIDENCE = "answer from EVIDENCE, not recall — check the file/command/source, cite it, say 'unverified' if you can't."

def discipline(p):
    """Return the single most relevant one-liner for this prompt.
    ponytail: keyword rungs, first match wins; tune the regexes if it mis-routes, no scoring."""
    low = URL.sub(" ", p.lower())
    if FAULT.search(low) or (ERROR.search(low) and ERROR_CONTEXT.search(low)):
        return "investigate — reproduce, compete 3+ hypotheses, trace the full causal chain, verify before & after."
    if INTERVIEW.search(low):
        return "interview first — ask only the few questions whose answers would change the design, build nothing yet."
    if (QUESTION.search(low) or WH_QUESTION.search(low)) and not BUILD_REQUEST.search(low):
        return EVIDENCE   # before STEPS and BUILD: "how does the api work?" is a question
    if STEPS.search(low) or len(re.findall(_w("then"), low)) >= 2:
        # plugin path variables are not set in Bash, so hand the model the real path
        return f"multi-step — decompose with the completion gate (python3 {shlex.quote(GOALS_PY)}): evidence per goal, final goal verifies."
    if TRIVIAL.search(low):
        return "small fix — just make it and say what you checked; no unknowns list, no questions."
    if BUILD.search(low):
        return "build then VERIFY — name the open decisions first (ask when a wrong guess is costly, else state the assumption), then run it and show the output."
    return EVIDENCE   # neutral default: confirmations, slash commands, chatter

def main():
    _firelog("UserPromptSubmit/inject_method")
    try:
        sys.stdin.reconfigure(errors="replace")
        data = json.load(sys.stdin)
    except Exception:
        return 0
    p = data.get("prompt") if isinstance(data, dict) else None
    p = p.strip() if isinstance(p, str) else ""
    if not p:
        return 0
    # Claude Code reads hook stdout as text; the line has a non-ASCII dash, so pin the encoding
    sys.stdout.reconfigure(encoding="utf-8")
    print("[fable-workflow] " + discipline(p))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:   # a hook must never fail the user's prompt; stderr lands in the debug log
        print(f"inject_method: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)
