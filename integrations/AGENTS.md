# Fable Workflow — agent rules

> **Portable adapter.** Copy this file to your **project root** as `AGENTS.md`. It is read by
> Antigravity (v1.20.3+), Cursor, OpenAI Codex, Aider, Zed, Jules, and other AGENTS.md-aware
> agents. (Antigravity also accepts it in `.agents/rules/`, or global rules in `~/.gemini/GEMINI.md`.)
> Self-contained on purpose — no other file required.

## When to apply
Starting a non-trivial coding, design, or research task — **especially** when the spec is vague,
the codebase/domain is unfamiliar, or you'd otherwise guess at something unspecified. Skip for
trivial one-line changes.

## The one idea
**The map is not the territory.** The spec/prompt is the *map*; the real codebase and constraints
are the *territory*. Wherever they diverge is an **unknown** — an unspecified decision. Don't guess
it silently. Surface it first, then build.

## The loop
1. **Unhobble** — use tools, not memory. Counting / enumeration / precise lookup → *write a script*, don't recall.
2. **Find the unknowns — before building:**
   - **Blind-spot pass** — "list my unknown-unknowns and the gotchas in this module/domain."
   - **Interview me** — ask questions, **prioritising ones that would change the architecture.**
   - **Variants** — for taste calls (design, output format, API shape), offer **N genuinely different** options to react to, not one.
   - **References as maps** — prefer an example/mockup over a written spec ("build in the spirit of this").
3. **Build, logging deviations** — keep a running **ASSUMPTIONS / NOTES** list of every unknown hit and the choice made.
4. **Verify — make it real** — exercise the result before calling it done (code: run it / smallest check; research: verify the claim against a source). A good plan is not a correct answer. If it fails, enter a bounded correction loop (attempt → verify → diagnose → repeat) with a max-iterations cap; stop and surface the blocker if the signal stalls.
5. **Stay in the loop** — **quiz the human** before merge so they still own the work.

## Rules
- Vague spec / unfamiliar territory → find the unknowns **before** implementing. Don't build the first interpretation silently.
- Enumeration / counting / precise lookup → **script it**, don't recall it.
- Taste / subjective call → **offer variants**, don't pick one and hope.
- **Can't ask** (autonomous run)? Still write an **UNKNOWNS** list, pick a sensible default for each **with a one-line reason**, log them, then proceed.
- Prioritise unknowns that change the architecture or the answer — not trivia.
