# Fable Workflow: agent rules

> **Portable adapter.** Copy this file to your **project root** as `AGENTS.md`. It is read by
> Antigravity, Cursor, OpenAI Codex, Aider, Zed, Jules, and other AGENTS.md-aware
> agents. (Antigravity also accepts it in `.agents/rules/`, or global rules in `~/.gemini/GEMINI.md`.)
> Self-contained on purpose: no other file required. It is a condensed copy of `SKILL.md`.

## Every answer, always
Sentence one is the answer. Mark each load-bearing claim Verified (with the evidence), Likely, or
Assumption. Recompute numbers with a tool instead of recalling them. End with what you did not check.

## When to apply the loop
Starting a non-trivial coding, design, or research task, especially when the spec is vague, the
codebase or domain is unfamiliar, or you would otherwise guess at something unspecified. Skip the
loop for a one-line change or an obvious fix. The rules above still apply there.

## The one idea
The map is not the territory. The spec or prompt is the *map*; the real codebase and constraints
are the *territory*. Wherever they diverge is an **unknown**, an unspecified decision. Don't guess
it silently. Surface it first, then build.

## The loop
1. **Unhobble.** Use tools, not memory. Counting, enumeration, and precise lookup mean writing a
   script. A name you don't confidently recognise, or one from a fast-moving area (AI models, dev
   tools), is itself something to verify: search it as the user wrote it before answering or building.
2. **Find the unknowns before building.**
   - Blind-spot pass: "list my unknown-unknowns and the gotchas in this module or domain."
   - Interview me: ask questions, prioritising the ones that would change the architecture.
   - Variants: for taste calls (design, output format, API shape), offer N genuinely different options.
   - References as maps: prefer an example or mockup over a written spec.
3. **Build: name the check first, then log the deviations.** Before the first edit, write down the
   command that decides "done" and what pass and fail look like. For a bug, reproduce it with a
   failing check first. If nothing runnable exists, say so and tag the result Likely. Stay inside the
   request: note a bug you spot elsewhere as a follow-up and do not fix it, but implement everything
   requested completely. Keep a running ASSUMPTIONS list of every unknown you hit and the choice made,
   in a notes file during a long session so it survives compaction.
4. **Verify: make it real.** Run the result, or write the smallest check that fails if the logic
   breaks, and look at the output. For a bug fix, watch the check fail on the unfixed code first.
   Research: test the key claim against a source. A subagent's or tool's report ("done", "12 passed")
   is a claim, not evidence: re-run it or read the diff first. For a non-trivial result, if you have
   subagents, give a fresh-context reviewer only the diff and the requirements and ask for
   correctness gaps, not style.
5. **Stay in the loop.** After a large change (several files, or a long session) and before merge or
   PR, offer to quiz the user on what changed. The user decides whether to take it.

## Correction loop (when verify fails)
Don't one-shot again. Each attempt states one hypothesis for why it failed, changes only that,
re-verifies, and logs hypothesis, change, and result. Cap the iterations before attempt one. If the
signal doesn't change across 2 iterations, stop and re-isolate. Stuck for real: write the repro, the
hypotheses tried, and the current signal to `.fable/handoff.md`, then continue in a fresh session.
A new unknown or an irreversible step breaks the loop to the human.

## Completion gate (2+ sequential stories, or a long autonomous run)
Decompose into goals and finish one at a time. A goal completes only with concrete evidence you
could be audited on (a command and its output, a `file:line`). The last goal is a verification story
with its verify command and the result it printed. `scripts/goals.py` exists only in a clone of the
fable-workflow repo. There, use `python3 scripts/goals.py create|next|checkpoint|status`. A copied
adapter has no `scripts/` directory, so keep the same list in a notes file. Never report "done"
while a goal is open. Skip all of this for single-step work.

## Rules
- Vague spec or unfamiliar territory: find the unknowns before implementing. Don't build the first interpretation silently.
- Enumeration, counting, precise lookup: script it. Taste call: offer variants that are genuinely different.
- Prioritise the few unknowns that change the architecture or the answer. Trivia questions waste the loop.
- Can't ask (one-shot or autonomous run)? Still write the UNKNOWNS list. Pick the conservative default
  for each (reversible, smallest blast radius) and log it with a one-line reason. If the only way
  forward is irreversible or external (delete, overwrite, push, send, spend, shared hardware), don't
  default it: leave it undone and list it as "needs your decision" with the command to run.
- Log every assumption so a wrong guess gets caught before it ships.
- A good plan is not a correct answer. Step 4 is mandatory.
