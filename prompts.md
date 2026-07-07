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

## Log deviations (during build)
> While you build, keep a running **ASSUMPTIONS / IMPLEMENTATION NOTES** list: every time
> you hit something my spec didn't cover (an unknown), record it and the choice you made.
> Show the list with the result.

## Quiz me (stay in the loop before merge)
> Before I open the PR, **quiz me** on what changed and why — the decisions I'd need to
> defend in review. Flag anything I get wrong or can't explain.

## One-shot / autonomous (can't ask back)
> You can't ask me questions on this run. So first write an **UNKNOWNS** list (the decision
> points my spec left open), pick a sensible default for each **and say why**, THEN implement.
> Surface the unknowns even though you're proceeding without me.
