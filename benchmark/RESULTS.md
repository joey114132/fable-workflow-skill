# Benchmark — does the `fable-workflow` skill change model behavior?

**Audience:** anyone deciding whether to adopt this skill, and anyone who wants to reproduce or extend the evaluation.

**Question it answers:** when a model is given an under-specified task, does injecting the `fable-workflow` skill make it *surface the hidden decisions first* — and does that help more on some models than others?

> ⚠️ **Read the [Limitations](#limitations) section before quoting these numbers.** This is a small directional pilot (n=1 task, single trial, self-judged), not a statistically robust leaderboard.

---

## TL;DR

![benchmark chart](bench.png)

Scores are out of **100**.

| Model | Type | No skill | With skill | Δ |
|---|---|:---:|:---:|:---:|
| llama3:8b | local | 10 | 60 | **+50** |
| gemma3:4b | local | 40 | 70 | +30 |
| **Haiku 4.5** | cloud | 40 | 80 | **+40** |
| qwen2.5:7b | local | 50 | 70 | +20 |
| qwen3.6 | local | 90 | 100 | +10 |
| **Sonnet 5** | cloud | 90 | 100 | +10 |
| **Opus 4.8** | cloud | 90 | 100 | +10 |
| **Fable 5** | cloud | 100 | 100 | 0 |

The skill's job — porting Fable 5's native "find-the-unknowns-first" behavior onto other models — shows up cleanly, and **the lift tracks base weakness**: the weaker a model is unaided, the more the skill helps (llama3:8b +50 → frontier +10 → Fable +0). This holds across **both cloud and local** models — a strong local reasoning model (qwen3.6) behaves like the frontier (near-ceiling, +10), while weak locals gain the most.

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

- **Cloud (Anthropic):** Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5 — spawned as identical `general-purpose` subagents, output capped at ~400 words + code.
- **Local (ollama, RTX 3080 Ti 16 GB):** qwen3.6, qwen2.5:7b, llama3:8b, gemma3:4b — run via `ollama run` with the identical prompts.

8 models × 2 conditions = **16 runs**. (GLM 5.2 was requested but **not run** — no API key was available in the environment.)

### Rubric (out of 100)

| Dimension | Points | What earns them |
|---|:---:|---|
| **Unknowns surfaced** | 0–50 | Count of genuine, distinct, architecture/behavior-changing unknowns raised |
| **Assumptions logged** | 0–20 | Defaults stated explicitly, each with a reason |
| **Implementation quality** | 0–30 | Actually enforces 100/min, thread-safe, correct on the window-boundary edge case |

---

## Per-model evidence

### Cloud
- **Fable 5 is the "native" of this workflow.** *Without* the skill it already surfaced 6 unknowns as a labeled decisions list (including the subtle **clock-source** one), logged every default with a reason, and **ran its own self-check** before answering. *With* the skill it went further — flagging *"this repo has no web API to attach to"* and *"do rejected requests consume tokens?"* (9 unknowns). Nothing to improve on a perfect 100.
- **Haiku 4.5 — the clearest cloud win.** *Without* the skill it mislabeled a **fixed-window** counter as a "token bucket" (carrying the 200-request boundary-burst bug) and surfaced only 2 unknowns → **40/100**. *With* the skill: correct sliding window + a 7-row unknowns table → **80/100** (+40).
- **Opus 4.8 / Sonnet 5 were already near-ceiling.** Both surfaced most unknowns in prose even without the skill (correct sliding-window / token-bucket implementations, `Retry-After`, self-checks). The skill mainly reshaped that reasoning into an explicit, prioritized list (+10 each).

### Local (ollama)
- **qwen3.6 matched the frontier.** This local reasoning model's visible "thinking" trace *already* enumerates unknowns unaided (scope, sliding-vs-fixed window, storage, clock source) → **90** no-skill; with the skill it produced a clean per-IP fixed-window, thread-safe limiter with `Retry-After` and an eviction note → **100** (+10). Same shape as Opus/Sonnet.
- **Weak locals gained the most — but on the *unknowns* dimension, not the code.** llama3:8b unaided emitted broken code (`dict.keys()[0]` crashes, incoherent threading) and surfaced ~0 unknowns → **10**; with the skill it produced a 3-item UNKNOWNS list with defaults and a coherent counter → **60** (+50). gemma3:4b (**40→70**, +30) and qwen2.5:7b (**50→70**, +20) show the same pattern: the skill reliably adds the *surface-the-unknowns* behavior even when the generated **code still has bugs** (missing `import`, no time window, no lock). So their with-skill gains come from the Unknowns/Assumptions dimensions — **not** implementation quality.

## Interpretation

The skill is **not** a uniform quality boost. Its measurable effect is concentrated exactly where the theory predicts: models that don't spontaneously "find the unknowns" get the biggest lift. Frontier models mostly already do it; Fable 5 does it by default. So the skill's real value is **leveling up weaker models to the frontier's default behavior** on ambiguous specs. The local runs sharpen this: **capability, not vendor, predicts the lift** — a strong local model (qwen3.6) needs the skill as little as a frontier cloud model, while a weak one (llama3:8b) needs it most.

---

## Limitations

Do not over-read these numbers.

- **n = 1 task, single trial, no repeats.** No error bars. Scores are directional.
- **Self-judged.** Scoring was done by one of the contestant models (Opus 4.8), a bias risk — especially for the Opus row.
- **One-shot autonomous can only test one slice of the skill.** The interactive moves — *interview me*, *blind-spot pass over a real codebase*, *N variants*, *quiz-back before merge* — do not fire in a single autonomous shot. The measured gain is only the **surface-the-unknowns** behavior.
- **Local models: code quality stayed low regardless of the skill.** Their with-skill gains are mostly in *surfacing unknowns*, not working code (missing imports, no time window, crashes). The rubric rewards the former — do **not** read the local with-skill scores as "production-ready output."
- **GLM 5.2 was not run** — no API key available. Provide a Zhipu / OpenRouter key to add it.
- **Single task domain** (rate limiting). Results may not transfer to other kinds of ambiguity.

### To make it robust
- Add the multi-turn tasks (interview / variants) with a **neutral judge** model (not a contestant).
- Run **3–5 trials per cell** for variance.
- Broaden to **several task domains**.

---

## Reproduce

**Cloud:** for each of {Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5} × {no skill, with skill}, run an identical autonomous agent on the task above.
**Local:** same two prompts via ollama:

```bash
ollama run <model> "$(cat prompt_noskill.txt)"      # no-skill arm
ollama run <model> "$(cat prompt_withskill.txt)"    # with-skill arm
```

For the **with-skill** arm, the prompt prepends:

```
Follow this working method (Fable workflow):
The spec is a MAP; the real system is the TERRITORY. Wherever the spec is silent
there is an UNKNOWN — a decision it didn't make. Since you can't ask me:
1) FIRST write an "UNKNOWNS" list — the open decision points — prioritising ones
   that change the architecture or behaviour.
2) For each, pick a sensible DEFAULT and say why (one line).
3) THEN implement, matching your defaults.
```

Score each output with the rubric above (out of 100). Prefer a judge model that is *not* one of the models under test.
