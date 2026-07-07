# Benchmark — does the `fable-workflow` skill change model behavior?

**Audience:** anyone deciding whether to adopt this skill, and anyone who wants to reproduce or extend the evaluation.

**Question it answers:** when a model is given an under-specified task, does injecting the `fable-workflow` skill make it *surface the hidden decisions first* — and does that help more on some models than others?

> ⚠️ **Read the [Limitations](#limitations) section before quoting these numbers.** This is a small directional pilot (n=1 task, single trial, self-judged), not a statistically robust leaderboard.

---

## TL;DR

| Model | No skill | With skill | Δ |
|---|:---:|:---:|:---:|
| **Fable 5** | 10 | 10 | 0 |
| **Opus 4.8** | 9 | 10 | +1 |
| **Sonnet 5** | 9 | 10 | +1 |
| **Haiku 4.5** | 4 | 8 | **+4** |

The skill's job — porting Fable 5's native "find-the-unknowns-first" behavior onto other models — shows up cleanly: **biggest lift where the model is weakest** (Haiku +4), **near-zero where the model already does it** (Fable +0, frontier models +1).

---

## What was tested

### Task (identical for every run)

A deliberately under-specified spec, framed as a one-shot autonomous job (the model **cannot** ask questions):

> **TASK:** Add rate limiting to our web API.
> **SPEC (verbatim from the product owner):** *"Users shouldn't be able to spam our API. Limit it to 100 requests per minute."*
> Deliver a Python rate-limiter implementation plus a short note.

This spec hides at least ~8 **architecture- or behavior-changing unknowns**:

1. **Scope** — per-IP, per-user, per-API-key, or global?
2. **Window algorithm** — fixed window, sliding window, or token bucket? (fixed windows allow a 2× burst across the minute boundary)
3. **Storage** — in-memory (single process) or Redis/shared (distributed)?
4. **Over-limit behavior** — reject 429, queue, or throttle? `Retry-After`?
5. **Burst tolerance** — hard ceiling, or allow an idle client to burst?
6. **Concurrency** — thread safety of the counter.
7. **Clock source** — wall clock vs monotonic (NTP jumps).
8. **Memory growth** — are idle keys ever evicted?

A model that "just codes" picks one interpretation silently. A model applying the skill enumerates these, picks defaults *with reasons*, then implements.

### Conditions

- **No skill:** the task prompt alone.
- **With skill:** the same task prompt + the skill's one-shot instruction (surface an UNKNOWNS list first, pick a default per item with a one-line reason, then implement).

### Models

Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5 — spawned as identical `general-purpose` subagents, tools available, output capped at ~400 words + code. 4 models × 2 conditions = **8 runs**.

### Rubric (0–10)

| Dimension | Points | What earns them |
|---|:---:|---|
| **Unknowns surfaced** | 0–5 | Count of genuine, distinct, architecture/behavior-changing unknowns raised |
| **Assumptions logged** | 0–2 | Defaults stated explicitly, each with a reason |
| **Implementation quality** | 0–3 | Actually enforces 100/min, thread-safe, correct on the window-boundary edge case |

---

## Results (with breakdown)

| Model | Condition | Unknowns | U (0–5) | A (0–2) | I (0–3) | **Total** |
|---|---|:---:|:---:|:---:|:---:|:---:|
| Fable 5 | no skill | 6 | 5 | 2 | 3 | **10** |
| Fable 5 | with skill | 9 | 5 | 2 | 3 | **10** |
| Opus 4.8 | no skill | ~5 | 4 | 2 | 3 | **9** |
| Opus 4.8 | with skill | 7 | 5 | 2 | 3 | **10** |
| Sonnet 5 | no skill | ~6 | 4 | 2 | 3 | **9** |
| Sonnet 5 | with skill | 7 | 5 | 2 | 3 | **10** |
| Haiku 4.5 | no skill | 2 | 2 | 1 | 1 | **4** |
| Haiku 4.5 | with skill | 7 | 4 | 2 | 2 | **8** |

## Per-model evidence

- **Fable 5 is the "native" of this workflow.** *Without* the skill it already surfaced 6 unknowns as a labeled decisions list (including the subtle **clock-source** one), logged every default with a reason, and **actually ran its own self-check** before answering. *With* the skill it went further — flagging the meta-unknown *"this repo has no web API to attach to"* and *"do rejected requests consume tokens?"* (9 unknowns). Nothing to improve on a 10.

- **Haiku 4.5 — the clearest win.** *Without* the skill it mislabeled a **fixed-window** counter as a "token bucket" (carrying the 200-request boundary-burst bug) and surfaced only 2 unknowns → **4/10**. *With* the skill it produced a correct sliding window and a 7-row unknowns table → **8/10** (+4).

- **Opus 4.8 / Sonnet 5 were already near-ceiling.** Both surfaced most unknowns in prose even without the skill (correct sliding-window / token-bucket implementations, `Retry-After`, self-checks). The skill mainly reshaped that reasoning into an explicit, prioritized list (+1 each).

## Interpretation

The skill is **not** a uniform quality boost. Its measurable effect is concentrated exactly where the theory predicts: models that don't spontaneously "find the unknowns" get the biggest lift. Frontier models mostly already do it; Fable 5 does it by default. So the skill's real value is **leveling up cheaper/weaker models to the frontier's default behavior** on ambiguous specs.

---

## Limitations

Do not over-read these numbers.

- **n = 1 task, single trial, no repeats.** No error bars. Scores are directional.
- **Self-judged.** Scoring was done by one of the contestant models (Opus 4.8), which is a bias risk — especially for the Opus row.
- **One-shot autonomous can only test one slice of the skill.** The interactive moves — *interview me*, *blind-spot pass over a real codebase*, *N variants for taste calls*, *quiz-back before merge* — do not fire in a single autonomous shot. The measured gain is only the **surface-the-unknowns** behavior.
- **Single task domain** (rate limiting). Results may not transfer to other kinds of ambiguity.

### To make it robust
- Add the multi-turn tasks (interview / variants) with a **neutral judge** model (not a contestant).
- Run **3–5 trials per cell** for variance.
- Broaden to **several task domains**.

---

## Reproduce

For each of {Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5} × {no skill, with skill}, spawn an identical autonomous agent with the task above. For the **with-skill** arm, prepend:

```
Follow this working method (Fable workflow):
The spec is a MAP; the real system is the TERRITORY. Wherever the spec is silent
there is an UNKNOWN — a decision it didn't make. Since you can't ask me:
1) FIRST write an "UNKNOWNS" list — the open decision points — prioritising ones
   that change the architecture or behaviour.
2) For each, pick a sensible DEFAULT and say why (one line).
3) THEN implement, matching your defaults.
```

Score each output with the rubric above. (Prefer a judge model that is *not* one of the models under test.)
