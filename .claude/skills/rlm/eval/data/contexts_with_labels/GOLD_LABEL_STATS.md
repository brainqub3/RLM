# Gold label distributions (ANSWER KEY — read-guarded)

Moved out of `eval/README.md` so a blind eval session cannot read the answers.
This file lives under `contexts_with_labels/`, which is denied to all eval sessions
by the read-guard in `.claude/settings.json` (native `Read` deny + PreToolUse hook).
It is for human/verification use only; score runs out-of-band via `score.py`.

Label distributions recomputed from the gold labels (`_cache/verify_eval.py`):

- **cw8** (3,182): numeric value 965, entity 748, human being 447, description/abstract 352, location 351, abbreviation 319 — *most common = numeric value*.
- **cw6** (3,182): description/abstract 577, abbreviation 571, location 571, human being 544, entity 521, numeric value 398 — *least common = numeric value*; location ties abbreviation at 571.

Comparison (`RELATIVE_FREQ`) gold outcomes span all three: *less* ×2, *more* ×1, *same* ×1.
