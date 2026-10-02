# fable-workflow-skill

A portable agent skill (`SKILL.md` plus reference files) that ports a Fable-style working
method onto any model, with optional Claude Code plugin hooks. No build step. The only code is
small stdlib-only Python (hooks and `scripts/goals.py`) with self-tests.

## Layout
- `SKILL.md` is the entry point and the canonical method. It must stay at or under 120 lines, frontmatter included.
- `prompts.md`, `standing-orders.md`, `loop-engineering.md`, `completion-gate.md` hold the detail SKILL.md points to.
- `scripts/goals.py` (with `test_goals.py`) is the completion-gate ledger.
- `hooks/` has the plugin hooks: `inject_method.py` (UserPromptSubmit), `verify_gate.py` (Stop), `hooks.json`, `test_hooks.py`.
- `integrations/` has `AGENTS.md` and `cursor/fable-workflow.mdc`, each a condensed copy of the method.
- `evals/` has the claude-plugin-eval cases. Results land in `evals/results/` (gitignored).
- `benchmark/RESULTS.md` is the cross-model A/B pilot. `assets/banner.png` is the banner.
- `README.md` and `README.ko.md` mirror each other.
- `install.sh` copies SKILL.md, the reference .md files and `scripts/goals.py` into a skills dir. Hooks are plugin-only.

## Editing rules
- Keep SKILL.md short and put detail in the reference files. Every reference file needs a pointer from SKILL.md.
- When the method changes, update `integrations/AGENTS.md` and `integrations/cursor/fable-workflow.mdc` too.
- Any README change goes into both languages. A new language means `README.<lang>.md` plus the switcher line in every README.
- Benchmark numbers come from a small pilot. If you rerun, update the caveats, not just the table.
- Tests must pass: `python3 hooks/test_hooks.py` and `python3 scripts/test_goals.py`.
- The SKILL.md frontmatter key is `allowed-tools` (hyphenated; `allowed_tools` is silently ignored). It pre-approves tools rather than restricting them, so list only read and search tools (Read, Grep, Glob, WebSearch, WebFetch).

## Evals
Run `claude plugin eval . --no-publish`. Add `--allow-tools WebSearch WebFetch` if a case needs them.
Bash cannot be granted without socat. Do not edit the cases to make them pass.

## Versioning
Bump `version` in `.claude-plugin/plugin.json` and in the `.claude-plugin/marketplace.json` entry together.
A pinned version is what ships updates, so users on an old version see nothing until it changes.
`claude plugin tag` checks that the two agree.
