# fable-workflow-skill

A single portable agent skill (`SKILL.md`) that ports a Fable-style working method onto any
model. This repo is docs + one skill — there is no build step.

## Layout
- `SKILL.md` — the skill itself (the only file agents load). Keep it under ~120 lines.
- `prompts.md` — copy-paste prompt templates referenced by the skill.
- `integrations/` — adapters for other tools: `AGENTS.md` (Antigravity/Codex/Aider/Zed/…) and `cursor/fable-workflow.mdc`.
- `benchmark/RESULTS.md` — the cross-model A/B evaluation.
- `README.md` / `README.ko.md` — English + Korean. **Keep both in sync when editing.**
- `install.sh` — copies `SKILL.md` + `prompts.md` into a target `.claude/skills` dir.
- `assets/banner.png` — repo banner (user-supplied).

## Editing rules
- Edit the skill in `SKILL.md` in place; don't split it into more files.
- `SKILL.md` is canonical; `integrations/AGENTS.md` and `integrations/cursor/fable-workflow.mdc` carry a condensed copy — keep all three in sync when the method changes.
- Any change to one README must be mirrored in the other language.
- Benchmark numbers are from a small pilot — if you rerun, update the caveats too, don't
  just swap the table.

## Adding a README language
Add `README.<lang>.md` and update the language switcher line at the top of every README.
