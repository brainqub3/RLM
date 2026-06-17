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
