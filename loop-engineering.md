# Loop Engineering — act → verify → correct → repeat

Verify (step 4) isn't one-shot. When verification fails you enter a **correction loop**.
Engineering that loop — so it *converges* instead of thrashing or spinning forever — is the
difference between an agent that finishes and one that burns the budget.

## The loop
1. **Attempt** — make the smallest change that could plausibly work.
2. **Verify** — exercise it (run / check / drive). Capture the concrete **signal** (test output, error text, metric).
3. **Diagnose** — if it failed, form **one specific hypothesis** for *why* (reproduce → isolate → hypothesize). Don't edit randomly.
4. **Correct** — change the one thing the hypothesis points at.
5. **Repeat** — back to step 2.

## Stop conditions — this is the actual engineering
A loop without exits is a hang. Decide these **before** the first attempt:

- **Success** — verification passes → stop, done.
- **Budget** — cap it (≤ N iterations, or a token/time budget). Hitting the cap is a *stop*, not a cue to keep going.
- **No progress** — if the signal doesn't change across 2 iterations (same error, same failure), you're spinning. Stop looping and **re-isolate** — more attempts won't help.
- **Repeat detection** — about to try something already tried? Stop.
- **New unknown / irreversible step** — the loop uncovered an unspecified decision, or you're about to do something destructive → **break to the human**. Don't decide it inside the loop.

## Rules
- **Every iteration must move a measurable signal.** If you can't name the signal, you can't loop — go back to Verify and define it.
- **Change one thing per iteration.** Multi-change turns make the signal uninterpretable.
- **Log each turn**: hypothesis → change → result. That log is the audit trail *and* your repeat-detector.
- **Diagnose, don't thrash.** Random edits until it passes is a slot machine, not a loop.
- **Bound it up front** — set the max-iterations/budget before attempt #1, not after you're 20 turns deep.

## Anti-patterns
- **Infinite retry** — same failing action, no new hypothesis.
- **Green by luck** — stopping when the check passes without understanding *why* it passes (may be masking the bug).
- **Silent thrash** — many iterations, no logged hypotheses; nobody can tell what was tried.
- **Looping past an unknown** — hit an unspecified decision and guessed instead of surfacing it.

## Autonomous loops (no human to break to)
The budget + no-progress + repeat-detection exits become **mandatory** — they're the only thing
between you and an infinite spend. On exit-by-stuck, emit a clear **"here's what I tried, here's
where I'm blocked, here's the unknown"** report — never a false success.
