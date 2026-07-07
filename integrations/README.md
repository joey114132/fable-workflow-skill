# Integrations

The same method (`../SKILL.md`) packaged for other agent tools. Each adapter is self-contained.

| Tool | File | Install into your project |
|---|---|---|
| **Claude Code** | `../SKILL.md` + `../prompts.md` | `.claude/skills/fable-workflow/` (or run `../install.sh`) |
| **Cursor** | `cursor/fable-workflow.mdc` | `.cursor/rules/` |
| **Antigravity** | `AGENTS.md` | project root (or `.agents/rules/`, or `~/.gemini/GEMINI.md` for global) |
| **Codex / Aider / Zed / Jules / other AGENTS.md agents** | `AGENTS.md` | project root |

## Copy commands

```bash
# Cursor
mkdir -p .cursor/rules && cp cursor/fable-workflow.mdc .cursor/rules/

# Antigravity / Codex / Aider / Zed / Jules …
cp AGENTS.md /path/to/your-project/AGENTS.md
```

## How each tool triggers it

- **Cursor** — `.mdc` with `alwaysApply: false` and a `description`; Cursor pulls it in
  ("agent-requested") when a task matches the description. `globs` is empty because this is
  task-triggered, not file-triggered.
- **Antigravity** — reads `AGENTS.md` from the workspace root before each task.
- **Others** — `AGENTS.md` is the emerging cross-tool standard; drop it at the repo root.

## Keeping adapters in sync
`../SKILL.md` is canonical. `AGENTS.md` and `cursor/fable-workflow.mdc` carry a **condensed** copy
of the loop + rules. If you change the method, update all three.
