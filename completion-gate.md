# Completion Gate — multi-story work that can't fake "done"

For work that's **2+ sequential stories** (or a long autonomous run), decompose it and complete
one story at a time, producing evidence as you go. The ledger (`scripts/goals.py`) refuses a
groundless "done": `complete` needs non-empty evidence, and the final (verification) story needs
a verify command **and** its result. State lives in `<project root>/.fable/goals.json` (the git toplevel, else the
current directory), so `status` finds it from any subdirectory and you can resume any time.

`<goals>` below stands for the exact command SKILL.md gives for the ledger, which is `python3`
plus the quoted absolute path of `scripts/goals.py`, quotes included. Claude Code fills that path
in only inside SKILL.md, and the plugin variables are not set in Bash, so copy the command from
SKILL.md and do not type a variable of your own.

```bash
<goals> create --brief "<summary>" \
  --goal "title::verifiable objective" --goal "..." --goal "verify::run the checks"
<goals> next          # activate a story + handoff
# ... work that story only ...
<goals> checkpoint --id G001 --status complete --evidence "<concrete evidence>"
# final story = verification gate:
<goals> checkpoint --id G00N --status complete \
  --evidence "..." --verify-cmd "<command>" --verify-evidence "<result>"
<goals> status        # resume / see progress
```

Rules
- `complete` requires non-empty `--evidence`; the engine refuses otherwise (exit 2).
- The **last** goal is the verification story. It cannot complete without `--verify-cmd` and `--verify-evidence`.
- Stuck? `--status blocked` with a note, and report it. A *blocked and reported* goal is an honest stop; a pending or active one is not.
- The `Stop` verify gate reads `.fable/goals.json`. While any goal is pending or active it flags "not done" (advisory; `FABLE_STRICT=1` blocks the stop).
- The engine checks only that the evidence strings are non-empty. They are self-reported, so write evidence you could be audited on, such as a command and its output or a `file:line`.
- In Claude Code, you can pair the gate with `/goal <one measurable end state>`, for example `pytest -q exits 0 and its output is in the transcript`. A separate evaluator model then decides when the work is done, not the worker.
- The evaluator reads the conversation and does not run commands, so word the `/goal` condition as something Claude's own output can show.
- Single-step tasks don't need this (YAGNI).
