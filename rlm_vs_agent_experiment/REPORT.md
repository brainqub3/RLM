# RLM vs. a normal Claude Code agent on OOLONG — and what happens when the agent runs a cheap model

**Benchmark:** OOLONG `trec_coarse`, 10 tasks @ 131,072 tokens · **Dates:** 2026-06-17 – 2026-06-18
**Systems compared (3):**
1. the `rlm` skill (Recursive Language Model loop, **`haiku`** leaf),
2. a normal Claude Code agent on **`opus`** (default tools on),
3. the same normal Claude Code agent on **`haiku`** (default tools on).

---

## Abstract

We evaluated three ways of answering long-context aggregation questions that "depend on almost
every line" of a 131K-token context: a **Recursive Language Model (RLM)** with a cheap `haiku`
leaf, and a **normal Claude Code agent** (default tools on) run on both `opus` and `haiku`. Scored
with the official OOLONG-synth scorer:

- The **`haiku` RLM (54.2%)** and the **`opus` agent (54.6%)** are statistically tied, and produce
  the same per-task correctness profile — but the RLM costs **$13.38** vs the agent's **$72.31**
  (~1/5 the cost).
- Dropping the **agent** from `opus` to `haiku` **collapses it from 54.6% to 20.0%** (−34.6 points):
  the plain agent loses *all* label and exact-count tasks, keeping only half the comparison tasks,
  for **$2.70**.
- On the **same `haiku` model**, the **RLM scaffold scores 2.7× the plain agent (54.2% vs 20.0%)**.

The mechanism is structural: the RLM *guarantees* every one of the 3,182 items is classified and
does the counting in code, whereas a plain agent — especially the weaker model — **shortcuts by
sampling/estimating**, which is fatal when the answer depends on every line. **The agent's accuracy
is highly model-dependent; the RLM's is not.** A `haiku`-leaf RLM matches an `opus` agent and nearly
triples a `haiku` agent — i.e. for this task the *scaffold substitutes for model strength.*
(Scope: 10 tasks over 2 contexts, one model pairing, 2026-06-17/18 list prices — a single
reproducible data point, not a broad sweep.)

---

## 1. The task

OOLONG (Bertsch et al., 2025; arXiv:2511.02817) `trec_coarse` presents a long context — **3,182
short TREC questions**, each with a user and date, **no labels shown** — and asks a distributional
question whose answer is a deterministic function of *every* item:

- **LABEL** — which coarse semantic class is most / least common? (e.g. `numeric value`)
- **NUMERIC** — exactly how many items are class *X*?
- **COMPARISON** — is class *A* more / less common than class *B*, or the same?

The six classes are the standard TREC coarse labels: *numeric value, entity, human being, location,
abbreviation, description and abstract concept*. The labels are never in the input, so a system must
infer the class of essentially every line and aggregate — retrieval/keyword shortcuts can't work.
This is the paper's headline scaling task (its Table 1 reports **GPT-5 base = 44.0 → RLM = 56–58**
on OOLONG `N=131K`). This subset is **10 tasks over 2 distinct 131K-token contexts** (2 LABEL, 4
NUMERIC, 4 COMPARISON); every gold answer was independently re-derived, and the scorer self-test
scores 1.00.

**Scoring** (`score.py`, a faithful re-implementation of the upstream OOLONG-synth scorer): parse the
text after the last `:`; **exact match → 1.0**; COMPARISON by phrase; **NUMERIC partial credit
`0.75^|gold−pred|`** (≈0 past a difference of ~8); else 0.0. Mean ×100 ≈ the paper's Table 1 OOLONG
column (same upstream scorer; the paper doesn't formally state the metric, so treat cross-comparison
as indicative).

---

## 2. Setup — RLM vs. a normal agent (two models)

All three systems map `(context_file, question) → answer` and are scored identically. Each task is an
**independent** invocation (no caching across tasks), so per-task figures reflect one isolated run.
No system is given the gold labels.

### System A — the RLM skill (`haiku` leaf)

A faithful instantiation of *Recursive Language Models* (Zhang, Kraska, Khattab; arXiv:2512.24601,
Algorithm 1). The context **never enters the orchestrator's context window**; it lives in a Python
REPL. The orchestrator writes code that **(1) classifies all 3,182 questions** into the six labels —
in parallel batches of 100, each batch a cheap sub-LM call (a nested headless `claude -p`, **tools
off**, model **`haiku`**), ~32 leaf calls per context, with a coverage check that re-runs any
unlabeled item — then **(2) aggregates in Python** (count, then argmax/argmin/`counts[X]`/compare).
LLM does the semantics, Python does the arithmetic; the orchestration is deterministic Python, so
the only LLM tokens are the `haiku` leaves. Driver: `rlm_haiku/run_rlm_eval.py`
(`--model haiku --batch 100 --workers 8`).

### System B — a normal Claude Code agent (run on `opus`, then `haiku`)

Plain Claude Code, headless, **default tools on** (`claude -p --model <opus|haiku>
--permission-mode bypassPermissions`, web tools disabled). It is given the **absolute path** to the
context file and the task, told the file holds 3,182 items and is larger than a single read returns
(so it must account for all of them — avoiding the silent file-read truncation trap; it is *not*
told how to classify), and left to solve however it likes (read in chunks, write/run a script,
reason directly). The RLM skill is never invoked and — run from a folder outside the RLM repo — is
not even on the skill path. Driver: `agent_*/run_plain_eval.py` (`--model <opus|haiku> --modes
agent`). The two model runs differ only in `--model`.

> **Operational notes.** (a) The `opus` agent ran in two phases for unrelated reasons (initial tasks
> 206/208/222/223, then an agent-only resume for the rest); consolidated in
> `agent_opus/diagnostics.json`. (b) The `haiku` agent run hit a **Windows-only logging crash** after
> task 6 (a `✓` in the model's output vs. the cp1252 console encoding); the driver was hardened
> (UTF-8 logging) and tasks 7–10 were resumed. Neither affects any per-task figure — each task is an
> independent session, and the saved per-task tokens/cost/time are the model's own.

---

## 3. Results

### 3.1 Headline (3 systems)

| System | Score | Tokens | Cost | End-to-end time |
|---|---:|---:|---:|---:|
| **RLM — `haiku` leaf** | **54.2%** | 12,142,040 | **$13.38** | ~49 min |
| **Agent — `opus`, tools on** | **54.6%** | 6,445,722 | **$72.31** | ~104 min |
| **Agent — `haiku`, tools on** | **20.0%** | 8,277,515 | **$2.70** | ~47 min |
| *Paper Table 1 — GPT-5 base / RLM (reference)* | *44.0 / 56–58* | — | — | — |

### 3.2 Per-task (predicted answer / score for each system)

Grouped by answer type. NUMERIC shows `pred (Δ)` where Δ = |gold − pred|.

| id | task | gold | RLM `haiku` | | agent `opus` | | agent `haiku` | |
|---|---|---|---|--:|---|--:|---|--:|
| 17000206 | LEAST_FREQ | numeric value | numeric value | **1.00** | numeric value | **1.00** | description & abstract | 0.00 |
| 17000208 | MOST_FREQ | numeric value | numeric value | **1.00** | numeric value | **1.00** | description & abstract | 0.00 |
| 17000207 | RELATIVE | less common than | less common than | **1.00** | less common than | **1.00** | less common than | **1.00** |
| 17000210 | RELATIVE | less common than | less common than | **1.00** | less common than | **1.00** | less common than | **1.00** |
| 17000213 | RELATIVE | more common than | more common than | **1.00** | more common than | **1.00** | less common than | 0.00 |
| 17000237 | RELATIVE | same frequency as | less common than | 0.00 | more common than | 0.00 | more common than | 0.00 |
| 17000222 | NUMERIC | 352 | 399 (Δ47) | 0.00 | 414 (Δ62) | 0.00 | 298 (Δ54) | 0.00 |
| 17000223 | NUMERIC | 748 | 803 (Δ55) | 0.00 | 737 (Δ11) | 0.04 | 273 (Δ475) | 0.00 |
| 17000238 | NUMERIC | 398 | 401 (Δ3) | **0.42** | 401 (Δ3) | **0.42** | 308 (Δ90) | 0.00 |
| 17000239 | NUMERIC | 521 | 661 (Δ140) | 0.00 | 547 (Δ26) | 0.00 | 109 (Δ412) | 0.00 |
| | | **mean** | | **0.5422** | | **0.5465** | | **0.2000** |

By answer type:

| answer_type | RLM `haiku` | agent `opus` | agent `haiku` |
|---|---:|---:|---:|
| LABEL (most/least common) | 2/2 = **100%** | 2/2 = **100%** | 0/2 = **0%** |
| COMPARISON (A vs B) | 3/4 = **75%** | 3/4 = **75%** | 2/4 = **50%** |
| NUMERIC (exact count) | 0.42/4 = **10.5%** | 0.46/4 = **11.6%** | 0/4 = **0%** |

### 3.3 Efficiency

| | RLM `haiku` | agent `opus` | agent `haiku` |
|---|---:|---:|---:|
| Total cost | $13.38 | $72.31 | $2.70 |
| Cost / task (mean) | $1.34 | $7.23 | $0.27 |
| Total tokens | 12,142,040 | 6,445,722 | 8,277,515 |
| Total wall time | ~49 min | ~104 min | ~47 min |
| Effective blended rate | ~$1.10 / MTok | ~$11.22 / MTok | ~$0.33 / MTok |

---

## 4. The two comparisons this study isolates

### 4.1 Does the *agent* approach degrade on a cheaper model? — Yes, sharply.

**`opus` agent 54.6% → `haiku` agent 20.0%** (−34.6 points; it keeps ~37% of the score) while cost
falls **~27×** ($72.31 → $2.70). The collapse is not uniform — it's concentrated exactly where the
task demands processing *every* item:

- **LABEL: 100% → 0%.** The `haiku` agent answered "description and abstract concept" for both
  most- and least-common questions (a default-ish guess), where gold is "numeric value".
- **NUMERIC: ~12% → 0%.** Its counts are wildly low (273 vs gold 748; 109 vs gold 521) — the model's
  own output reveals it working from a **small sample / running percentages** (e.g. on task 208 it
  reported "location: 184 (5.79%) … entity: 152 (4.78%)"), not an exhaustive pass over 3,182 items.
- **COMPARISON: 75% → 50%.** Only direction-only comparisons partly survive (it got the two "less
  common" cases, missed the "more common" one and the tie).

So a plain agent's accuracy on whole-context aggregation is **highly model-dependent**: swap the
frontier model for a cheap one and it falls apart, because the cheap model takes the shortcut the
task is specifically designed to punish.

### 4.2 Same `haiku` model: scaffold vs. plain agent — the scaffold wins ~3×.

**RLM `haiku` 54.2% vs. agent `haiku` 20.0%** — *identical model*, but the RLM scores **2.7×**
higher. Tellingly, the RLM is the **more expensive** `haiku` configuration ($13.38 vs $2.70): it
spends ~322 leaf calls precisely *to not shortcut* — every item is classified and the counts are
computed in Python. The plain agent is cheap because it estimates, and the estimate is exactly why
it fails. So the RLM scaffold's value is to make a weak model behave exhaustively.

### 4.3 Synthesis

| | accuracy | cost | what determines accuracy |
|---|---|---|---|
| Plain agent | `opus` 54.6 → `haiku` 20.0 | $72.31 → $2.70 | **the model** (collapses on the cheap one) |
| RLM | `haiku` leaf = 54.2 (≈ `opus` agent) | $13.38 | **the scaffold** (cheap model suffices) |

The RLM converts the problem from "does the model reason correctly over 131K tokens in one pass"
(which a weak model can't) into "classify a bounded chunk, then count in code" (which a weak model
can). That is why a `haiku`-leaf RLM matches an `opus` agent at 1/5 the cost and triples a `haiku`
agent. **For whole-context aggregation, the scaffold buys accuracy that the plain-agent route can
only buy with a much more expensive model.**

### 4.4 The shared ceiling (RLM `haiku` ≈ agent `opus`)

The two strong systems tie at ~54% and fail the *same* two ways: the exact-count NUMERIC tasks (both
drift by tens; only `numeric value`, the most distinctive class, scores — Δ3 on task 238 for both)
and the one true frequency **tie** (task 237: `location` = `abbreviation` = 571, unreproducible under
classification noise). Their common limiter is **per-item accuracy of the 6-way TREC
classification**, which neither saturates. The lever that would move it is a stronger *classifier*
(e.g. a `sonnet` leaf) or a per-item voting pass — not a bigger orchestrator.

---

## 5. Token-pricing assumptions

Per-task **cost was not estimated** — each `claude -p` call reports its own `total_cost_usd`
(computed by the CLI from live per-token prices), and we summed those verbatim. The list prices below
are recorded so the totals are auditable. Verified against the Claude API pricing reference (per
**million tokens**, USD):

| Model | Input | Output | Cache write — 5-min (1.25×) | Cache write — 1-hour (2×) | Cache read (0.1×) |
|---|---:|---:|---:|---:|---:|
| **Claude Opus 4.8** (`claude-opus-4-8`) | $5.00 | $25.00 | $6.25 | $10.00 | $0.50 |
| **Claude Haiku 4.5** (`claude-haiku-4-5`) | $1.00 | $5.00 | $1.25 | $2.00 | $0.10 |

- **Token total per call** = `input + output + cache_creation + cache_read` (the scorer's
  aggregation of the `usage` object).
- **Claude Code caches its CLI system prompt at the 1-hour TTL**, so cache *writes* are billed at
  **2× base** (confirmed: `usage.cache_creation` shows `ephemeral_1h_input_tokens`).
- First-party list prices, no negotiated/volume discount. Figures reflect what the CLI billed at list
  rates on 2026-06-17/18.

Sanity check (not used to compute anything): blended effective rate = total cost / total tokens →
RLM **~$1.10/MTok**, `opus` agent **~$11.22/MTok**, `haiku` agent **~$0.33/MTok** — each consistent
with its model's input/output/cache mix.

---

## 6. Conclusion

On a long-context aggregation benchmark that defeats retrieval, **a Recursive Language Model with a
cheap `haiku` leaf (54.2%) matches a frontier `opus` Claude Code agent (54.6%) at ~1/5 the cost — and
nearly triples the *same* model run as a plain agent (`haiku` agent 20.0%).** The plain-agent route
is strongly model-dependent: dropping `opus`→`haiku` collapses it from 54.6% to 20.0% because the
cheap model samples/estimates instead of processing all 3,182 items. The RLM route is largely
model-independent here because the scaffold *forces* exhaustive per-item classification and exact
Python counting. **Headline: for whole-context aggregation, the RLM scaffold delivers frontier-agent
accuracy at small-model economics, and is what lets a weak model succeed where a plain agent on the
same model fails.** The remaining ceiling for the strong configurations is per-item classification
accuracy — a classifier/voting problem, not an orchestrator problem. (Single data point: 10 tasks, 2
contexts, this model pairing, 2026-06-17/18 prices.)

---

## 7. Auditability — reproduce the scores from this folder

Self-contained: the scorer, the manifest (with gold answers), all three predictions files, and full
diagnostics/logs are included. Re-derive all three headline scores:

```bash
# RLM (haiku):         expect 0.5422, 12,142,040 tok, $13.3820
python score.py --manifest oolong_trec_coarse.jsonl --predictions rlm_haiku/preds_rlm.jsonl

# Agent (opus):        expect 0.5465,  6,445,722 tok, $72.3138
python score.py --manifest oolong_trec_coarse.jsonl --predictions agent_opus/preds_agent_opus.jsonl

# Agent (haiku):       expect 0.2000,  8,277,515 tok, $2.6994
python score.py --manifest oolong_trec_coarse.jsonl --predictions agent_haiku/preds_agent_haiku.jsonl
```

All three were re-scored from these copied files and reproduce the numbers above exactly.

### Contents

```
rlm_vs_agent_experiment/
├── REPORT.md                       # this report
├── score.py                        # official OOLONG-synth scorer (stdlib-only)
├── oolong_trec_coarse.jsonl        # manifest: 10 tasks + gold answers
├── rlm_haiku/
│   ├── preds_rlm.jsonl             # scored predictions (id, output, total_tokens, total_cost_usd)
│   ├── diagnostics.json            # per-task timing, per-class counts, coverage, call/token/cost stats
│   ├── run.log                     # raw run log
│   └── run_rlm_eval.py             # the RLM driver
├── agent_opus/
│   ├── preds_agent_opus.jsonl      # scored predictions (10 agent tasks)
│   ├── diagnostics.json            # consolidated agent-only per-task diagnostics (all 10 tasks)
│   ├── agent_rest.log              # raw log, agent tasks 5–10
│   └── run_plain_eval.py           # the plain-agent driver (also has a tools-off "base" mode, deliberately not used)
└── agent_haiku/
    ├── preds_agent_haiku.jsonl     # scored predictions (10 agent tasks)
    ├── diagnostics.json            # consolidated agent-only per-task diagnostics (all 10 tasks)
    ├── run1_tasks1-6.log           # raw log, tasks 1–6 (ends with the Windows logging crash)
    ├── run2_tasks7-10.log          # raw log, tasks 7–10 (resumed with the hardened driver)
    └── run_plain_eval.py           # same plain-agent driver
```

## Provenance & license

- **Benchmark:** OOLONG — Bertsch, Pratapa, Mitamura, Neubig, Gormley, *Oolong: Evaluating Long
  Context Reasoning and Aggregation Capabilities*, 2025 (arXiv:2511.02817). Scorer/task code from
  [`abertsch72/oolong`](https://github.com/abertsch72/oolong) (MIT). Cite the OOLONG paper if you use it.
- **RLM:** Zhang, Kraska, Khattab, *Recursive Language Models*, 2025 (arXiv:2512.24601).
- Prices are first-party Claude API list rates as of 2026-06-17/18.
