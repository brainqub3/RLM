# RLM eval — OOLONG (`trec_coarse`) long-context subset

A small, self-contained evaluation set for scoring this repo's RLM implementation
(the `/rlm` skill + `rlm-subcall` subagent) on a genuinely **long-context**,
information-dense reasoning task.

## Why this benchmark

The reference paper (`paper/2512.24601v3.pdf`, *Recursive Language Models*, arXiv:2512.24601)
reports four long-context benchmarks in its Table 1 — **CodeQA**, **BrowseComp-Plus**,
**OOLONG**, and **OOLONG-Pairs** (§3.1/Figure 1 also use **S-NIAH** as a scaling baseline).
Of these, **OOLONG** is the cleanest fit for this repo's RLM harness, which operates over a
*single large context file + a query*. The paper describes it as (§3.1, verbatim):

> **OOLONG** [Bertsch et al., 2025]. A long reasoning benchmark that requires semantically
> labeling and aggregating these labels to form a final answer. We focus specifically on
> the `trec_coarse` split, a set of 50 tasks over a dataset of questions with semantic
> labels. Each task requires using nearly all dataset questions, and therefore scales
> linearly in processing complexity relative to the input length.

This subset samples **10 of those tasks** (see *Subset statistics* below).

OOLONG is also the paper's headline scaling task (Figure 1) and is the one where the
RLM most clearly beats the base model (Table 1: GPT-5 base 44.0 → RLM 56–58; the answer
"depends explicitly on almost every line in the prompt"). That is exactly the property
we want to test: the model cannot succeed by retrieving a single "needle" — it must
process the whole context.

## What's here

```
eval/
├── README.md                          # this file
├── score.py                           # faithful, dependency-free OOLONG-synth scorer
├── data/
│   ├── oolong_trec_coarse.jsonl          # manifest: one JSON line per eval item
│   ├── contexts/
│   │   └── trec_coarse_cw<cwid>.txt      # FULL model-facing context (no labels)  ← feed this to /rlm
│   └── contexts_with_labels/
│       └── trec_coarse_cw<cwid>.txt      # same context WITH gold labels (verification only)
├── _cache/                               # download/build/verify scripts (provenance; raw cache gitignored)
│   ├── pyarrow_fetch.py                   # pulls trec_coarse@131072 rows from HF parquet
│   ├── build_eval.py                      # selects the 10 items, writes contexts + manifest
│   └── verify_eval.py                     # re-derives every gold answer from the labelled context
└── _upstream_ref/                        # upstream scorer + task-construction source, for provenance
    ├── eval_helpers.py
    ├── task_constructors.py
    └── constants.py
```

Each item is one OOLONG `trec_coarse` task at a context length of **131,072 tokens**
(~310 KB of text), matching the OOLONG column in the paper's Table 1 (`N = 131K`).
The 10 items are drawn over the **2 distinct long contexts** available at this length
(`context_window_id` 6 and 8, each 3,182 labelled TREC questions); contexts are stored
once and shared by the items that use them. **Context is never trimmed** — each
`contexts/*.txt` holds the entire context verbatim (the file you feed to `/rlm` is the
exact, full context).

### Manifest fields (`data/oolong_trec_coarse.jsonl`)

| field | meaning |
|---|---|
| `id` | OOLONG item id |
| `context_window_id` | which of the 2 shared long contexts this item uses (6 or 8) |
| `context_len_tokens` | native context length (131072) |
| `context_chars` | characters in the model-facing context file |
| `num_labels` | number of distinct semantic labels (6 for trec_coarse) |
| `task` / `task_group` | task type (e.g. `TASK_TYPE.MOST_FREQ`) / group (`counting`) |
| `answer_type` | `ANSWER_TYPE.LABEL` / `NUMERIC` / `COMPARISON` |
| `question` | the exact task prompt to answer about the context |
| `answer` | gold answer as a stringified list; the scorer compares against element `[0]` |
| `context_file` | model-facing context (relative path) — **the only thing the model sees** |
| `context_with_labels_file` | gold-labeled context, for independent verification only |

## The task

The context is a list of short natural-language items (TREC questions), each attributed
to a user and a date, **with no labels shown**. The model must infer each item's coarse
semantic class — one of *description and abstract concept, entity, human being, numeric
value, location, abbreviation* — and then aggregate across the whole context to answer a
distributional question, e.g.:

- *which label is the most / least common?* (`LABEL`)
- *is label A more / less common than label B?* (`COMPARISON`)
- *how many items are label X?* (`NUMERIC`)

The labels are never given in the input, so the model must label essentially every line
and then aggregate — defeating retrieval-style shortcuts.

## How to run the eval

For each item in the manifest, run the RLM over its context file with its question, and
record the RLM's final answer. Then score.

1. **Run the RLM per item** (in this Claude Code session). Use each item's
   `context_file` and `question` from the manifest (several items share a context file):

   ```
   /rlm context=.claude/skills/rlm/eval/data/contexts/trec_coarse_cw8.txt query=<the item's question>
   ```

   Collect each run's final answer into a predictions file, one JSON object per line:

   ```json
   {"id": <id>, "output": "<the RLM's final answer text>"}
   ```

   (`output` can be the full final answer; the scorer extracts the answer after the last
   `:` exactly as the official OOLONG harness does, so answers phrased like
   `Label: entity` or `Answer: 37` score correctly.)

2. **Score:**

   ```bash
   python .claude/skills/rlm/eval/score.py --predictions preds.jsonl
   ```

   Prints a per-item table and the mean score (0–1, ×100 for a percentage comparable to
   the paper's Table 1 OOLONG column). This uses the official OOLONG-synth scoring code —
   the same per-item scorer the upstream repo applies for that column. Note the paper does
   not state OOLONG's metric explicitly (only BrowseComp = "percentage correct" and
   OOLONG-Pairs = "F1" are defined), so treat the comparison as based on the upstream
   scorer rather than a metric the paper formally specifies.

### Sanity check

```bash
python .claude/skills/rlm/eval/score.py --self-test
```

Feeds the gold answers back through the parser+scorer; should report mean score ≈ 1.00.
If it doesn't, the manifest and scorer are out of sync.

## Scoring details

`score.py` is a faithful re-implementation of `synth_process_response` /
`synth_attempt_answer_parse` from the official OOLONG repo
(`_upstream_ref/eval_helpers.py`). Summary:

- gold = first element of the stringified `answer` list;
- the model output is parsed by taking text after the last `:` and stripping `*`/`[`/`]`;
- **exact string match → 1.0**;
- `COMPARISON` answers (`more/less common`, `same frequency`) match by phrase;
- `NUMERIC` answers get partial credit `0.75 ** |gold − pred|`;
- everything else → 0.0.

## Provenance & license

- **Benchmark:** OOLONG — Bertsch, Pratapa, Mitamura, Neubig, Gormley,
  *Oolong: Evaluating Long Context Reasoning and Aggregation Capabilities*, 2025.
  arXiv:2511.02817.
- **Data source:** Hugging Face dataset
  [`oolongbench/oolong-synth`](https://huggingface.co/datasets/oolongbench/oolong-synth)
  (config `default`, split `validation`, sub-corpus `dataset = "trec_coarse"`),
  downloaded via the HF datasets-server `/filter` API (full, untruncated rows).
- **Code (scorer / task constructors):** [`abertsch72/oolong`](https://github.com/abertsch72/oolong), MIT License.
- **License note:** the upstream dataset repo does not publish an explicit data license;
  this subset is included here solely for local evaluation of the RLM implementation.
  Cite the OOLONG paper if you use it.

```bibtex
@article{bertsch2025oolong,
  title={Oolong: Evaluating Long Context Reasoning and Aggregation Capabilities},
  author={Bertsch, Amanda and Pratapa, Adithya and Mitamura, Teruko and Neubig, Graham and Gormley, Matthew R.},
  journal={arXiv preprint arXiv:2511.02817},
  year={2025}
}
```

<!-- STATS:START -->
## Subset statistics

- **10 items** over **2 long contexts** (`context_window_id` 6 and 8), each **131,072 tokens**
  (cw6 = 308,367 chars, cw8 = 316,769 chars; 625,136 chars of unique model-facing context).
- **Task mix:** `MOST_FREQ` ×1, `LEAST_FREQ` ×1, `NUMERIC_ONE_CLASS` ×4, `RELATIVE_FREQ` ×4.
- **Answer types:** `LABEL` ×2, `NUMERIC` ×4, `COMPARISON` ×4
  (comparison golds span all three outcomes: *less* ×2, *more* ×1, *same* ×1).
- **Verified:** every gold answer was independently re-derived from the labelled context
  (`_cache/verify_eval.py`), and the scorer self-test scores 1.00
  (`score.py --self-test`). Label distributions recomputed from the gold labels:
  - **cw8** (3,182): numeric value 965, entity 748, human being 447, description/abstract 352, location 351, abbreviation 319 — *most common = numeric value*.
  - **cw6** (3,182): description/abstract 577, abbreviation 571, location 571, human being 544, entity 521, numeric value 398 — *least common = numeric value*; location ties abbreviation at 571.

### Reproducing the data

```bash
python .claude/skills/rlm/eval/_cache/pyarrow_fetch.py   # download trec_coarse@131072 rows (HF parquet)
python .claude/skills/rlm/eval/_cache/build_eval.py      # select 10 items -> contexts/ + manifest
python .claude/skills/rlm/eval/_cache/verify_eval.py     # re-derive every gold answer (integrity check)
```

The download step needs network/HF access plus two libraries
(`pip install "pyarrow>=14" "huggingface_hub>=0.20"`); `build_eval.py`, `verify_eval.py`,
and `score.py` are dependency-free (stdlib only). Note `pyarrow_fetch.py` reads the HF
auto-converted parquet under `refs/convert/parquet/…` — that ref is regenerated by HF and
its shard paths can change over time; the already-built `data/` does not depend on it.
<!-- STATS:END -->
