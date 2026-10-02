# Fable Workflow — copy-paste prompts

Paste these to any model. Works in English or Korean; capable models handle both.
Fill the `{…}` slots. These implement the loop in `SKILL.md`.

## Blind-spot pass (find unknown-unknowns)
> I'm about to work on **{task/module}** in this codebase, and I don't know it well yet.
> Do a **blind-spot pass**: read the relevant code (and {git diff / Slack / these docs:
> …} for context) and list the **unknown-unknowns** I should decide before we start —
> gotchas, hairy dead-ends, hidden coupling. Then tell me how to prompt you better.

New-domain variant:
> I know almost nothing about **{new field}**. Do a blind-spot pass and teach me the
> relevant unknowns — what would change my approach if I knew it?

## Interview me (fill known-unknowns)
> Before you build **{task}**, **interview me**. Ask one question at a time.
> **Prioritise questions that would change the architecture** or the core decisions.
> Context on me and where I'm at: {…}. Stop when the remaining questions are just details.

## Variants (surface unknown-knowns / taste calls)
> I have {no / weak} visual taste here. Make **{N=3–4} deliberately DIFFERENT** {designs /
> output formats / API shapes} for **{thing}** as {an HTML page / side-by-side samples} so
> I can react to them. Make them genuinely distinct, not three shades of one idea.

## Reference as map (skip writing the full spec)
> Here is {code / a mockup / an HTML page} that represents what I want: {paste or path}.
> It may be a different language/system. **Read it, understand the intent, then build
> {target}** in that spirit. Ask only if the intent is ambiguous.

## Check first (before the first edit)
> Before you change anything, write down the check that decides "done": the exact command and
> what pass and fail look like. For a bug, reproduce it with a failing check first. If nothing
> runnable exists, say so and mark the result Likely. Stay inside this request; list anything
> else you notice as a follow-up instead of fixing it.

## Log deviations (during build)
> While you build, keep a running **ASSUMPTIONS / IMPLEMENTATION NOTES** list: every time
> you hit something my spec didn't cover (an unknown), record it and the choice you made.
> In a long session keep the list in a notes file so it survives compaction. Show it with the result.

## Verify — make it real (before you call it done)
> Don't assert it works — **exercise it.** Code: run it, or write the smallest check that fails
> if the logic breaks, and show the output. For a bug fix, show that check failing on the
> unfixed code first, then passing. Research/analysis: verify the key claim against a source.
> Design/doc: put it in the real context and show how it holds up. A subagent's or tool's
> "done" is a claim: re-run it or read the diff before you repeat it.

## Correction loop (when verify fails)
> Don't retry blindly. Each attempt: state ONE hypothesis for *why* it failed, change only that,
> re-verify, and log hypothesis → change → result. Cap it at N tries. If the signal doesn't change
> across 2 iterations, stop and re-isolate — or tell me the unknown you hit. Don't loop forever.

## Quiz me (stay in the loop before merge)
> Before I open the PR, **quiz me** on what changed and why — the decisions I'd need to
> defend in review. Flag anything I get wrong or can't explain.

## One-shot / autonomous (can't ask back)
> You can't ask me questions on this run. So first write an **UNKNOWNS** list (the decision
> points my spec left open), pick the **conservative** default for each (reversible, smallest
> blast radius) **and say why**, THEN implement. Anything irreversible or external (delete,
> overwrite, push, send, spend, shared hardware): don't default it. Leave it undone and list it
> as "needs your decision" with the command to run. Surface the unknowns even though you're
> proceeding without me.

## Small / local models (about 8B and under)

A weak model spends its limited capacity on the process and can then botch the code. In one
benchmark run gemma3:4b, asked to *derive* an implementation while also producing a full
unknowns list, inverted the logic (commit 3b4a763). Its later runs scored higher with the pilot's
one-shot unknowns prompt (18→60, 51→61 in `benchmark/RESULTS.md`), so treat this as a risk to watch, not a rule.
If a small model's code gets worse, cap the analysis and use the **references-as-maps** move:
have it *adapt a known-good reference* instead of deriving.

> You're building a small feature and CANNOT ask questions. Keep it short.
> STEP 1 — list only the **2–3 most important** open decisions, each with a one-line default.
> STEP 2 — implement by **ADAPTING the reference below** to those defaults. Keep its structure
> and algorithm; do NOT invent a new approach.
>
> REFERENCE (a known-good implementation of the pattern you want — adapt, don't rewrite):
> ```
> {paste a correct example/skeleton of the target pattern}
> ```
>
> TASK: {your task + spec}

No reference handy? Try a stronger local model, but the benchmark gives no safe size. The
reasoning model qwen3.6 went 82→87 in one run and 82→70 and 90→75 in two later ones. Every cell
is a single self-judged draw, so check the code itself, not the score.
