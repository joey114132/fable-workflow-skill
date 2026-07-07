# Completion Gate — multi-story work that can't fake "done"

For work that's **2+ sequential stories** (or a long autonomous run), decompose it and complete
one story at a time, producing evidence as you go. The ledger (`scripts/goals.py`, a plugin
feature) refuses a groundless "done": `complete` needs non-empty evidence, and the final
(verification) story needs a verify command **and** its result. State lives in
`./.fable/goals.json` — resume any time with `status`.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/goals.py create --brief "<summary>" \
  --goal "title::verifiable objective" --goal "..." --goal "verify::run the checks"
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/goals.py next          # activate a story + handoff
# ... work that story only ...
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/goals.py checkpoint --id G001 --status complete \
  --evidence "<concrete evidence>"
# final story = verification gate:
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/goals.py checkpoint --id G00N --status complete \
  --evidence "..." --verify-cmd "<command>" --verify-evidence "<result>"
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/goals.py status        # resume / see progress
```

Rules
- `complete` requires non-empty `--evidence`; the engine refuses otherwise (exit 2).
- The **last** goal is the verification story — it cannot complete without `--verify-cmd` and `--verify-evidence`.
- Stuck? `--status blocked` with a note, and report it — a *blocked and reported* goal is an honest stop; a pending/active one is not.
- The `Stop` verify gate reads `.fable/goals.json`: while any goal is pending/active it flags "not done" (advisory; `FABLE_STRICT=1` blocks the stop).
- Single-step tasks don't need this — skip it (YAGNI).
