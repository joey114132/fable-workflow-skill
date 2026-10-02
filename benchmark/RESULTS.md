# Benchmark: does the `fable-workflow` skill change model behavior?

**Audience:** anyone deciding whether to adopt this skill, and anyone who wants to reproduce or extend the evaluation.

**Question it answers:** when a model is given an under-specified task, does injecting the `fable-workflow` skill improve the **quality of its answer and its thinking**, and does it help some models more than others?

**Models tested (pilot, run July 2026):** Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5 (cloud), plus four local models. As of 2026-10-02 Anthropic lists Fable 5.1, Opus 5.5, Sonnet 5.5 and Haiku 4.5 as current, and Fable 5, Opus 4.8 and Sonnet 5 as legacy. Only the Haiku 4.5 row therefore describes a current model, and the Opus 4.8 judge is also a legacy model. On 2026-10-02 Opus 5.5 and Sonnet 5.5 were added with one draw each (see [Opus 5.5 and Sonnet 5.5 re-run](#opus-55-and-sonnet-55-re-run-2026-10-02-n1)). Fable 5.1 and Haiku 4.5 were not re-measured.

**What replaces it:** this pilot tested a short one-shot prompt, not the shipped plugin. The reproducible check of the shipped plugin is the `evals/` suite (`claude plugin eval . --no-publish`, see the repo [README](../README.md#evals)). The numbers below are kept as a historical, directional pilot.

> Read the [Limitations](#limitations) before quoting these numbers. This is a directional pilot (n=1 task, **a single trial per cell in the headline run**, self-judged). Later local re-runs are listed below. One cell even went *down* on the headline run (gemma3:4b) purely from run-to-run variance, as the re-runs show.

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
| **Sonnet 5.5** (2026-10-02) | cloud | 44 → 46 | 46 → 45 | **90 → 91** | +1 |
| **Sonnet 5** | cloud | 43 → 48 | 48 → 50 | **91 → 98** | +7 |
| **Opus 5.5** (2026-10-02) | cloud | 46 → 48 | 47 → 47 | **93 → 95** | +2 |
| **Opus 4.8** | cloud | 46 → 48 | 49 → 50 | **95 → 98** | +3 |
| **Fable 5** | cloud | 46 → 50 | 50 → 50 | **96 → 100** | +4 |

The skill's effect is asymmetric:

- **Thinking quality goes up for every model in the headline run** (+2 to +18), and for the three weak and mid locals in the independent reproduction. The strongest local model (qwen3.6) is the exception there (Thinking 40 → 32). The skill reliably makes weaker models reason about the real decisions.
- **Answer quality only rises when the model can already code the plan.** For the frontier it climbs a little (already near-ceiling); for weak local models it's **flat or negative**. gemma3:4b's *answer* score fell 37→8 because, unaided, it happened to write a correct sliding-window limiter, while with the skill it reasoned more but shipped broken counting logic.

So the skill improved the models' reasoning more than their code. Biggest total gains land on capable-but-under-reasoning models (llama3:8b +19, Haiku 4.5 +15). Fable 5 earns **96 unaided** (not a free 100) and tops out at 100 with the skill.

---

## What was tested

### Task (identical for every run)

A deliberately under-specified spec, one-shot autonomous (the model **cannot** ask questions):

> **TASK:** Add rate limiting to our web API.
> **SPEC (verbatim from the product owner):** *"Users shouldn't be able to spam our API. Limit it to 100 requests per minute."*
> Deliver a Python rate-limiter implementation plus a short note.

It hides ~8 architecture-/behavior-changing unknowns: scope (per-IP / per-user / per-key / global), window algorithm (fixed / sliding / token-bucket; fixed allows a 2× boundary burst), storage (in-memory / distributed), over-limit behavior (429 / `Retry-After`), burst tolerance, concurrency (thread safety), clock source (wall vs monotonic), memory growth (idle-key eviction).

### Conditions

- **No skill:** the task prompt alone.
- **With skill:** the same task + the skill's one-shot instruction (surface an UNKNOWNS list with defaults + reasons, then implement).

### Models (8 × 2 = 16 runs in the headline run)

- **Cloud (Anthropic):** Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5, as identical `general-purpose` subagents.
- **Local (ollama, RTX 3080 Ti 16 GB):** qwen3.6, qwen2.5:7b, llama3:8b, gemma3:4b, via `ollama run` with the identical prompts.

### Detailed rubric (out of 100)

Each output is scored against explicit, checkable criteria, not a coarse band.

**Thinking / analysis: 50 pts**
| Criterion | Pts |
|---|:---:|
| Unknowns coverage (4 pts each × 8 reference unknowns) | 0–32 |
| Justification quality (defaults backed by sound tradeoff reasoning) | 0–10 |
| Edge-case awareness (names the boundary-burst and/or multi-worker N×limit issue) | 0–8 |

**Answer / implementation: 50 pts**
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
- **Fable 5 (96 → 100).** Unaided: correct sliding-window, thread-safe, monotonic clock, `Retry-After` fully wired, self-verified. It didn't *explicitly* name clock-source as a decision and skipped burst, so it scored **96, not 100**. With the skill: 9 unknowns incl. the subtle *"do rejected requests consume budget?"*, plus a rigorous injected-clock self-check → 100.
- **Sonnet 5 (91 → 98) / Opus 4.8 (95 → 98).** Strong reasoning + correct token-bucket/sliding implementations even unaided; the skill mostly reshaped the reasoning into an explicit prioritized list (+7 / +3).
- **Haiku 4.5 (66 → 81), the clearest cloud win.** Unaided it *mis-reasoned*: called a fixed-window counter a "token bucket," carrying the boundary-burst bug. The skill fixed both the reasoning (correct sliding window) and the answer (+15).

### Local (ollama)
- **qwen3.6 (82 → 87).** A local reasoning model whose thinking trace already reasons through the decisions, and it writes correct thread-safe code. Behaves like the frontier; small lift (+5).
- **llama3:8b (8 → 27), the biggest jump.** Unaided: no real reasoning and broken code (a counter that never actually limits). With the skill: a coherent UNKNOWNS list and structured code, but the implementation is still shaky (+19, almost all of it in *Thinking*).
- **qwen2.5:7b (44 → 54) & gemma3:4b (50 → 38).** Both show the asymmetry. Their **Thinking** jumped (+18, +17). Their **Answer** *fell* (−8, −29): unaided, each happened to emit a clean sliding-window counter; with the skill they spent effort on unknowns and shipped worse code (qwen2.5 dropped a clean design; gemma3 wrote non-functional counting logic). gemma3's total therefore went **negative**, an n=1 variance artifact.

## Opus 5.5 and Sonnet 5.5 re-run (2026-10-02, n=1)

Same task, same two prompts, same /100 rubric. One draw per cell, so the deltas below are inside the noise this file documents.

| Model | Think (no→with) | Answer (no→with) | **Total (no→with)** | Δ |
|---|:---:|:---:|:---:|:---:|
| Opus 5.5 (`claude-opus-5-5`) | 46 → 48 | 47 → 47 | **93 → 95** | +2 |
| Sonnet 5.5 (`claude-sonnet-5-5`) | 44 → 46 | 46 → 45 | **90 → 91** | +1 |

Both models land at 90 or above unaided, so there is little room to gain. Thinking rose by 2 for each. Answer did not move for Opus 5.5 and fell by 1 for Sonnet 5.5. Each model's unaided reply named seven of the eight reference unknowns. Opus 5.5 with the skill named all eight, and Sonnet 5.5 with the skill still left clock source only partly covered, so the Think gains are one unknown or less.

How it was run. Each arm was a single `claude -p --model <id> --tools ""` call with a minimal system prompt ("Answer directly in plain text. No tools are available."), no MCP servers, no skills, and a scratch `CLAUDE_CONFIG_DIR` so that no user hooks, plugins or CLAUDE.md reached the model. The judge was Opus 4.8 (`claude-opus-4-8`, a legacy model that is not under test in this re-run). The four replies were shuffled under neutral labels and scored against the rubric above in separate calls. The first attempts with the default system prompt made the models try tool calls, stalled or returned no text, so they were discarded and the four arms were rerun under the same settings. Raw replies were not kept in the repository. Reply cost was about 0.44 USD.

Differences from the July pilot. July used `general-purpose` subagents and this re-run uses a bare `claude -p` call, and the judge is a different, non-contestant model. The two sets of rows are therefore not strictly comparable. Fable 5.1 was not re-run.

---

## Interpretation

On answer + thinking quality, the skill improved reasoning more than code. It reliably makes a model reason about the right decisions (Thinking up for all 8 models in the headline run, but not for qwen3.6 in the 2026-07-08 reproduction); whether that becomes a better *answer* depends on whether the model can already code the plan. Net: biggest total gains for **capable-but-under-reasoning** models (llama3, Haiku); small for the already-excellent (no room); noisy or negative for weak local coders (better plan, worse or unchanged code). **Capability, not vendor, sets the ceiling**: a strong local model (qwen3.6) sits with the frontier.

---

## Local reproducibility: a second trial (the n=1 warning, demonstrated)

I re-ran the four local models (same task, same rubric). Scores swung hard between identical runs, which is direct evidence that single-trial local numbers are mostly noise:

| Local model | Trial 1 (no→with, Δ) | Trial 2 (no→with, Δ) | 2-trial avg Δ |
|---|:---:|:---:|:---:|
| llama3:8b | 8→27 (+19) | 8→22 (+14) | **+16** |
| gemma3:4b | 50→38 (**−12**) | 18→60 (**+42**) | **+15** |
| qwen2.5:7b | 44→54 (+10) | 32→55 (+23) | **+16** |
| qwen3.6 | 82→87 (+5) | 82→70 (−12) | **−4** |

- **Single-trial local Δ is dominated by variance.** gemma3:4b swung from −12 to +42 between identical runs; qwen3.6 from +5 to −12. Trial 1's gemma3 −12 (flagged as an artifact) is **confirmed noise**.
- **The *no-skill* arm is the noisy one.** With-skill scores varied less than no-skill scores across trials 1 and 2 for qwen2.5 (54/55) but not for gemma3 (38/60), and qwen2.5 fell to 26 in the independent run below. The no-skill draws swing (gemma3 50 vs 18): a weak model randomly either lands on the common correct pattern or improvises a broken one.
- **Averaged (n=2), the mid-tier locals are net positive** (+15 to +16), so the skill helps them on average, while the strongest local (qwen3.6) is a wash-to-slightly-negative (−4): with the skill it sometimes picks a simpler fixed-window (no lock) instead of its own unaided sliding-window, so it has nothing to gain.

**Don't trust any single local Δ.** Cloud models weren't re-run, so treat their deltas as single-trial too. Real conclusions need n ≥ 3.

---

## Independent reproduction: local, 2026-07-08 (n=1)

A further single-trial run of the **local** arm on separate hardware, following the
[Reproduce](#reproduce) steps verbatim, with the same task, the same two prompts and the same /100 rubric.
Judge: Opus 4.8 (same self-judge caveat as above). One draw per cell, so **every Δ here is
noise-dominated** per the warning directly above. It is one more data point toward the
"run 3–5 trials" goal, not a verdict. Reported in full, including the two cells that landed
*lower* than the headline run.

| Model | Think (no→with) | Answer (no→with) | **Total (no→with)** | Δ |
|---|:---:|:---:|:---:|:---:|
| llama3:8b | 2 → 17 | 6 → 15 | **8 → 32** | +24 |
| gemma3:4b | 15 → 24 | 36 → 37 | **51 → 61** | +10 |
| qwen2.5:7b | 8 → 22 | 18 → 4 | **26 → 26** | 0 |
| qwen3.6 | 40 → 32 | 50 → 43 | **90 → 75** | −15 |

**Confirms the core asymmetry.** Thinking rose for the three weak/mid models (+15, +9, +14);
Answer only rose where the model could already code the plan (llama3 +9, gemma3 +1) and fell
where it couldn't (qwen2.5 −14, shipping a misused external lib after reasoning more).
llama3's no-skill total landed on **8**, identical to Trial 1's, an independent match on a
model that, unaided, writes a counter that never limits.

**Diverges on qwen3.6** (90 → 75, Δ −15). Its *Thinking* dipped rather than rising: with the
skill it reasoned itself from a correct **sliding** window into a simpler **fixed** window,
reintroducing the boundary-burst bug and dropping the multi-worker note it made unaided, so
it stopped reasoning about those edges. Same mechanism the n=2 table flags for the strongest
local model ("picks a simpler fixed-window… nothing to gain"), landing on the negative side of
its variance envelope this draw.

---

## Limitations

- **n = 1 for cloud; n = 3 for local (two own trials plus one independent run on different hardware and judge, not pooled; see above).** Local Δs swing wildly run-to-run (gemma3:4b: −12 then +42), **confirming** single-trial numbers are mostly noise. Treat any single Δ, cloud or local, as directional only; real conclusions need n ≥ 3.
- **Self-judged in July.** The July cloud scoring was done by one of the contestant models (Opus 4.8), a bias risk, especially for the Opus row. The 2026-10-02 re-run used Opus 4.8 as a judge for models that are not Opus 4.8, so that bias does not apply to those two rows, but a single judge still scores them.
- **One-shot autonomous tests only one slice of the skill.** The interactive moves (*interview me*, *blind-spot pass over a real codebase*, *N variants*, *quiz-back before merge*) do not fire in a single autonomous shot.
- **The with-skill arm is a short one-shot prompt.** It is not the current `SKILL.md`, the hooks, the standing orders, or the small-model variant, so these numbers do not measure the shipped plugin.
- **Models are dated.** Three of the four July cloud models and the Opus 4.8 judge are now legacy (see the note at the top). Only the Opus 5.5 and Sonnet 5.5 rows come from the current lineup, and they have n=1. The two rows measured in July for the same families (Opus 4.8, Sonnet 5) differ by setup as well as by model.
- **Single task domain** (rate limiting). Results may not transfer.

### To make it robust
- Use a **neutral judge** (not a contestant), ideally an ensemble.
- Run **3–5 trials per cell** and report mean ± spread. That alone would erase the gemma3 artifact.
- Broaden to **several task domains**.

---

## Reproduce

**Cloud:** for each of {Fable 5, Opus 4.8, Sonnet 5, Haiku 4.5} × {no skill, with skill}, run an identical autonomous agent on the task above. That was the July 2026 lineup. The 2026-10-02 re-run used `claude -p --model claude-opus-5-5` and `claude -p --model claude-sonnet-5-5` with the settings described in the re-run section above.
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

## First `claude plugin eval` run (2026-10-02, plugin 1.1.0)

Seven behavior cases from `evals/`, one run per case and arm, `--allow-tools WebSearch WebFetch`, Haiku as the judge, about 2.1 USD. Mean with-minus-without delta was -0.14: six cases tied and the interview case scored 0 with the plugin against 1 without. The with-plugin reply stated assumptions and a design direction instead of asking only design-changing questions. The skill itself was invoked in 0 of 7 with-plugin runs, so the with arm differed from the baseline only by the one-line hook. Overall the with-plugin arm passed 4 of 7 cases (overall score 0.75). Two cases failed in both arms: `trivial-fix-no-ceremony` (0.75) and `underspecified-build-defaults` (0.5). The `SKILL.md` description was edited after this run while the plugin version stayed at 1.1.0, so these numbers describe the earlier description. Read this as a first data point, not a verdict. One run per arm is inside the noise this file already documents, and the next measurement should use `--runs 3` and a description that actually triggers the skill.
