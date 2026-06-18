# ARCHIVED — RLM run with a pre-written OOLONG harness (superseded)

**Status:** withdrawn from the headline comparison. Kept for reference only.

This is the original RLM result for the experiment: **54.2%**, 12,142,040 tokens, $13.38, ~49 min
(`preds_rlm.jsonl` / `diagnostics.json` / `run.log`, produced by `run_rlm_eval.py`).

## Why it was archived

It does **not** measure what we want to test. `run_rlm_eval.py` is a **deterministic, OOLONG-specific
harness** — the classify-then-count strategy was written and verified by hand for this task, not
discovered at runtime by the model. Specifically it hardcodes:

- OOLONG's line format (`|| Instance:`, the `"contain N general-knowledge questions"` header),
- the six TREC `trec_coarse` labels,
- the four OOLONG task types (`MOST_FREQ` / `LEAST_FREQ` / `NUMERIC_ONE_CLASS` / `RELATIVE_FREQ`) and
  the answer formatting for each.

So its "orchestrator is deterministic Python, zero root-LLM tokens" property is an artifact of a
frozen, task-specialized strategy — it measures the RLM paradigm's *ceiling when the orchestration is
already correct*, not the out-of-the-box behaviour of the general `/rlm` skill (where an LLM root
must probe the data, choose a decomposition, and write the aggregation code itself, at non-zero root
cost and with real variance).

## What replaces it

A re-run using the **general `/rlm` skill** (LLM-as-root, self-authored strategy, Haiku leaf), with
root **and** leaf token/cost accounted for. Tracked in the GitHub issue referenced from the parent
`REPORT.md`. The two **agent** runs (`agent_opus/`, `agent_haiku/`) are unaffected and remain valid.
