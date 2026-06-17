# RLM skill — OOLONG (`trec_coarse`) eval run

**Method:** the `rlm` skill (Recursive Language Model loop) · **Leaf model:** `haiku` · **Date:** 2026-06-17

## TL;DR

| Metric | Value |
|---|---|
| **Eval score (mean)** | **0.5422 → 54.2%** (10 items, official OOLONG-synth scorer) |
| **Total tokens** | **12,142,040** (mean 1,214,204 / item) |
| **Total cost** | **$13.38** (mean $1.34 / item) |
| **End-to-end wall time** | **2,956 s = 49.3 min** (mean 295.6 s / item) |
| Leaf sub-LM calls | 322 (mean 32.2 / item) · 1 failed call, auto-recovered |
| Classification coverage | **3,182 / 3,182 on every item** (0 unmapped labels) |

Score breakdown by answer type: **LABEL 2/2 (100%)**, **COMPARISON 3/4 (75%)**, **NUMERIC 0.42/4 (10.5%)**.

For reference, the paper's Table 1 OOLONG column (N=131K) reports **GPT-5 base = 44.0 → RLM = 56–58**.
This run (a *cheaper* `haiku` leaf, same upstream scorer) lands at **54.2%** — above the base-model
number and just under the paper's RLM band. See [Comparison](#comparison-to-the-paper) for the caveat
that the paper does not formally specify OOLONG's metric.

---

## What was run

Each of the 10 manifest items is one OOLONG `trec_coarse` task at **131,072 tokens** (~310 KB) of context:
a list of 3,182 TREC questions (no labels shown) plus a distributional question that **depends on
almost every line** — which label is most/least common, how many items are label X, or is label A more
common than label B. The labels are never in the input, so the method must classify essentially every
question and then aggregate — retrieval shortcuts can't work.

The run used `eval/run_rlm_eval.py`, a faithful automated driver of the `rlm` skill's strategy for this
homogeneous aggregation task. It reproduces the skill's **leaf mechanism exactly**:

- sub-LM = a nested headless Claude Code (`claude -p`), **tools OFF**, model **`haiku`**, the skill's
  leaf system prompt — identical to `rlm_repl.py`'s `llm_query`;
- the only addition is `--output-format json`, so each leaf call's `usage` and `total_cost_usd` can be
  captured and summed (exactly as the eval README's *Recording token/cost usage* section prescribes for
  a multi-call method).

It follows the decomposition the skill's `SKILL.md` prescribes — **LLM does the semantics, Python does
the arithmetic**:

1. **Classify** every one of the 3,182 questions into one of the 6 `trec_coarse` labels, in parallel
   batches of 100 (8 workers). Coverage is checked and any unlabeled/garbled index is re-classified
   until 100% covered.
2. **Aggregate in Python** — count the labels, then answer the specific question (argmax / argmin /
   `counts[X]` / compare A vs B) in the exact format the task requests.

The "root model" orchestration here is **deterministic Python** (the driver), so the method consumes
**no root-LLM tokens** — the reported tokens are the leaf classifier calls only, which is the dominant
and only LLM cost of the RLM loop for this task. Each item was run as an **independent** RLM pass (its
whole context re-classified from scratch), so per-item tokens/cost/time reflect one isolated `/rlm`
invocation on that item.

**Config:** `model=haiku`, `batch=100`, `workers=8`, `timeout=240s`. Machine: Windows 11, 12 cores.

---

## Per-item results

| id | task | answer_type | gold | predicted | score | tokens | cost | time |
|---|---|---|---|---|---:|---:|---:|---:|
| 17000206 | LEAST_FREQ | LABEL | numeric value | `Label: numeric value` | **1.00** | 1,234,062 | $1.744 | 277.2 s |
| 17000208 | MOST_FREQ | LABEL | numeric value | `Label: numeric value` | **1.00** | 1,224,784 | $1.826 | 334.5 s |
| 17000207 | RELATIVE_FREQ | COMPARISON | less common than | `numeric value is less common than entity` | **1.00** | 1,204,749 | $1.217 | 246.1 s |
| 17000210 | RELATIVE_FREQ | COMPARISON | less common than | `description and abstract concept is less common than entity` | **1.00** | 1,195,159 | $1.124 | 243.8 s |
| 17000213 | RELATIVE_FREQ | COMPARISON | more common than | `entity is more common than human being` | **1.00** | 1,201,290 | $1.115 | 265.3 s |
| 17000238 | NUMERIC_ONE_CLASS | NUMERIC | 398 | `Answer: 401` (Δ=3) | **0.42** | 1,216,669 | $1.296 | 315.8 s |
| 17000222 | NUMERIC_ONE_CLASS | NUMERIC | 352 | `Answer: 399` (Δ=47) | 0.00 | 1,212,471 | $1.327 | 302.0 s |
| 17000223 | NUMERIC_ONE_CLASS | NUMERIC | 748 | `Answer: 803` (Δ=55) | 0.00 | 1,205,096 | $1.230 | 237.0 s |
| 17000239 | NUMERIC_ONE_CLASS | NUMERIC | 521 | `Answer: 661` (Δ=140) | 0.00 | 1,218,922 | $1.248 | 442.5 s |
| 17000237 | RELATIVE_FREQ | COMPARISON | same frequency as | `location is less common than abbreviation` | 0.00 | 1,228,838 | $1.256 | 291.8 s |
| | | | | **mean** | **0.5422** | **12,142,040** | **$13.382** | **2,956 s** |

NUMERIC scoring is partial-credit `0.75^|gold−pred|`, which decays to ~0 past Δ≈8; only item 238 (Δ=3)
clears it. COMPARISON/LABEL are exact-match (with phrase matching for comparisons).

---

## Token / cost / time breakdown

- **Tokens:** 12,142,040 total · 1,214,204 mean/item · ~37,700 per leaf call.
  Each `claude -p` leaf call carries a large **fixed overhead** (~30K tokens of cached Claude Code
  system prompt: ~21K cache-read + ~9K cache-creation, measured) on top of ~8K of actual batch
  content. With ~32 calls/item, that fixed overhead — not the question text — dominates the token
  count. Fewer, fatter batches would cut tokens roughly proportionally to the call count.
- **Cost:** $13.38 total · $1.34 mean/item · ~$0.042 per leaf call. Cache-creation of the per-call
  system prompt is the main cost driver, for the same reason.
- **Time:** 49.3 min total, items run sequentially (per-item times sum to the total). Within an item,
  ~32 batches run 8-at-a-time. Item 239 was the slowest (442 s) because one leaf call failed and its
  100 items were re-classified in a recovery round.

> **Independent-runs note (honest accounting).** The 10 items use only **2** distinct contexts (cw6 ×5,
> cw8 ×5), and each item re-classified its context from scratch. A method that **cached the per-context
> labels** would do ~2 classifications instead of 10 — cutting tokens/cost/time by roughly **5×** (to
> ~2.4M tokens / ~$2.7 / ~10 min) at the same score. The numbers above are the conservative
> per-item-independent figures (what one isolated `/rlm` run costs), not the amortized batch figures.

---

## Comparison to the paper

| System (OOLONG, N=131K) | Score |
|---|---:|
| GPT-5 **base model** (paper Table 1) | 44.0 |
| **RLM** (paper Table 1) | 56 – 58 |
| **This run — `rlm` skill, `haiku` leaf** | **54.2** |

The RLM loop with a cheap `haiku` leaf reproduces RLM-class behaviour on OOLONG: it clears the
base-model number and approaches the paper's RLM band, despite a much weaker/cheaper leaf model than
GPT-5. **Caveat (from the eval README):** the paper does not state OOLONG's metric explicitly, so this
comparison is against the **upstream OOLONG-synth scorer** (the same per-item scorer the upstream repo
applies), not a metric the paper formally specifies — treat it as indicative, not a like-for-like
leaderboard entry.

---

## Error analysis — where it wins and loses

**Wins (5/6 LABEL+COMPARISON correct).** The whole-context label *ordering* is recovered reliably, so
"most/least common" and most "A vs B" comparisons land. Gold vs. a representative classified pass:

- **cw8** gold: numeric 965 · entity 748 · human 447 · desc 352 · location 351 · abbrev 319.
  Run (item 208): numeric **968** · entity 801 · human 410 · desc 391 · location 316 · abbrev 296 —
  numeric is near-exact and clearly the max ⇒ MOST_FREQ correct; ordering preserved ⇒ comparisons 210/213 correct.
- **cw6** gold: desc 577 · abbrev 571 · location 571 · human 544 · entity 521 · numeric 398.
  Run (item 239): numeric **400** · entity 661 · human 495 · location 500 · abbrev 532 · desc 594 —
  numeric clearly the min ⇒ LEAST_FREQ correct.

**Losses come from two systematic classifier biases (haiku):**

1. **Exact counts are hard (the 3 zero-scored NUMERIC items).** Classification is directionally right
   but per-class counts are off by tens, and `0.75^|Δ|` punishes that to ~0. Only `numeric value` is
   classified accurately enough (Δ=3 on item 238) to score, because it's the most distinctive class
   ("how many…", "what year…", "what %…"). `entity` / `description` counts drift by 47–140.
2. **cw6 over-predicts `entity` and `description`** (entity ≈620–660 vs gold 521) and **under-predicts
   `location`/`abbreviation`**. This is exactly what breaks item 237: the gold is a true **tie**
   (location = abbreviation = 571), but the noisy counts come out 497 vs 511, so the method reports
   "less common than" instead of "same frequency as". Exact ties are essentially unrecoverable under
   classification noise.

Net: the RLM decomposition is sound (100% coverage, Python aggregation is exact); the ceiling here is
the **leaf model's per-question classification accuracy**. A stronger leaf (`sonnet`) or a
self-consistency/voting pass over each question would most directly lift the NUMERIC and tie cases.

---

## Reproduce

```bash
# Run the method over all 10 items (captures tokens + cost + time):
python .claude/skills/rlm/eval/run_rlm_eval.py --model haiku --batch 100 --workers 8

# Score the predictions (also aggregates the recorded usage):
python .claude/skills/rlm/eval/score.py --predictions .claude/skills/rlm/eval/preds_rlm.jsonl
```

**Artifacts from this run** (under `.claude/skills/rlm/eval/`):
- `run_rlm_eval.py` — the faithful RLM driver used to produce the predictions *(committed)*
- `_runs/rlm_run.json` — full diagnostics: per-item output, gold, timing, per-class counts,
  coverage, and call/token/cost stats *(committed)*
- `preds_rlm.jsonl` — score-ready predictions with `total_tokens` / `total_cost_usd` per item.
  **Gitignored local scratch** (`preds*.jsonl`); regenerate by re-running the driver. The same
  per-item outputs are also recorded in `_runs/rlm_run.json`.
- `_runs/run.log` — raw progress log of the run (local; regenerable, not committed).
