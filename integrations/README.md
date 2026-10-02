# Integrations

The same method (`../SKILL.md`) packaged for other agent tools. Each adapter is one file you can copy on its own.

| Tool | File | Install into your project |
|---|---|---|
| **Claude Code** (plugin) | the whole repo, hooks included | `/plugin marketplace add joey114132/fable-workflow-skill`, then `/plugin install fable-workflow` |
| **Claude Code** (skills dir) | `../SKILL.md`, `../prompts.md`, `../standing-orders.md`, `../loop-engineering.md`, `../completion-gate.md`, `../scripts/goals.py` | `.claude/skills/fable-workflow/`, or run `../install.sh <skills-dir>`, which copies all of them (hooks are plugin-only) |
| **Cursor** | `cursor/fable-workflow.mdc` | `.cursor/rules/` |
| **Antigravity** | `AGENTS.md` | project root (or `.agents/rules/`, or `~/.gemini/GEMINI.md` for global) |
| **Codex / Aider / Zed / Jules / other AGENTS.md agents** | `AGENTS.md` | project root |

## Copy commands

```bash
# Cursor
mkdir -p .cursor/rules && cp cursor/fable-workflow.mdc .cursor/rules/

# Antigravity / Codex / Aider / Zed / Jules ...
cp AGENTS.md /path/to/your-project/AGENTS.md
```

## How each tool triggers it

Cursor reads the `.mdc` with `alwaysApply: false` and a `description`, and pulls it in
(agent-requested) when a task matches the description. `globs` is empty because the rule is
task-triggered, not file-triggered. Antigravity reads `AGENTS.md` from the workspace root before each
task. `AGENTS.md` is the emerging cross-tool standard, so other agents only need it at the repo root.

## What the adapters do not have

The adapters carry the method, not the Claude Code hooks. Nothing injects a reminder per prompt and
nothing checks a groundless "done" at the end of a turn. The completion gate is a plain Python script
(`../scripts/goals.py`) that runs wherever the agent can run `python3`, but only from a clone of
this repo. An adapter copied into another project has no `scripts/` directory, so there both adapters
tell the agent to keep the same goal list in a notes file.

## Keeping adapters in sync

`../SKILL.md` is canonical. `AGENTS.md` and `cursor/fable-workflow.mdc` carry a condensed copy of the
always-on core, the five-step loop, the correction loop, the completion gate, and the one-shot rule.
When the method changes, update all three.
