# Benchmark — does the `fable-workflow` skill change model behavior?

**Audience:** anyone deciding whether to adopt this skill, and anyone who wants to reproduce or extend the evaluation.

**Question it answers:** when a model is given an under-specified task, does injecting the `fable-workflow` skill improve the **quality of its answer and its thinking** — and does that help more on some models than others?

> ⚠️ **Read the [Limitations](#limitations) before quoting these numbers.** This is a directional pilot (n=1 task, **single trial**, self-judged). One cell even went *down* on this run (gemma3:4b) purely from run-to-run variance — see below.

---

## TL;DR

![benchmark chart](bench.png)

Every run is scored on **answer + thinking quality out of 100**, split into two halves:

| Model | Type | Think /50 (no→with) | Answer /50 (no→with) | **Total (no→with)** | Δ |
|---|---|:---:|:---:|:---:|:---:|
| llama3:8b | local | 3 → 19 | 5 → 8 | **8 → 27** | +19 |
| qwen2.5:7b | local | 11 → 29 | 33 → 25 | **44 → 54** | +10 |
| gemma3:4b | local | 13 → 30 | 37 → 8 | **50 → 38** | **−12** |
| **Haiku 4.5** | cloud | 27 → 39 | 39 → 42 | **66 → 81** | +15 |
| qwen3.6 | local | 34 → 38 | 48 → 49 | **82 → 87** | +5 |
| **Sonnet 5** | cloud | 43 → 48 | 48 → 50 | **91 → 98** | +7 |
| **Opus 4.8** | cloud | 46 → 48 | 49 → 50 | **95 → 98** | +3 |
| **Fable 5** | cloud | 46 → 50 | 50 → 50 | **96 → 100** | +4 |

**The split is the finding.** The skill's effect is asymmetric:

- **Thinking quality goes up for *every* model, no exceptions** (+2 to +18). The skill reliably makes a model reason about the real decisions.
- **Answer quality only rises when the model can already code the plan.** For the frontier it climbs a little (already near-ceiling); for weak local models it's **flat or negative** — gemma3:4b's *answer* score fell 37→8 because, unaided, it happened to write a correct sliding-window limiter, while with the skill it reasoned more but shipped broken counting logic.

So: **the skill is a reasoning amplifier, not a coding amplifier.** Biggest total gains land on capable-but-under-reasoning models (llama3:8b +19, Haiku 4.5 +15). Fable 5 earns **96 unaided** (not a free 100) and tops out at 100 with the skill.

---

## What was tested

### Task (identical for every run)

A deliberately under-specified spec, one-shot autonomous (the model **cannot** ask questions):

> **TASK:** Add rate limiting to our web API.
> **SPEC (verbatim from the product owner):** *"Users shouldn't be able to spam our API. Limit it to 100 requests per minute."*
> Deliver a Python rate-limiter implementation plus a short note.

It hides ~8 architecture-/behavior-changing unknowns: scope (per-IP / per-user / per-key / global), window algorithm (fixed / sliding / token-bucket — fixed allows a 2× boundary burst), storage (in-memory / distributed), over-limit behavior (429 / `Retry-After`), burst tolerance, concurrency (thread safety), clock source (wall vs monotonic), memory growth (idle-key eviction).

### Conditions

- **No skill:** the task prompt alone.
- **With skill:** the same task + the skill's one-shot instruction (surface an UNKNOWNS list with defaults + reasons, then implement).

### Models (8 × 2 = 16 runs)

- **Cloud (Anthropic):** Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5 — identical `general-purpose` subagents.
- **Local (ollama, RTX 3080 Ti 16 GB):** qwen3.6, qwen2.5:7b, llama3:8b, gemma3:4b — via `ollama run` with the identical prompts.

### Detailed rubric (out of 100)

Each output is scored against explicit, checkable criteria — not a coarse band.

**Thinking / analysis — 50 pts**
| Criterion | Pts |
|---|:---:|
| Unknowns coverage (4 pts each × 8 reference unknowns) | 0–32 |
| Justification quality (defaults backed by sound tradeoff reasoning) | 0–10 |
| Edge-case awareness (names the boundary-burst and/or multi-worker N×limit issue) | 0–8 |

**Answer / implementation — 50 pts**
| Criterion | Pts |
|---|:---:|
| Enforces the limit correctly (100 / window) | 0–12 |
| Correct window semantics (no silent boundary-burst bug) | 0–8 |
| Thread-safe (lock / atomic) | 0–8 |
| Per-key / scope implemented (not just one global bucket) | 0–8 |
| Over-limit response (429 + `Retry-After`) | 0–6 |
| Runs without fatal bugs (imports present, no crash, not a non-functional stub) | 0–8 |

---

## Per-model evidence

### Cloud
- **Fable 5 (96 → 100).** Unaided: correct sliding-window, thread-safe, monotonic clock, `Retry-After` fully wired, self-verified — but didn't *explicitly* name clock-source as a decision and skipped burst, so **96, not 100**. With the skill: 9 unknowns incl. the subtle *"do rejected requests consume budget?"*, plus a rigorous injected-clock self-check → 100.
- **Sonnet 5 (91 → 98) / Opus 4.8 (95 → 98).** Strong reasoning + correct token-bucket/sliding implementations even unaided; the skill mostly reshaped the reasoning into an explicit prioritized list (+7 / +3).
- **Haiku 4.5 (66 → 81) — clearest cloud win.** Unaided it *mis-reasoned*: called a fixed-window counter a "token bucket," carrying the boundary-burst bug. The skill fixed both the reasoning (correct sliding window) and the answer (+15).

### Local (ollama)
- **qwen3.6 (82 → 87).** A local reasoning model — its thinking trace already reasons through the decisions and it writes correct thread-safe code. Behaves like the frontier; small lift (+5).
- **llama3:8b (8 → 27) — biggest jump.** Unaided: no real reasoning and broken code (a counter that never actually limits). With the skill: a coherent UNKNOWNS list and structured code — though the implementation is still shaky (+19, almost all of it in *Thinking*).
- **qwen2.5:7b (44 → 54) & gemma3:4b (50 → 38).** Both show the asymmetry starkly. Their **Thinking** jumped (+18, +17). Their **Answer** *fell* (−8, −29): unaided, each happened to emit a clean sliding-window counter; with the skill they spent effort on unknowns and shipped worse code (qwen2.5 dropped a clean design; gemma3 wrote non-functional counting logic). gemma3's total therefore went **negative** — a vivid n=1 variance artifact.

## Interpretation

On answer + thinking quality, the skill is a **reasoning amplifier, not a coding amplifier.** It reliably makes a model reason about the right decisions (Thinking up for all 8 models); whether that becomes a better *answer* depends on whether the model can already code the plan. Net: biggest total gains for **capable-but-under-reasoning** models (llama3, Haiku); small for the already-excellent (no room); noisy or negative for weak local coders (better plan, worse or unchanged code). **Capability, not vendor, sets the ceiling** — a strong local model (qwen3.6) sits with the frontier.

---

## Local reproducibility — a second trial (the n=1 warning, demonstrated)

I re-ran the four local models (same task, same rubric). Scores swung hard between identical runs — direct evidence that single-trial local numbers are mostly noise:

| Local model | Trial 1 (no→with, Δ) | Trial 2 (no→with, Δ) | 2-trial avg Δ |
|---|:---:|:---:|:---:|
| llama3:8b | 8→27 (+19) | 8→22 (+14) | **+16** |
| gemma3:4b | 50→38 (**−12**) | 18→60 (**+42**) | **+15** |
| qwen2.5:7b | 44→54 (+10) | 32→55 (+23) | **+16** |
| qwen3.6 | 82→87 (+5) | 82→70 (−12) | **−4** |

- **Single-trial local Δ is dominated by variance.** gemma3:4b swung from −12 to +42 between identical runs; qwen3.6 from +5 to −12. Trial 1's gemma3 −12 (flagged as an artifact) is **confirmed noise**.
- **The *no-skill* arm is the noisy one.** With-skill scores are relatively stable (gemma3 38/60, qwen2.5 54/55); the no-skill draws swing (gemma3 50 vs 18) — a weak model randomly either lands on the common correct pattern or improvises a broken one.
- **Averaged (n=2), the mid-tier locals are net positive** (+15 to +16) — the skill helps them on average — while the strongest local (qwen3.6) is a wash-to-slightly-negative (−4): with the skill it sometimes picks a simpler fixed-window (no lock) instead of its own unaided sliding-window, so it has nothing to gain.

**Don't trust any single local Δ.** Cloud models weren't re-run — treat their deltas as single-trial too. Real conclusions need n ≥ 3.

---

## Limitations

- **n = 1 for cloud; n = 2 for local (see reproducibility above).** Local Δs swing wildly run-to-run (gemma3:4b: −12 then +42), **confirming** single-trial numbers are mostly noise. Treat any single Δ — cloud or local — as directional only; real conclusions need n ≥ 3.
- **Self-judged.** Scoring was done by one of the contestant models (Opus 4.8), a bias risk — especially the Opus row.
- **One-shot autonomous tests only one slice of the skill.** The interactive moves — *interview me*, *blind-spot pass over a real codebase*, *N variants*, *quiz-back before merge* — do not fire in a single autonomous shot.
- **Single task domain** (rate limiting). Results may not transfer.

### To make it robust
- Use a **neutral judge** (not a contestant), ideally an ensemble.
- Run **3–5 trials per cell** and report mean ± spread — this alone would erase the gemma3 artifact.
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

Score each output against the detailed rubric above (Thinking /50 + Answer /50). Prefer a judge that is *not* one of the models under test.
