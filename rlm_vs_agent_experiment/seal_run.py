#!/usr/bin/env python3
"""Seal / unseal completed eval-arm result folders (issue #6 cross-arm leak guard).

The three arms of the OOLONG A/B run *sequentially* through `claude -p` sessions
that have Bash/Read/Grep/Glob and cwd = repo root. A later arm's session could
therefore incidentally read an *earlier* arm's results -- and each arm's
`diagnostics.json` contains the gold answer (`gold`) and the arm's own answers
(`root_result`). That would contaminate the comparison.

To prevent it we MOVE a finished arm's folder out of `runs/<run_id>/<arm>/` into
`_sealed/<run_id>/<arm>/`, which is locked down by the read-guard in
`.claude/settings.json` (native `Read` deny + a PreToolUse hook on `_sealed/`).
A later arm's session cannot read it.

This script is invoked BY NAME with (run_id, arm) -- the guarded `_sealed/`
substring never appears on the caller's command line, so the read-guard does not
block the caller (the secret path lives inside this script, exactly like the way
`score.py` reads the manifest the caller is blocked from). The moves themselves
are plain Python file I/O and are not hook-gated.

After ALL arms finish (no more eval sessions => no leak risk) run `unseal` to move
everything back into `runs/<run_id>/` so the experiment keeps issue #6's layout
(all arms under one `runs/<ts>/`) for scoring and provenance.

Usage:
  python rlm_vs_agent_experiment/seal_run.py seal   <run_id> <arm>   # runs/<id>/<arm> -> _sealed/<id>/<arm>
  python rlm_vs_agent_experiment/seal_run.py unseal <run_id>          # _sealed/<id>/* -> runs/<id>/*
  python rlm_vs_agent_experiment/seal_run.py status <run_id>          # show what is sealed / live
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # rlm_vs_agent_experiment/
RUNS = HERE / "runs"
SEALED = HERE / "_sealed"
ARCHIVE = HERE / "_archive"


def _move(src: Path, dst: Path) -> None:
    if not src.exists():
        sys.exit(f"ERROR: nothing to move -- source does not exist: {src}")
    if dst.exists():
        sys.exit(f"ERROR: refusing to overwrite existing destination: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    print(f"moved {src}  ->  {dst}")


def seal(run_id: str, arm: str) -> None:
    _move(RUNS / run_id / arm, SEALED / run_id / arm)


def unseal(run_id: str) -> None:
    src_root = SEALED / run_id
    if not src_root.exists():
        sys.exit(f"ERROR: nothing sealed for run_id {run_id}: {src_root}")
    arms = sorted(p for p in src_root.iterdir() if p.is_dir())
    if not arms:
        sys.exit(f"ERROR: no sealed arm folders under {src_root}")
    for arm_dir in arms:
        _move(arm_dir, RUNS / run_id / arm_dir.name)
    # tidy the now-empty sealed run folder
    try:
        src_root.rmdir()
        if not any(SEALED.iterdir()):
            SEALED.rmdir()
    except OSError:
        pass


def archive(run_id: str, name: str, label: str) -> None:
    """Move a run artifact into _archive/<run_id>_<label>/ as committed provenance,
    then `git add` it. The _archive/ tree is read-guarded for the eval sessions, and
    this path never appears on the *caller's* command line (it lives here), so the
    caller is not blocked. git runs as a subprocess and is not hook-gated."""
    dst_dir = ARCHIVE / f"{run_id}_{label}"
    _move(RUNS / run_id / name, dst_dir / name)
    readme = dst_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Archived eval artifact ({label})\n\n"
            f"Moved here for provenance from `runs/{run_id}/` (gitignored scratch) "
            f"so the run tree starts clean. Run id `{run_id}`.\n\n"
            f"See the OOLONG RLM-vs-agents A/B (issue #6) and the PR that enforces "
            f"RLM-off for the control arms.\n",
            encoding="utf-8")
    subprocess.run(["git", "add", "-f", str(dst_dir)],
                   cwd=str(HERE.parent), check=False)
    print(f"archived -> {dst_dir} (staged for commit)")


def status(run_id: str) -> None:
    live = sorted(p.name for p in (RUNS / run_id).iterdir() if p.is_dir()) \
        if (RUNS / run_id).exists() else []
    sealed = sorted(p.name for p in (SEALED / run_id).iterdir() if p.is_dir()) \
        if (SEALED / run_id).exists() else []
    print(f"run_id {run_id}")
    print(f"  live  (runs/):    {live or '-'}")
    print(f"  sealed (_sealed/): {sealed or '-'}")


def main(argv: list[str]) -> int:
    if not argv:
        sys.exit(__doc__)
    cmd = argv[0]
    if cmd == "seal" and len(argv) == 3:
        seal(argv[1], argv[2])
    elif cmd == "unseal" and len(argv) == 2:
        unseal(argv[1])
    elif cmd == "archive" and len(argv) == 4:
        archive(argv[1], argv[2], argv[3])
    elif cmd == "status" and len(argv) == 2:
        status(argv[1])
    else:
        sys.exit(f"bad args: {argv}\n{__doc__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
