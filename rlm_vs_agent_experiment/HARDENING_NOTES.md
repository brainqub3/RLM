# Blind-eval hardening — status & validation notes (issue #6)

Implements the fixes from the Codex methodology review. **Nothing has been run for
real** (no model calls); validation so far is static only. This file is the inspection
surface before the next live run.

## What changed (by Codex finding)

| Finding | Fix | Files |
|---|---|---|
| README leaked gold label distributions | Scrubbed gold out of the committed README into a read-guarded file | `eval/README.md`, `eval/data/contexts_with_labels/GOLD_LABEL_STATS.md` |
| Bash/grep bypass; case variants | Per-task **blind sandbox** (cwd) holding only the context (+skill for RLM); hardened repo guards (case-insensitive, README) | `eval_sandbox.py`, `.claude/settings.json` |
| Cross-arm leak (seal not wired in) | **Obviated** by the sandbox — a later arm's session cannot see a prior arm's `runs/` (not in its sandbox). Per-arm seal/unseal retired; `seal_run.py` kept for `archive` provenance | `run_rlm_skill_eval.py` |
| Control spawns its own `claude` (uncounted) | **D2: account via shim** — transparent `claude` shim first on the control sandbox PATH logs child usage; plus transcript **detection** (`spawned_submodel_calls`) | `eval_sandbox.py`, `run_rlm_skill_eval.py` |
| Orchestration-failure not faithful | `read_context_directly` now **fails** the RLM item (`CONTEXT_READ_DIRECT`); detector extended to Bash reads; failure rate printed | `run_rlm_skill_eval.py` |
| n=10 / 2 contexts / partial credit | Reporting discipline (REPORT.md framing) — applied when results exist | (REPORT.md, later) |

## Integrity guarantees are env-INDEPENDENT (robust)

- **Sandbox isolation:** each `claude -p` runs with cwd = a fresh temp dir containing
  only `context.txt` (+ the skill for RLM / the shim for controls). The manifest,
  labels, README, `_cache`, `_archive`, other arms' `runs/`, and `REPORT.md` are simply
  **not present** — not reachable by relative `ls`/`grep -r`/`cat`.
- **Per-arm sandbox guards:** the scaffold guard is written **only** into control
  sandboxes as an *unconditional* grep (no env gate) — control sandboxes deny
  `rlm_repl`/`llm_query`/`rlm_query`; RLM sandboxes allow them. (Verified statically.)
- **`--disallowedTools Skill`** for controls (the proven, real restriction under
  `bypassPermissions`).
- **Transcript detection** (`control_used_rlm`, `spawned_submodel_calls`,
  `read_context_directly`) is parsed from the stream — independent of any env var.

## KNOWN RISK — git-bash env propagation (affects ACCOUNTING only, NOT integrity)

On this Windows machine, a freshly-passed env var does **not** reach `bash -c`
(`python -> git-bash` drops it; `python -> python`/`cmd` keep it). If Claude's Bash
tool launches git-bash the same way, then env-based **cost accounting** may not reach
the sub-process:

- `RLM_LEAF_USAGE_LOG` may not reach `rlm_repl` → RLM **leaf cost could read 0**
  (the RLM arm still *functions*; only the cost number is affected).
- The control shim relies on `PATH`/`REAL_CLAUDE`/`RLM_CHILD_USAGE_LOG` reaching
  git-bash → control child-cost capture may not fire (detection still flags it).

This is **not** confirmed for the real `claude -> bash` path (prior RLM runs did capture
leaf usage, suggesting it works there). **Validate in the live smoke** and check
`leaf_tokens`/`leaf_cost` are non-zero for the RLM arm. If they are 0, switch leaf/child
accounting from env to a sandbox config file the copied `rlm_repl`/shim reads.

## Live-validation checklist (run during inspection — these spawn `claude`)

```
python rlm_vs_agent_experiment/verify_guards.py            # static (passes now)
python rlm_vs_agent_experiment/verify_guards.py --live <id>  # 1 item/arm, asserts guards
```

Confirm: (1) RLM **skill discovery** works in the sandbox cwd (FINAL produced);
(2) RLM **leaf cost > 0** (env reached `rlm_repl`); (3) control shows **no**
Skill/scaffold use; (4) any control sub-model spawn is **flagged** (and, if env
propagates, cost-accounted); (5) transcripts show **no** answer-key path access.
