---
name: fable-workflow
description: >
  Use when a coding, design, or research request is vague or underspecified ("build me X", "add a feature", "write a
  function", "make a landing page"), even if the user says they are in a hurry, cannot answer questions, or tells you to
  "just finish it"; when the code or domain is unfamiliar; when the user wants options to react to ("I'll know it when I
  see it", "give me variants"); when they say "interview me" or "log your assumptions"; or when the answer includes
  facts that go stale (current versions, LTS lines, defaults, prices) that will be pasted into a doc or runbook. Makes
  the model find the unknowns that change the design BEFORE building, commit to explicit defaults, offer genuinely
  different variants for taste calls, verify the result with a tool, and state what was and was not verified or sourced.
  Skip trivial one-line edits and obvious typo fixes.
allowed-tools: [Read, Grep, Glob, WebSearch, WebFetch]
---

# Fable Workflow

A working method for capable frontier models. A capable model can traverse a huge solution
space on its own, so the bottleneck is whether **the human's map matches the territory**
before it starts moving. This skill closes that gap.

## Reference files (open one when its trigger fires)

- `prompts.md`: exact prompt wording. Read it when you run a blind-spot pass, interview, variants, quiz, or one-shot.
- `standing-orders.md`: per-ANSWER discipline, even for trivial answers. Read its Final gate (last section) before any answer that states a number, a version, or a claim about unrun code. Read §1 before asking the user a mid-task question.
- `loop-engineering.md`: read when a verify fails, before the second attempt, and before any unattended run.
- `completion-gate.md`: read for 2+ sequential stories or a long autonomous run. Ledger command: `python3 "${CLAUDE_SKILL_DIR}/scripts/goals.py" <subcommand>`, with the path filled in when this file loads.
- `hooks/` (plugin install only): a one-line reminder per prompt and a `Stop` gate that flags code edited but never run, or an open goals ledger. Advisory unless `FABLE_STRICT=1`.

Every answer, always: sentence one is the answer. Mark each load-bearing claim Verified (with
the evidence), Likely, or Assumption. Recompute numbers with a tool. End with what you did not check.

## The one idea

**The map is not the territory.** Your plan, spec, or prompt is the *map*; the real codebase
and constraints are the *territory*. Each place the model hits territory the map didn't cover
is an **unknown**, an unspecified decision. A capable model explores widely and hits many of
them. Left alone it guesses silently, and each silent guess is a place the result can drift
from what the user wanted. So **surface unknowns first, decide them explicitly, then build.**
This holds in any field: a vague research question or an ambiguous design brief hides the same decisions.

## The loop

### 1. Unhobble: reach for tools, not memory
Capable models are *spiky*: a question they fail from memory they nail by **writing a
script** (count letters, filter a fetched list). On any enumeration, counting, lookup, or
precise-string task, **use a tool** (Bash, a script, a search), not memory. A name in the
request that you don't confidently recognise, or that sits in a fast-moving area (AI models,
dev tools), is itself something to verify: search it as the user wrote it before answering or
building. Prefer a small instruction set with *context* over a long list of "do not" constraints.

### 2. Find the unknowns, before writing the real thing
Sort the problem into **known-knowns** (you'll say them), **known-unknowns** (you haven't
decided), **unknown-knowns** (so obvious you didn't say them), and **unknown-unknowns** (never
considered). Drag the bottom row into the light (`prompts.md` has copy-paste versions):

- **Blind-spot pass**: "list my unknown-unknowns for this module or domain, and where the
  gotchas are." Point it at git diffs, docs, and chat for context. Works for new codebases and new fields.
- **Interview me**: have the model interview you, **prioritising questions that would change
  the architecture.** Give it context about you and your stage.
- **Variants for taste calls**: for anything "I'll know it when I see it" (design, output
  format, API shape), ask for **N deliberately different options** to react to, not one.
- **References as maps**: hand it *example code or a mockup* of the target ("read this, then
  build in its spirit"). A second map beats prose.

### 3. Build: name the check first, then log the deviations
Before the first edit, write down the check that decides "done": the command, and what pass
and fail look like. For a bug, reproduce it with a failing check first. If nothing runnable
exists, say so now and tag the result Likely (`standing-orders.md` §5). Stay inside the
request: note a bug or improvement you spot elsewhere as a follow-up and do not fix it here,
but implement everything requested completely. **Log every unknown you hit** and the choice
made in an assumptions list. In a long session, keep that list in a notes file so it survives
compaction. It is the audit trail of where map and territory diverged.

### 4. Verify: make it real, don't just assert it
Before calling it done, **exercise the result**. Good reasoning does not guarantee a good
answer. Code: run it, or write the smallest check that fails if the logic breaks, and look
at the output. For a bug fix, watch that check FAIL on the unfixed code first, then pass.
Research or analysis: test the key claim against a source. Design or writing: put it in the
real context. A subagent's or tool's report ("done", "12 passed") is a claim, not evidence:
re-run it or read the diff before you repeat it. If the result scores two or more §3 flags and the
harness has subagents, give a fresh-context reviewer only the diff and the requirements and ask
for correctness gaps, not style (`standing-orders.md` §6). When verify **fails**, don't one-shot
again: enter a bounded **correction loop** with explicit stop conditions (`loop-engineering.md`).

### 5. Stay in the loop: keep owning it
After a large change (several files, or a long session) and before merge or PR, offer to
**quiz the user** on what changed so they can represent the work. They decide whether to take
it. Building is cheap; **generating value is still the hard part**, and staying in the loop
is how you keep steering toward it.

## Rules

- Vague spec or unfamiliar territory: **do step 2 before step 3.** Don't implement the first interpretation silently.
- Enumeration, counting, precise lookup: **script it**. Taste call: **offer variants**.
- End every build with the logged assumptions list. Offer the quiz-back only as step 5 says.
- **Verify the result, don't assert it.** A good plan is not a correct answer (see Gotchas).
- One-shot or autonomous (can't ask)? Write the unknowns list anyway and take the **conservative** default for each (reversible, smallest blast radius) with a one-line reason. List irreversible or external steps as "needs your decision" instead of doing them.

## Gotchas

- **The skill's value is front-loaded, and easy to skip.** The payoff is in the *pre-build*
  phase. Under time pressure models jump straight to code, which is exactly when the gap
  bites. If you skipped step 2, you didn't use the skill.
- **"Surface unknowns" is not "ask 20 questions and stall."** Prioritise the few unknowns
  that would *change the architecture or the answer*. Trivia questions waste the loop.
- **Don't over-apply the process to trivial tasks.** A one-line change or an obvious fix
  needs no blind-spot pass; YAGNI applies to process too. The per-answer rules above still apply.
- **Variants must be genuinely different**, not three shades of one idea.
- **Logging assumptions is not optional cover.** It lets the human catch a wrong guess
  *before* it ships. An unlogged assumption is a silent bet.
- **A surfaced plan is not a verified answer.** The method reliably improves *reasoning*,
  but reasoning is not a correct result, especially for code. Step 4 is mandatory.
- **A correction loop needs exits.** Retrying with no new hypothesis, or looping past a
  discovered unknown, is a hang. Cap iterations, require a moving signal each turn, and break to the human when stuck.
- **Small models (about 8B and under) may code worse with the pilot's one-shot unknowns prompt.**
  In `benchmark/RESULTS.md` the answer score fell in some runs (qwen2.5:7b 33→25 and 18→4,
  gemma3:4b 37→8 once) while gemma3:4b's totals later rose (18→60, 51→61). Each cell is one
  draw, self-judged, and the pilot did not test this SKILL.md, so there is no proven size cutoff.
  qwen3.6 also swung (82→87, 82→70, 90→75). If a small model's code gets worse, switch to the
  lite variant: cap unknowns at 2–3 and give a **reference to adapt** (`prompts.md` → Small / local models).
