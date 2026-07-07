# Benchmark — does the `fable-workflow` skill change model behavior?

**Audience:** anyone deciding whether to adopt this skill, and anyone who wants to reproduce or extend the evaluation.

**Question it answers:** when a model is given an under-specified task, does injecting the `fable-workflow` skill improve the **quality of its answer and its thinking** — and does that help more on some models than others?

> ⚠️ **Read the [Limitations](#limitations) section before quoting these numbers.** This is a small directional pilot (n=1 task, single trial, self-judged, coarse bands), not a statistically robust leaderboard.

---

## TL;DR

![benchmark chart](bench.png)

Scored on **answer + thinking quality**, out of **100**.

| Model | Type | No skill | With skill | Δ |
|---|---|:---:|:---:|:---:|
| llama3:8b | local | 20 | 50 | **+30** |
| gemma3:4b | local | 40 | 50 | +10 |
| **Haiku 4.5** | cloud | 50 | 80 | **+30** |
| qwen2.5:7b | local | 60 | 60 | 0 |
| **Sonnet 5** | cloud | 90 | 100 | +10 |
| **Opus 4.8** | cloud | 90 | 100 | +10 |
| qwen3.6 | local | 90 | 100 | +10 |
| **Fable 5** | cloud | 100 | 100 | 0 |

Measuring **answer + thinking quality** (not merely "did it list the unknowns") tells a sharper, more honest story: the skill is a **reasoning amplifier, not a coding amplifier.** It reliably lifts *thinking* — the model reasons about the real decisions — but *answer* quality only rises when the model can also **execute** that plan. So the biggest total-quality gains land on **capable-but-under-reasoning** models (llama3:8b 20→50, Haiku 4.5 50→80, both +30). At the extremes the gain fades: the already-excellent have no room (Fable 100→100; frontier +10), and the weakest coders improve their *plan* but still ship broken code (gemma3 +10; qwen2.5:7b **net 0** — better reasoning, but it dropped an `import`). **Surfacing unknowns ≠ better code.**

---

## What was tested

### Task (identical for every run)

A deliberately under-specified spec, framed as a one-shot autonomous job (the model **cannot** ask questions):

> **TASK:** Add rate limiting to our web API.
> **SPEC (verbatim from the product owner):** *"Users shouldn't be able to spam our API. Limit it to 100 requests per minute."*
> Deliver a Python rate-limiter implementation plus a short note.

This spec hides at least ~8 **architecture- or behavior-changing unknowns**: scope (per-IP / per-user / per-key / global), window algorithm (fixed / sliding / token-bucket — fixed allows a 2× boundary burst), storage (in-memory / distributed), over-limit behavior (429 / queue / `Retry-After`), burst tolerance, concurrency (thread safety), clock source (wall vs monotonic), and memory growth (idle-key eviction).

### Conditions

- **No skill:** the task prompt alone.
- **With skill:** the same task + the skill's one-shot instruction (surface an UNKNOWNS list first, pick a default per item with a one-line reason, then implement).

### Models

- **Cloud (Anthropic):** Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5 — identical `general-purpose` subagents.
- **Local (ollama, RTX 3080 Ti 16 GB):** qwen3.6, qwen2.5:7b, llama3:8b, gemma3:4b — via `ollama run` with the identical prompts.

8 models × 2 conditions = **16 runs**. (GLM 5.2 was requested but **not run** — no API key was available.)

### Rubric (out of 100) — answer + thinking quality

Each run is judged holistically on a 0–100 scale that blends two things:

- **Thinking quality** — did it reason correctly about the *real* decisions and tradeoffs (scope, window algorithm, concurrency, storage, edge cases like the boundary burst and clock source)?
- **Answer quality** — is the delivered code + note actually correct and usable (enforces 100/min, thread-safe, right window semantics, no crashes / missing imports)?

Scored in coarse 10-point bands. Treat ±10 as noise (see [Limitations](#limitations)).

---

## Per-model evidence

### Cloud
- **Fable 5 (100 → 100).** Excellent reasoning *and* correct, self-verified code in both conditions — a genuine ceiling. The skill has nothing to add.
- **Sonnet 5 / Opus 4.8 (90 → 100, +10).** Strong reasoning + correct implementations (`Retry-After`, self-checks) even unaided; the skill mostly reshaped the reasoning into an explicit prioritized form and tightened the output.
- **Haiku 4.5 (50 → 80, +30) — the clearest cloud win.** Unaided it *mis-reasoned* — it called a fixed-window counter a "token bucket," carrying the 200-request boundary-burst bug. The skill fixed both the reasoning (correct sliding window) and the answer.

### Local (ollama)
- **qwen3.6 (90 → 100, +10).** A local reasoning model whose visible "thinking" already reasons through the decisions (scope, sliding-vs-fixed, clock source) and writes correct thread-safe code — it behaves like the frontier.
- **llama3:8b (20 → 50, +30) — the biggest single jump.** Unaided it produced no real reasoning and broken code (`dict.keys()[0]` crashes, incoherent threading). The skill gave it a coherent plan and workable-ish code.
- **gemma3:4b (40 → 50, +10) & qwen2.5:7b (60 → 60, 0).** The skill improved their *reasoning* (real unknowns, sensible defaults) but their *code stayed broken* — gemma3 shipped no time window at all; qwen2.5 dropped `import time` and stubbed its state. So total quality barely moved. This is the clearest evidence that **on weak models the skill lifts thinking, not implementation.**

## Interpretation

On answer + thinking quality, the skill is a **reasoning amplifier, not a coding amplifier.** It reliably makes a model reason about the right decisions; whether that becomes a better *answer* depends on whether the model can already code the plan. Net effect: the biggest quality gains go to **capable-but-under-reasoning** models (llama3:8b, Haiku 4.5); little to the already-excellent (no room) or the weakest coders (better plan, still-broken code). **Capability, not vendor, sets the ceiling** — a strong local model (qwen3.6) sits with the frontier.

---

## Limitations

Do not over-read these numbers.

- **n = 1 task, single trial, no repeats.** No error bars.
- **Coarse 10-point bands, single sample → treat ±10 as noise.** The qwen2.5:7b "0" and the exact frontier "+10"s are within noise; the *pattern* (thinking up, answer only when the model can code) is the takeaway, not any individual cell.
- **Self-judged.** Scoring was done by one of the contestant models (Opus 4.8), a bias risk — especially for the Opus row.
- **One-shot autonomous only tests one slice of the skill.** The interactive moves — *interview me*, *blind-spot pass over a real codebase*, *N variants*, *quiz-back before merge* — do not fire in a single autonomous shot.
- **GLM 5.2 was not run** — no API key available. Provide a Zhipu / OpenRouter key to add it.
- **Single task domain** (rate limiting). Results may not transfer to other kinds of ambiguity.

### To make it robust
- Use a **neutral judge** model (not a contestant) — ideally an ensemble — to score answer + thinking quality.
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

Judge each output on **answer + thinking quality** (out of 100) using the rubric above. Prefer a judge that is *not* one of the models under test.
