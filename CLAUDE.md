# Project instructions

## RLM mode for long-context tasks

This repository includes a faithful "Recursive Language Model" (RLM) setup for
Claude Code (after *Recursive Language Models*, arXiv:2512.24601, Algorithm 1):
- Skill: `rlm` in `.claude/skills/rlm/`
- Persistent Python REPL: `.claude/skills/rlm/scripts/rlm_repl.py` — holds the
  large context as a variable and exposes `llm_query` / `llm_query_map` /
  `rlm_query` and `FINAL` / `FINAL_VAR`.
- Sub-LM (`llm_query`): a nested headless Claude Code (`claude -p`, tools off,
  default model `haiku`), called *programmatically from REPL code* — not a Task
  subagent. The recursive `rlm_query` runs `claude -p` with bash + this skill on.

When the user needs you to work over a context that is too large to paste into chat:
1) Ask for (or locate) a context file path.
2) Run the `/rlm` Skill and follow its procedure.

Keep the main conversation light: the root model never reads the full context —
it writes REPL code that sub-queries the context in chunks, then synthesises.
Use `python` (not `python3`) to invoke the REPL on this machine.

## OOLONG eval — where run artifacts go

The RLM-vs-agent OOLONG eval (issue #6) is driven by
`rlm_vs_agent_experiment/run_rlm_skill_eval.py`. **Every run writes only under a
timestamped folder — `rlm_vs_agent_experiment/runs/<YYYYMMDD_HHMMSS>/<arm>/` — never
loose in the experiment folder.** Pass the same `--run-id` to every arm so one
experiment groups together:

```bash
TS=$(date +%Y%m%d_%H%M%S)
python rlm_vs_agent_experiment/run_rlm_skill_eval.py --run-id $TS --mode agent --root opus
python rlm_vs_agent_experiment/run_rlm_skill_eval.py --run-id $TS --mode agent --root haiku
python rlm_vs_agent_experiment/run_rlm_skill_eval.py --run-id $TS --mode rlm   --root opus
python rlm_vs_agent_experiment/score.py --predictions rlm_vs_agent_experiment/runs/$TS/rlm_skill_opus/preds_rlm_skill.jsonl
```

`runs/` is gitignored — run folders are local scratch; the committed deliverable is
`rlm_vs_agent_experiment/REPORT.md`. This keeps the repo clean so we never accumulate
stray eval files that must later be archived. (To keep a specific run as committed
provenance, `git add -f` that one run folder.)

This is a **driver convention only — the `/rlm` skill is unchanged**. The skill's own
on-disk state is the transient `.claude/rlm_state/` REPL pickle (gitignored, and wiped
per task by the driver); it never writes into the experiment folder.
