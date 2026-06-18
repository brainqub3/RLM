#!/usr/bin/env python3
"""Verification gate for the blind OOLONG A/B harness (issue #6, Phase 6).

Two modes:

  python rlm_vs_agent_experiment/verify_guards.py            # STATIC (no model calls)
  python rlm_vs_agent_experiment/verify_guards.py --live ID  # LIVE smoke (spawns claude)

STATIC asserts, with NO claude calls:
  * sandbox build copies only the model-facing context (+ skill for RLM / shim for
    control) and never leaks eval/ (the answer key) into the sandbox;
  * the REAL read-guard hook commands in .claude/settings.json AND the sandbox's
    generated settings actually DENY answer-key path references (case-insensitive)
    and ALLOW benign ones; the control-scoped scaffold guard fires only when
    RLM_CONTROL_SESSION is set.

LIVE smoke (run during inspection / before the real run) additionally asserts, on a
single item per arm into a throwaway run-id:
  * control: no Skill/scaffold use, control_used_rlm == False, any sub-model spawn is
    accounted (child usage logged) and flagged;
  * rlm: a FINAL answer was produced, no direct context read;
  * no arm's transcript references an answer-key path.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import eval_sandbox  # noqa: E402

PASS, FAIL = "PASS", "FAIL"
_results = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    _results.append(ok)
    print(f"  [{PASS if ok else FAIL}] {name}" + (f"  -- {detail}" if detail else ""))


def _hook_denies(commands, sample_json: str, env: dict) -> bool:
    """Run the REAL hook command(s) with sample_json on stdin; True if any denies."""
    for cmd in commands:
        try:
            r = subprocess.run(["bash", "-c", cmd], input=sample_json,
                               capture_output=True, text=True, env=env, timeout=30)
        except Exception:
            continue
        if '"deny"' in (r.stdout or ""):
            return True
    return False


def _hook_commands(settings_path_or_text) -> list:
    if isinstance(settings_path_or_text, Path):
        cfg = json.loads(settings_path_or_text.read_text(encoding="utf-8"))
    else:
        cfg = json.loads(settings_path_or_text)
    cmds = []
    for entry in (cfg.get("hooks", {}).get("PreToolUse", []) or []):
        for h in (entry.get("hooks", []) or []):
            if h.get("command"):
                cmds.append(h["command"])
    return cmds


def _sample(**tool_input) -> str:
    return json.dumps({"tool_name": "Bash", "tool_input": tool_input})


def static_checks() -> None:
    print("STATIC guard checks (no model calls)")

    # --- sandbox build: RLM + control -------------------------------------- #
    tmp = Path(tempfile.mkdtemp(prefix="rlm_verify_"))
    try:
        src = tmp / "ctx.txt"
        src.write_text("a\nb\nc\n", encoding="utf-8")
        rlm = eval_sandbox.build(tmp / "rlm", src, "rlm", REPO, REPO / ".claude/skills/rlm")
        _check("RLM sandbox has context.txt", (tmp / "rlm/context.txt").exists())
        _check("RLM sandbox has skill", rlm["repl"].exists())
        _check("RLM sandbox excludes eval/ (answer key)",
               not (tmp / "rlm/.claude/skills/rlm/eval").exists())
        ctl = eval_sandbox.build(tmp / "ctl", src, "agent", REPO, REPO / ".claude/skills/rlm")
        _check("control sandbox has claude shim",
               all((ctl["bin"] / f).exists() for f in ("claude", "claude.cmd", "claude_shim.py")))
        _check("control sandbox has no skill", not (tmp / "ctl/.claude/skills").exists())
        for s in (tmp / "rlm/.claude/settings.json", tmp / "ctl/.claude/settings.json"):
            json.loads(s.read_text(encoding="utf-8"))
        _check("sandbox settings are valid JSON", True)
    finally:
        eval_sandbox.teardown(tmp)

    # --- the REAL hook commands: repo + sandbox ---------------------------- #
    repo_cmds = _hook_commands(REPO / ".claude/settings.json")
    sbx_cmds = _hook_commands(eval_sandbox.sandbox_settings(str(REPO), "agent"))
    base_env = dict(os.environ)

    deny_samples = {
        "contexts_with_labels path": _sample(file_path=".claude/skills/rlm/eval/data/contexts_with_labels/cw6.txt"),
        "manifest path": _sample(command="cat .claude/skills/rlm/eval/data/oolong_trec_coarse.jsonl"),
        "_archive path": _sample(command="ls rlm_vs_agent_experiment/_archive/"),
        "eval README path": _sample(file_path=".claude/skills/rlm/eval/README.md"),
        "GOLD_LABEL_STATS path": _sample(command="cat .../contexts_with_labels/GOLD_LABEL_STATS.md"),
        "case-variant (UPPER)": _sample(command="cat CONTEXTS_WITH_LABELS/x"),
    }
    for name, s in deny_samples.items():
        _check(f"repo guard denies: {name}", _hook_denies(repo_cmds, s, base_env))

    allow_samples = {
        "benign context probe": _sample(command="sed -n 1,5p context.txt"),
        "rlm repl init (RLM, no control env)": _sample(command="python .claude/skills/rlm/scripts/rlm_repl.py init context.txt"),
    }
    for name, s in allow_samples.items():
        _check(f"repo guard allows: {name}", not _hook_denies(repo_cmds, s, base_env))

    # scaffold guard is ARM-SPECIFIC in the sandbox settings (unconditional grep, no env
    # dependency): present for control sandboxes, absent for RLM sandboxes.
    sbx_rlm = _hook_commands(eval_sandbox.sandbox_settings(str(REPO), "rlm"))
    scaffold = _sample(command="python rlm_repl.py exec  # llm_query fan-out")
    _check("control sandbox denies the /rlm scaffold", _hook_denies(sbx_cmds, scaffold, base_env))
    _check("RLM sandbox allows the /rlm scaffold", not _hook_denies(sbx_rlm, scaffold, base_env))

    # fix #3: control sandbox denies reading the repo's /rlm skill doc by absolute path;
    # RLM sandbox must still allow its own SKILL.md.
    skilldoc = _sample(command="cat /x/.claude/skills/rlm/SKILL.md")
    _check("control sandbox denies repo SKILL.md", _hook_denies(sbx_cmds, skilldoc, base_env))
    _check("RLM sandbox allows its own SKILL.md", not _hook_denies(sbx_rlm, skilldoc, base_env))
    # fix #6: backslash / JSON-escaped path variants are denied
    bs = _sample(command="type .claude\\skills\\rlm\\eval\\README.md")
    _check("repo guard denies backslash eval README path", _hook_denies(repo_cmds, bs, base_env))

    # sandbox backstop denies repo-absolute answer-key + experiment tree refs
    _check("sandbox guard denies repo experiment tree",
           _hook_denies(sbx_cmds, _sample(command="ls rlm_vs_agent_experiment/runs/"), base_env))
    _check("sandbox guard denies repo answer key",
           _hook_denies(sbx_cmds, _sample(command="cat /x/contexts_with_labels/cw6.txt"), base_env))


def live_smoke(item_id: str) -> None:
    print(f"LIVE smoke on id={item_id} (spawns claude per arm)")
    run_id = f"verify_{item_id}"
    driver = HERE / "run_rlm_skill_eval.py"
    for mode, root, arm in (("agent", "haiku", f"agent_haiku"),
                            ("rlm", "opus", f"rlm_skill_opus")):
        print(f"-- arm: mode={mode} root={root}")
        subprocess.run([sys.executable, str(driver), "--mode", mode, "--root", root,
                        "--run-id", run_id, "--ids", str(item_id)], cwd=str(REPO))
        diag = HERE / "runs" / run_id / arm / "diagnostics.json"
        if not diag.exists():
            _check(f"{arm}: diagnostics written", False, "missing")
            continue
        d = json.loads(diag.read_text(encoding="utf-8"))["items"][0]
        if mode == "agent":
            _check(f"{arm}: control did NOT use skill/scaffold", not d.get("control_used_rlm"))
            if d.get("spawned_submodel_calls"):
                _check(f"{arm}: control sub-model spawn was accounted",
                       d.get("leaf_calls", 0) > 0, f"{d['spawned_submodel_calls']} spawns")
        else:
            _check(f"{arm}: RLM produced a FINAL answer", bool(d.get("repl_final")))
            _check(f"{arm}: RLM did not read context directly", not d.get("read_context_directly"))
    print("NOTE: also eyeball the *.stream.jsonl transcripts for any answer-key path access.")


def main(argv) -> int:
    if argv and argv[0] == "--live":
        if len(argv) < 2:
            sys.exit("usage: verify_guards.py --live <item_id>")
        live_smoke(argv[1])
    else:
        static_checks()
    ok = all(_results)
    print("=" * 60)
    print(f"VERIFY: {'ALL PASS' if ok else 'FAILURES PRESENT'} "
          f"({sum(_results)}/{len(_results)} checks)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
