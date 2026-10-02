<p align="center">
  <img src="assets/banner.png" alt="Fable Workflow" width="100%">
</p>

<h1 align="center">Fable Workflow</h1>

<p align="center">
  A portable agent skill that teaches <b>any</b> model (Opus, Sonnet, Haiku, Fable)
  to work like Anthropic's Fable: <b>find the unknowns before building, then verify the result.</b>
</p>

<p align="center">
  <b>English</b> · <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT">
  <img src="https://img.shields.io/badge/format-SKILL.md-purple" alt="SKILL.md">
  <img src="https://img.shields.io/badge/models-Opus%20%C2%B7%20Sonnet%20%C2%B7%20Haiku%20%C2%B7%20Fable-orange" alt="models">
</p>

---

## What this is

`fable-workflow` packages a working method for Anthropic's Fable-class models into a reusable [`SKILL.md`](SKILL.md) you can drop into Claude Code, Cursor, or any agent framework.

Capable models are powerful enough to explore a huge solution space on their own. The bottleneck is whether **your mental map matches the territory** before the model starts moving. Every place your spec is silent is an **unknown**: an unspecified decision the model will otherwise guess at silently. This skill makes the model **surface those unknowns first**, then build, then run what it built before it says "done".

## The one idea

> **The map is not the territory.** Your plan, spec, or prompt is the *map*. The real codebase and constraints are the *territory*. Wherever they diverge is an **unknown**, so decide it explicitly instead of letting the model guess.

## The loop

1. **Unhobble.** Reach for tools, not memory. Counting, enumeration, and lookup mean *writing a script*. A name the model doesn't confidently recognise gets searched as you wrote it.
2. **Find the unknowns** before building: blind-spot pass, interview-me, N variants for taste calls, references-as-maps.
3. **Build: name the check first, then log the deviations.** Write down the command that decides "done" before the first edit (a failing repro for a bug), keep an ASSUMPTIONS / NOTES list of every unknown it hits, and leave out-of-scope bugs as follow-ups.
4. **Verify: make it real.** Run it, or write the smallest check that fails if the logic breaks, and watch that check fail on the unfixed code first. A subagent's "done" is a claim, not evidence. When verify fails, a bounded correction loop takes over (one hypothesis per attempt, capped iterations, a fresh session when stuck).
5. **Stay in the loop.** After a large change and before merge or PR, the model offers to quiz you on what changed. You decide whether to take it.

Every answer, loop or not, opens with the answer itself, marks each load-bearing claim Verified, Likely, or Assumption, and ends with what was not checked.

When the model can't ask (a one-shot or autonomous run), it still writes the unknowns list and picks the conservative default for each. An irreversible or external step (delete, overwrite, push, send, spend) is left undone and listed as "needs your decision" with the command to run.

See [`SKILL.md`](SKILL.md) for the full method and [`prompts.md`](prompts.md) for copy-paste prompts.

[`standing-orders.md`](standing-orders.md) holds the per-answer discipline, [`loop-engineering.md`](loop-engineering.md) the correction loop, and [`completion-gate.md`](completion-gate.md) the multi-story gate.

## Install

### Claude Code: plugin (recommended)
```shell
/plugin marketplace add joey114132/fable-workflow-skill
/plugin install fable-workflow
```

### Claude Code: manual copy
```bash
git clone https://github.com/joey114132/fable-workflow-skill.git
./fable-workflow-skill/install.sh ~/your-project/.claude/skills
```
`install.sh` copies `SKILL.md`, the four reference files (`prompts.md`, `standing-orders.md`, `loop-engineering.md`, `completion-gate.md`) and `scripts/goals.py` into `~/your-project/.claude/skills/fable-workflow/`. Claude Code auto-discovers `SKILL.md` and triggers it from the YAML `description`.

The hooks are plugin-only and are not copied. Running it again overwrites the installed files, so keep local edits elsewhere.

### Cursor
```bash
git clone https://github.com/joey114132/fable-workflow-skill.git
mkdir -p .cursor/rules
cp fable-workflow-skill/integrations/cursor/fable-workflow.mdc .cursor/rules/
```
Cursor loads it in agent-requested mode via the rule's `description`.

### Antigravity · Codex · Aider · Zed & other AGENTS.md agents
Copy the portable rule to your project root:
```bash
cp fable-workflow-skill/integrations/AGENTS.md ./AGENTS.md
```
Antigravity also accepts it in `.agents/rules/`, or `~/.gemini/GEMINI.md` for global rules. Both adapters carry a condensed copy of the full method. They have no hooks.

All adapters and per-tool details: [`integrations/`](integrations/).

## Enforcement (Claude Code plugin)

Installed as a plugin, `fable-workflow` also enforces the method with two hooks (`hooks/`, stdlib-only Python):

- `UserPromptSubmit` runs `inject_method.py` on **every** prompt and injects exactly one short line (about 25 to 45 tokens, estimated from about 100 to 165 characters). The first rule that matches the prompt picks the line.
  - A bug, crash, or failing test gets "investigate" (reproduce, compete 3+ hypotheses, verify before and after).
  - "Interview me" gets "interview first".
  - A question gets "answer from evidence, not recall".
  - Several steps get "decompose with the completion gate".
  - A typo or one-liner gets "small fix, no ceremony".
  - A build request gets "name the open decisions, build, then run it".
  - Anything else (`continue`, `ok`, `thanks`) gets the neutral evidence line, never a build instruction.

  English and Korean keywords both match. Set `FABLE_HOOK_LOG=<path>` to log each firing.
- `Stop` runs `verify_gate.py` and judges only the current turn. It flags "not done" in two cases.
  - The turn edited a code file and never ran anything afterward.
  - The completion-gate ledger still has open goals (an unreadable ledger counts as not done).

  By default the gate is **advisory**: the warning is shown to you, and the model does not see it. With `FABLE_STRICT=1` it blocks the stop and feeds the reason back to the model, once per stop attempt.

The completion gate (`scripts/goals.py`) decomposes multi-step work into goals. Each goal completes only with evidence, and the final goal is a verification story that refuses "done" without a verify command and its result.

Inside the skill, Claude runs it as `python3 ${CLAUDE_SKILL_DIR}/scripts/goals.py <subcommand>` (`create`, `next`, `checkpoint`, `status`, `reset`), and the multi-step hook line hands the model the absolute path.

The ledger is `.fable/goals.json` in your project root, written atomically. See [`completion-gate.md`](completion-gate.md).

The evidence is self-reported, and the script only checks that it is non-empty. Word each goal so that someone reading the transcript could tell whether it was met.

Both checks are heuristics and can misfire (a declarative "I'll do X" can look like a skipped run), which is why the Stop gate is advisory by default and strict mode is opt-in.

The logic is covered by `hooks/test_hooks.py` and `scripts/test_goals.py`.

## Evals

`evals/` holds seven `claude plugin eval` cases that check behavior rather than wording: an architecture interview that asks only the few questions that matter, a stale fact that must be sourced or flagged, a one-shot build that states its assumptions, a trivial fix with no ceremony, and three more. Run them from the repo root:

```bash
claude plugin eval . --no-publish
claude plugin eval . --no-publish --allow-tools WebSearch WebFetch   # lets the evidence case search
```

Each case runs with and without the plugin (a baseline arm), and the harness does this for you. Results land in `evals/results/` (gitignored).

Bash cannot be granted without `socat`, so the suite does not cover the "run it to verify" behavior. Don't edit a case to make it pass.

The first run (2026-10-02, one run per case and arm) passed 4 of 7 cases with the plugin. It is a first data point, described in [benchmark/RESULTS.md](benchmark/RESULTS.md#first-claude-plugin-eval-run-2026-10-02-plugin-110).

## Benchmark

Does the skill actually change model behavior? A small A/B on a deliberately under-specified spec (*"Users shouldn't be able to spam our API. Limit it to 100 requests per minute."*, which hides about 8 architecture-changing unknowns), run across eight models (cloud and local) with and without a short one-shot prompt that states the skill's core move: list the unknowns with defaults, then implement (see "Reproduce" in [`benchmark/RESULTS.md`](benchmark/RESULTS.md)). The prompt is not the full `SKILL.md` and the hooks were not active.

![benchmark](benchmark/bench.png)

| Model | Type | No skill | With skill | Δ |
|---|---|:---:|:---:|:---:|
| llama3:8b | local | 8 | 27 | **+19** |
| qwen2.5:7b | local | 44 | 54 | +10 |
| gemma3:4b | local | 50 | 38 | **−12** |
| **Haiku 4.5** | cloud | 66 | 81 | **+15** |
| qwen3.6 | local | 82 | 87 | +5 |
| Sonnet 5.5 (re-run 2026-10-02) | cloud | 90 | 91 | +1 |
| **Sonnet 5** | cloud | 91 | 98 | +7 |
| Opus 5.5 (re-run 2026-10-02) | cloud | 93 | 95 | +2 |
| **Opus 4.8** | cloud | 95 | 98 | +3 |
| **Fable 5** | cloud | 96 | 100 | +4 |

Scored on **answer + thinking quality** out of 100, split Thinking /50 + Answer /50 ([detailed rubric and sub-scores](benchmark/RESULTS.md)). In the headline run the skill improved the models' reasoning more than their code. *Thinking* quality rose for every model (+2 to +18), but *answer* quality only improves when the model can already code the plan, and it was flat or negative for weak locals.

The local re-runs show how noisy single draws are. gemma3 swung from −12 to +42 between identical runs, and the strongest local model (qwen3.6) fell in a later reproduction (Thinking 40 → 32, total 90 → 75).

Biggest total gains were on capable-but-under-reasoning models (llama3:8b +19, Haiku 4.5 +15). Fable 5 scored **96 unaided**.

Read the numbers as a directional pilot. The July cloud rows are single-trial and were self-judged by Opus 4.8. The Opus 5.5 and Sonnet 5.5 rows are single draws from 2026-10-02, judged blind by Opus 4.8, which is not one of those two models. Both models score 90 or more unaided, so the skill had little room to add.

The cloud runs were made in July 2026. Three of the four cloud models they measured (Fable 5, Opus 4.8, Sonnet 5) are now legacy, and so is the Opus 4.8 judge. As of 2026-10-02 the current lineup is Fable 5.1, Opus 5.5, Sonnet 5.5 and Haiku 4.5. Opus 5.5 and Sonnet 5.5 were re-run once on 2026-10-02, with a different harness from July (see the re-run section of [benchmark/RESULTS.md](benchmark/RESULTS.md)). Haiku 4.5 is still the July row, and Fable 5.1 was not measured.

The [`evals/`](#evals) suite is the reproducible replacement, because it tests the shipped plugin instead of a short prompt.

Full methodology, rubric, per-model evidence, and limitations: **[benchmark/RESULTS.md](benchmark/RESULTS.md)**.

## Repo layout

```
fable-workflow-skill/
├── SKILL.md            # the skill (drop-in, canonical method)
├── standing-orders.md  # per-answer discipline + pre-send gate
├── prompts.md          # copy-paste prompt templates
├── loop-engineering.md # act → verify → correct → repeat (correction loop)
├── completion-gate.md  # multi-story completion gate (usage)
├── .claude-plugin/     # plugin.json + marketplace.json
├── hooks/              # plugin enforcement: inject + verify gate (+ tests)
├── scripts/            # goals.py completion-gate ledger + test_goals.py
├── evals/              # claude plugin eval cases (behavior checks)
├── integrations/       # adapters for other tools
│   ├── AGENTS.md       # Antigravity · Codex · Aider · Zed · Jules …
│   └── cursor/fable-workflow.mdc
├── install.sh          # copy the skill and goals.py into a .claude/skills dir
├── CLAUDE.md           # contributor notes for this repo
├── benchmark/
│   ├── RESULTS.md      # cross-model A/B evaluation
│   └── bench.png       # results chart
├── assets/banner.png
├── README.md           # English
└── README.ko.md        # 한국어
```

## Notes

This repo packages a working method as a skill. It is not an official Anthropic release.

## License

[MIT](LICENSE)
