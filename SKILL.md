---
name: fable-workflow
description: >
  Fable-style agentic working method, usable by ANY model (Opus, Sonnet, Haiku, Fable).
  Distills a Fable-style agentic working method into a repeatable loop: unhobble the model
  with tools, find the unknowns BEFORE building, generate variants for taste calls, log
  every deviation, and keep the human in the loop. Use when starting a non-trivial coding,
  design, or research task — especially when the spec is vague, the codebase or domain is
  unfamiliar, or the model would otherwise guess at things you never specified. Trigger on:
  "blind spot pass", "find my unknowns", "interview me", "give me N variants / options",
  underspecified specs, new-domain exploration, or "log your assumptions".
allowed_tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# Fable Workflow

A working method for capable ("Mithril-class") models. The model is powerful enough to
traverse a huge solution space on its own — so the bottleneck is no longer *its* ability,
it's whether **the human's map matches the territory** before the model starts moving.
This skill closes that gap.

> Prompt templates live in `prompts.md` — read it when you need the exact wording.

## The one idea

**The map is not the territory.** The plan/spec/prompt in your head is the *map*. The real
codebase and constraints are the *territory*. Every place the model hits territory the map
didn't cover is an **unknown** — an unspecified decision point. A capable model hits MANY of
these because it explores widely. Left alone it silently guesses; each silent guess is a
place the result can drift from what the user wanted. So: **surface unknowns first, decide
them explicitly, then build.** This holds in any field — a vague research question, an
ambiguous design brief, or an underspecified analysis each hide the same unspecified decisions.

## The loop

### 1. Unhobble — reach for tools, not memory
Capable models get smarter in *spiky* ways: a question they fail from memory they nail by
**writing a script** (e.g. "which Pokémon names end in 'aw'?" → fetch the list, filter it).
So on any enumeration / counting / lookup / precise-string task, **use a tool** (Bash, a
script, a search) instead of answering from memory. Prefer a smaller instruction set with
*context* over a long list of "do not" constraints — constraints cap a model that's more
imaginative than the examples you'd give it.

### 2. Find the unknowns — before writing the real thing
Sort the problem into: **known-knowns** (you'll write these in the prompt), **known-unknowns**
(you know you haven't decided), **unknown-knowns** (so obvious you didn't say it — you'll
know it when you see it), **unknown-unknowns** (never considered). Use these moves to drag
the bottom row into the light (`prompts.md` has copy-paste versions):

- **Blind-spot pass** — "do a blind-spot pass on this module/domain; list my unknown-unknowns
  and where the gotchas are." Point it at git diffs, Slack, docs for context. Great for new
  codebases *and* new fields.
- **Interview me** — have the model interview you, **prioritising questions that would change
  the architecture.** Give it context about you and the stage you're at.
- **Variants for taste calls** — for anything "I'll know it when I see it" (design, output
  format, API shape), ask for **N deliberately different options** to react to, not one.
- **References as maps** — instead of writing the whole spec, hand it *example code or a mockup*
  that represents the target ("read this, then build in its spirit"). A second map beats prose.

### 3. Build — but log the deviations
While building, **log every unknown it hits** and the choice it made (an "assumptions /
implementation notes" list). That's your audit trail of where map and territory diverged.

### 4. Verify — make it real, don't just assert it
Before calling it done, **exercise the result** — good reasoning does not guarantee a good
answer. Code: run it, or write the smallest check that fails if the logic breaks, and look at
the output. Research/analysis: test the key claim against a source. Design/writing: put it in
front of the real context. This is the step that turns a sound *plan* into a correct *result*.

### 5. Stay in the loop — keep owning it
Before merging/PR, have the model **quiz you** on what changed, so you can actually represent
the work. Building is now cheap; **generating value is still the hard part** — staying in the
loop is how you keep steering toward value instead of just shipping motion.

## Rules

- Vague spec or unfamiliar territory → **do step 2 before step 3.** Don't implement the first
  interpretation silently.
- Enumeration / counting / precise lookup → **script it**, don't recall it.
- Taste/subjective call → **offer variants**, don't pick one and hope.
- Always end a build with a **logged assumptions list** and (interactively) a quiz-back.
- **Verify the result, don't assert it** — run / check / drive the output before calling it done.
  A good plan is not a correct answer (see Gotchas).
- One-shot / autonomous (can't ask)? Still surface the unknowns as a written list, pick
  sensible defaults, and log them — the surfacing is the point, not the asking.

## Gotchas

- **The skill's value is front-loaded, and easy to skip.** The payoff is in the *pre-build*
  phase (unknowns, variants). Under time pressure models jump straight to code — that's
  exactly when the map/territory gap bites. If you skipped step 2, you didn't use the skill.
- **"Surface unknowns" ≠ "ask 20 questions and stall."** Prioritise the few unknowns that
  would *change the architecture or the answer*. Trivia questions waste the loop.
- **Don't over-apply to trivial tasks.** A one-line change or an obvious fix doesn't need a
  blind-spot pass. YAGNI applies to process too — this is for non-trivial work.
- **Variants must be genuinely different, not three shades of the same idea.** Three
  near-identical options give the human nothing to react to.
- **Logging assumptions is not optional cover.** It's the artifact that lets the human catch
  a wrong guess *before* it ships. An unlogged assumption is a silent bet.
- **A surfaced plan is not a verified answer.** The method's real limit: it reliably improves
  *reasoning*, but reasoning ≠ a correct result — especially for code. Don't stop at a great
  UNKNOWNS list and confident prose; **step 4 (verify) is mandatory** — exercise the output.
- **Weak/small models (≤ ~8B) need the lite variant.** The full "surface all unknowns, then
  derive the code" prompt crowds a small model's capacity and *degrades* its implementation —
  it reasons more but codes worse. For those, cap unknowns at 2–3 and anchor with a **reference
  to adapt** rather than derive (see `prompts.md` → Small / local models). Capable/reasoning
  models don't need this.
