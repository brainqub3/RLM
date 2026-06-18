#!/usr/bin/env python3
"""Per-task BLIND sandbox + child-model accounting shim for the OOLONG A/B (issue #6).

Each eval session (`claude -p`) runs with cwd = a fresh temp sandbox holding ONLY
what the model legitimately needs, so the answer key (manifest, labels, README
stats, _cache, _archive), other arms' results, and the committed REPORT simply are
not reachable by relative exploration:

  <sandbox>/
    context.txt                              # the single model-facing context (verbatim)
    .claude/settings.json                    # hardened read-guards (absolute-path backstop)
    .claude/skills/rlm/SKILL.md              # RLM ARM ONLY: skill instructions (no eval/)
    .claude/skills/rlm/scripts/*             # RLM ARM ONLY: rlm_repl.py + helpers
    bin/{claude,claude.cmd,claude_shim.py}   # CONTROL ARM ONLY: claude accounting shim

The parent driver still writes preds/diagnostics into the repo's runs/ (outside the
sandbox). This obviates the per-arm seal/unseal cross-arm guard: a later arm's
session cannot see a prior arm's results -- they are not in its sandbox.

D2 (control sub-model accounting): for control arms we put a transparent `claude`
shim first on PATH. Any `claude` the control spawns is forwarded to the real claude
(path in $REAL_CLAUDE); the shim logs that call's tokens/cost to $RLM_CHILD_USAGE_LOG
and returns the real output unchanged. It is SAFE-DEGRADING: if usage capture fails,
it still returns the real output, so a control run is never broken by the shim.

RESIDUAL (documented honestly): this is a minimized-cwd jail, NOT an OS sandbox -- a
determined session could still try absolute paths into the repo. That is backstopped
by the read-guards written here and in the repo .claude/settings.json. On Windows
there is no cheap hard jail; for non-adversarial eval models this closes the realistic
leak paths. The git-bash resolution of the no-extension `claude` shim and end-to-end
behaviour are NOT yet validated live -- see Phase 6 verification.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


# --------------------------------------------------------------------------- #
# The claude accounting shim (control arms only)                              #
# --------------------------------------------------------------------------- #
SHIM_PY = r'''#!/usr/bin/env python3
"""Transparent `claude` accounting shim (eval CONTROL sandboxes, issue #6).

First on a control session's PATH, so any `claude` the control spawns is intercepted:
forward to the REAL claude ($REAL_CLAUDE), capture the call's token/cost usage, append
one record to $RLM_CHILD_USAGE_LOG, and return the real output transparently. Safe-
degrading: if anything in the usage path fails, still return the real output + code.
"""
import json, os, subprocess, sys, time

_KEYS = ("input_tokens", "output_tokens",
         "cache_creation_input_tokens", "cache_read_input_tokens")


def _log(rec):
    p = os.environ.get("RLM_CHILD_USAGE_LOG")
    if not p:
        return
    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def main(argv):
    real = os.environ.get("REAL_CLAUDE")
    if not real:
        sys.stderr.write("[claude_shim] REAL_CLAUDE not set; cannot forward\n")
        return 127
    args = list(argv)
    has_fmt = any(a == "--output-format" or a.startswith("--output-format=") for a in args)
    capture = not has_fmt   # add json only if the caller did not ask for a format
    run_args = [real] + args + (["--output-format", "json"] if capture else [])
    try:
        # stdin=None inherits the caller's stdin (the piped prompt); capture stdout.
        res = subprocess.run(run_args, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
    except Exception as e:
        sys.stderr.write(f"[claude_shim] exec failed ({e}); bare passthrough\n")
        try:
            return subprocess.run([real] + args).returncode
        except Exception:
            return 1
    out = res.stdout or ""
    try:
        if capture:
            d = json.loads(out)
            usage = d.get("usage") or {}
            tot = sum(int(usage.get(k, 0) or 0) for k in _KEYS)
            _log({"ts": time.time(), "ok": not bool(d.get("is_error")),
                  "total_tokens": tot, "cost_usd": float(d.get("total_cost_usd") or 0.0),
                  "via": "shim"})
            sys.stdout.write(d.get("result") or "")
            sys.stderr.write(res.stderr or "")
            return res.returncode
        # caller specified its own format: pass output through untouched, best-effort usage
        sys.stdout.write(out)
        sys.stderr.write(res.stderr or "")
        try:
            d = json.loads(out)
            usage = d.get("usage") or {}
            tot = sum(int(usage.get(k, 0) or 0) for k in _KEYS)
            _log({"ts": time.time(), "ok": not bool(d.get("is_error")),
                  "total_tokens": tot, "cost_usd": float(d.get("total_cost_usd") or 0.0),
                  "via": "shim-passthrough"})
        except Exception:
            pass
        return res.returncode
    except Exception:
        # usage capture failed -> stay transparent: emit raw stdout, log nothing
        sys.stdout.write(out)
        sys.stderr.write(res.stderr or "")
        return res.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
'''

SHIM_SH = ('#!/bin/sh\n'
           '# git-bash wrapper -> the python accounting shim\n'
           'exec python "$(dirname "$0")/claude_shim.py" "$@"\n')

SHIM_CMD = ('@echo off\r\n'
            'python "%~dp0claude_shim.py" %*\r\n')


# --------------------------------------------------------------------------- #
# Hardened read-guard backstop written into the sandbox                       #
# --------------------------------------------------------------------------- #
# Case-insensitive substrings; separator-free tokens match both / and \ paths.
_ANSWERKEY_PAT = ("_archive|contexts_with_labels|_cache/|verify_eval|"
                  "oolong_trec_coarse|gold_label_stats|rlm_vs_agent_experiment|eval/readme")
_SCAFFOLD_PAT = "rlm_repl|llm_query|rlm_query"
_ANSWERKEY_REASON = ("Blocked (sandbox backstop): off-limits OOLONG answer key or the "
                     "repo experiment tree for the blind eval (issue #6). Score out-of-band "
                     "with score.py.")
_SCAFFOLD_REASON = ("Blocked: a RLM-OFF control may not use the /rlm scaffold "
                    "(rlm_repl / llm_query / rlm_query). Issue #6: control runs the skill OFF.")


def _hook_cmd(pattern: str, reason: str, env_gate: Optional[str] = None) -> str:
    payload = json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": reason}})
    pre = f'[ -n "${env_gate}" ] && ' if env_gate else ""
    return f"{pre}grep -qiE '{pattern}' && printf '%s' '{payload}' || true"


def sandbox_settings(repo_abs: str, mode: str) -> str:
    """Guard JSON for the sandbox: absolute-path Read denies into the repo answer key
    + a case-insensitive substring hook. For CONTROL arms ONLY we add an UNCONDITIONAL
    scaffold guard. Because each arm has its own sandbox settings.json, the guard can be
    arm-specific without an env gate -- a plain grep does not depend on an env var
    reaching the hook process (env propagation to git-bash is unreliable on Windows)."""
    hooks = [
        {"matcher": "Read|Grep|Glob|Bash", "hooks": [
            {"type": "command", "shell": "bash",
             "command": _hook_cmd(_ANSWERKEY_PAT, _ANSWERKEY_REASON)}]},
    ]
    if mode != "rlm":
        hooks.append({"matcher": "Read|Grep|Glob|Bash", "hooks": [
            {"type": "command", "shell": "bash",
             "command": _hook_cmd(_SCAFFOLD_PAT, _SCAFFOLD_REASON)}]})
    cfg = {
        "permissions": {"deny": [
            f"Read({repo_abs}/.claude/skills/rlm/eval/data/contexts_with_labels/**)",
            f"Read({repo_abs}/.claude/skills/rlm/eval/data/oolong_trec_coarse.jsonl)",
            f"Read({repo_abs}/.claude/skills/rlm/eval/_cache/**)",
            f"Read({repo_abs}/.claude/skills/rlm/eval/README.md)",
            f"Read({repo_abs}/rlm_vs_agent_experiment/**)",
        ]},
        "hooks": {"PreToolUse": hooks},
    }
    return json.dumps(cfg, indent=2)


# --------------------------------------------------------------------------- #
# Build / teardown                                                            #
# --------------------------------------------------------------------------- #
def _make_executable(p: Path) -> None:
    try:
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass


def _write_shim(bindir: Path) -> None:
    bindir.mkdir(parents=True, exist_ok=True)
    (bindir / "claude_shim.py").write_text(SHIM_PY, encoding="utf-8")
    sh = bindir / "claude"
    sh.write_text(SHIM_SH, encoding="utf-8", newline="\n")
    _make_executable(sh)
    (bindir / "claude.cmd").write_text(SHIM_CMD, encoding="utf-8", newline="")


def build(task_root: Path, ctx_src: Path, mode: str, repo: Path,
          skill_src: Path) -> Dict[str, Any]:
    """Create a fresh per-task sandbox; return paths the driver needs."""
    task_root = Path(task_root)
    if task_root.exists():
        teardown(task_root)
    task_root.mkdir(parents=True, exist_ok=True)

    ctx_dst = task_root / "context.txt"
    shutil.copyfile(ctx_src, ctx_dst)

    claude_dir = task_root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "settings.json").write_text(sandbox_settings(str(repo), mode), encoding="utf-8")

    info: Dict[str, Any] = {
        "root": task_root, "ctx": ctx_dst.resolve(), "repl": None,
        "state_dir": claude_dir / "rlm_state", "bin": None,
    }

    if mode == "rlm":
        dst_skill = claude_dir / "skills" / "rlm"
        (dst_skill / "scripts").mkdir(parents=True, exist_ok=True)
        # Copy ONLY the operational skill files -- never eval/ (which holds the key).
        shutil.copyfile(skill_src / "SKILL.md", dst_skill / "SKILL.md")
        for p in (skill_src / "scripts").iterdir():
            if p.is_file():
                shutil.copyfile(p, dst_skill / "scripts" / p.name)
        info["repl"] = (dst_skill / "scripts" / "rlm_repl.py").resolve()
    else:
        bindir = task_root / "bin"
        _write_shim(bindir)
        info["bin"] = bindir.resolve()

    # Best-effort: make cwd an unambiguous project root for skill discovery.
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(task_root),
                       capture_output=True, timeout=30)
    except Exception:
        pass
    return info


def _on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def teardown(task_root: Path) -> None:
    shutil.rmtree(Path(task_root), onerror=_on_rm_error)


# --------------------------------------------------------------------------- #
# Static self-test (no model calls): build a dummy sandbox + exercise the shim #
#   python eval_sandbox.py selftest
# --------------------------------------------------------------------------- #
def _selftest() -> int:
    import tempfile
    repo = Path(__file__).resolve().parent.parent
    skill_src = repo / ".claude" / "skills" / "rlm"
    tmp = Path(tempfile.mkdtemp(prefix="rlm_sbx_selftest_"))
    ok = True
    try:
        src_ctx = tmp / "src_ctx.txt"
        src_ctx.write_text("line one\nline two\n", encoding="utf-8")

        # RLM sandbox: skill copied, no eval/, settings valid JSON
        rlm_root = tmp / "rlm"
        info = build(rlm_root, src_ctx, "rlm", repo, skill_src)
        assert (rlm_root / "context.txt").exists(), "ctx missing"
        assert info["repl"].exists(), "repl not copied"
        assert (rlm_root / ".claude/skills/rlm/SKILL.md").exists(), "SKILL.md not copied"
        assert not (rlm_root / ".claude/skills/rlm/eval").exists(), "eval/ leaked into sandbox!"
        json.loads((rlm_root / ".claude/settings.json").read_text(encoding="utf-8"))
        print("[selftest] RLM sandbox OK (skill copied, no eval/, settings valid JSON)")

        # Control sandbox: shim present, no skill
        ctl_root = tmp / "ctl"
        info2 = build(ctl_root, src_ctx, "agent", repo, skill_src)
        for f in ("claude", "claude.cmd", "claude_shim.py"):
            assert (info2["bin"] / f).exists(), f"shim file missing: {f}"
        assert not (ctl_root / ".claude/skills").exists(), "skill leaked into control sandbox!"
        print("[selftest] control sandbox OK (shim present, no skill)")

        # Exercise the shim against a STUB real-claude that emits a json envelope.
        stub = tmp / "stub_claude.py"
        stub.write_text(
            'import json,sys\n'
            'print(json.dumps({"result":"STUB-RESULT","is_error":False,'
            '"total_cost_usd":0.01,"usage":{"input_tokens":3,"output_tokens":5}}))\n',
            encoding="utf-8")
        child_log = tmp / "child_usage.jsonl"
        env = dict(os.environ)
        # Make REAL_CLAUDE a python invocation of the stub via a tiny launcher.
        launcher = tmp / "real_claude_launcher.py"
        launcher.write_text(f'import runpy,sys; sys.argv[0]={str(stub)!r};'
                            f' runpy.run_path({str(stub)!r}, run_name="__main__")\n',
                            encoding="utf-8")
        env["REAL_CLAUDE"] = sys.executable
        env["RLM_CHILD_USAGE_LOG"] = str(child_log)
        # call: python claude_shim.py <launcher> -p hi   (shim prepends real + adds json)
        res = subprocess.run(
            [sys.executable, str(info2["bin"] / "claude_shim.py"), str(stub), "-p", "hi"],
            capture_output=True, text=True, env=env, encoding="utf-8", errors="replace")
        # REAL_CLAUDE=python, args=[stub, -p, hi, --output-format, json] -> stub ignores
        # extra flags and prints the json envelope; shim should emit just the result text.
        transparent = res.stdout.strip() == "STUB-RESULT"
        logged = child_log.exists() and "total_tokens" in child_log.read_text(encoding="utf-8")
        print(f"[selftest] shim transparent={transparent} usage_logged={logged} "
              f"(stdout={res.stdout.strip()!r})")
        ok = transparent and logged
    except AssertionError as e:
        print(f"[selftest] FAIL: {e}")
        ok = False
    finally:
        teardown(tmp)
    print("[selftest]", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(_selftest())
    print(__doc__)
