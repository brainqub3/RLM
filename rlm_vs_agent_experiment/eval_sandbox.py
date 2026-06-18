#!/usr/bin/env python3
"""Per-task BLIND sandbox + env-free child-model accounting for the OOLONG A/B (issue #6).

Each eval session (`claude -p`) runs with cwd = a fresh temp sandbox holding ONLY what
the model legitimately needs, so the answer key (manifest, labels, README stats, _cache,
_archive), other arms' results, and the committed REPORT are not reachable by relative
exploration:

  <sandbox>/
    context.txt                              # the single model-facing context (verbatim)
    .claude/settings.json                    # hardened read-guards (absolute-path backstop)
    .claude/skills/rlm/SKILL.md              # RLM ARM ONLY: skill instructions (no eval/)
    .claude/skills/rlm/scripts/*             # RLM ARM ONLY: rlm_repl.py (+ leaf_log_path.txt)
    bin/{claude,claude.cmd,claude_shim.py}   # CONTROL ARM ONLY: claude accounting shim

ENV-FREE ACCOUNTING (a freshly-passed env var does not reach git-bash on Windows):
  * RLM arm: the copied rlm_repl reads its leaf-usage log path from a sandbox file
    (`scripts/leaf_log_path.txt`) when RLM_LEAF_USAGE_LOG is absent -- so leaf cost is
    captured regardless of env propagation.
  * Control arm: the `claude` shim has REAL_CLAUDE + the child-usage log path BAKED into
    its generated source (env is only a fallback). Its only remaining live dependency is
    PATH resolution of `claude` -> the shim (validated in the live smoke); detection of
    sub-model spawns is transcript-based and env-free.

RESIDUAL (documented honestly): this is a minimized-cwd jail, NOT an OS sandbox -- a
determined session could still try absolute paths into the repo. That is backstopped by
the read-guards written here (answer key, the repo experiment tree, and -- for controls
-- the repo /rlm skill). For non-adversarial eval models this closes the realistic leaks.
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
# The claude accounting shim (control arms only). REAL_CLAUDE + log path are   #
# BAKED in at build time (sentinels replaced); env is only a fallback.         #
# --------------------------------------------------------------------------- #
SHIM_PY = r'''#!/usr/bin/env python3
"""Transparent `claude` accounting shim (eval CONTROL sandboxes, issue #6).

First on a control session's PATH, so any `claude` the control spawns is intercepted:
forward to the REAL claude, capture the call's token/cost usage, append one record to the
child-usage log, and return the real output transparently. The real-claude path and the
log path are BAKED below (env-free); env is only a fallback. Safe-degrading: if anything
in the usage path fails, still return the real output and exit code.
"""
import json, os, subprocess, sys, time

_BAKED_REAL_CLAUDE = @@REAL_CLAUDE@@
_BAKED_CHILD_LOG = @@CHILD_LOG@@
_KEYS = ("input_tokens", "output_tokens",
         "cache_creation_input_tokens", "cache_read_input_tokens")


def _real():
    return _BAKED_REAL_CLAUDE or os.environ.get("REAL_CLAUDE")


def _log_path():
    return _BAKED_CHILD_LOG or os.environ.get("RLM_CHILD_USAGE_LOG")


def _log(rec):
    p = _log_path()
    if not p:
        return
    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _usage_from(obj):
    usage = (obj or {}).get("usage") or {}
    tot = sum(int(usage.get(k, 0) or 0) for k in _KEYS)
    return tot, float((obj or {}).get("total_cost_usd") or 0.0), not bool((obj or {}).get("is_error"))


def _extract_usage(text):
    """Parse a usage object from json OR stream-json (JSONL: last 'result' line)."""
    try:
        return _usage_from(json.loads(text))
    except Exception:
        pass
    last = None
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if isinstance(d, dict) and (d.get("type") == "result" or "usage" in d):
            last = d
    return _usage_from(last) if last else (0, 0.0, True)


def main(argv):
    real = _real()
    if not real:
        sys.stderr.write("[claude_shim] no REAL_CLAUDE baked or in env; cannot forward\n")
        return 127
    args = list(argv)
    has_fmt = any(a == "--output-format" or a.startswith("--output-format=") for a in args)
    capture = not has_fmt   # add json only if the caller did not ask for a format
    run_args = [real] + args + (["--output-format", "json"] if capture else [])
    try:
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
            tot, cost, ok = _usage_from(d)
            _log({"ts": time.time(), "ok": ok, "total_tokens": tot, "cost_usd": cost, "via": "shim"})
            sys.stdout.write(d.get("result") or "")
            sys.stderr.write(res.stderr or "")
            return res.returncode
        # caller chose its own format: pass output through untouched; best-effort usage
        sys.stdout.write(out)
        sys.stderr.write(res.stderr or "")
        tot, cost, ok = _extract_usage(out)
        if tot or cost:
            _log({"ts": time.time(), "ok": ok, "total_tokens": tot, "cost_usd": cost,
                  "via": "shim-passthrough"})
        return res.returncode
    except Exception:
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
# Hardened read-guard backstop (case-insensitive; separator-free tokens, and  #
# `eval..?readme` tolerates one or two path separators incl. JSON-escaped \\). #
# --------------------------------------------------------------------------- #
_ANSWERKEY_PAT = ("_archive|contexts_with_labels|_cache|verify_eval|oolong_trec_coarse|"
                  "gold_label_stats|rlm_vs_agent_experiment|eval..?readme")
# control sandboxes additionally block the repo /rlm scaffold + skill doc
_CONTROL_BLOCK_PAT = "rlm_repl|llm_query|rlm_query|skill\\.md"
_ANSWERKEY_REASON = ("Blocked (sandbox backstop): off-limits OOLONG answer key or the "
                     "repo experiment tree for the blind eval (issue #6). Score out-of-band "
                     "with score.py.")
_CONTROL_REASON = ("Blocked: a RLM-OFF control may not use or read the /rlm scaffold or skill "
                   "doc (rlm_repl / llm_query / rlm_query / SKILL.md). Issue #6: control runs "
                   "the skill OFF.")


def _hook_cmd(pattern: str, reason: str) -> str:
    payload = json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": reason}})
    return f"grep -qiE '{pattern}' && printf '%s' '{payload}' || true"


def sandbox_settings(repo_abs: str, mode: str) -> str:
    """Guard JSON for the sandbox. CONTROL sandboxes also (a) deny the repo /rlm skill by
    absolute path and (b) carry an UNCONDITIONAL scaffold+skill-doc grep -- arm-specific
    (each arm has its own sandbox settings) so no env gate is needed."""
    deny = [
        f"Read({repo_abs}/.claude/skills/rlm/eval/data/contexts_with_labels/**)",
        f"Read({repo_abs}/.claude/skills/rlm/eval/data/oolong_trec_coarse.jsonl)",
        f"Read({repo_abs}/.claude/skills/rlm/eval/_cache/**)",
        f"Read({repo_abs}/.claude/skills/rlm/eval/README.md)",
        f"Read({repo_abs}/rlm_vs_agent_experiment/**)",
    ]
    hooks = [
        {"matcher": "Read|Grep|Glob|Bash", "hooks": [
            {"type": "command", "shell": "bash",
             "command": _hook_cmd(_ANSWERKEY_PAT, _ANSWERKEY_REASON)}]},
    ]
    if mode != "rlm":
        # control must not reach the repo's own /rlm skill (relative copy absent; this
        # blocks the absolute-path route Codex flagged -- e.g. reading repo SKILL.md).
        deny.append(f"Read({repo_abs}/.claude/skills/rlm/**)")
        hooks.append({"matcher": "Read|Grep|Glob|Bash", "hooks": [
            {"type": "command", "shell": "bash",
             "command": _hook_cmd(_CONTROL_BLOCK_PAT, _CONTROL_REASON)}]})
    return json.dumps({"permissions": {"deny": deny}, "hooks": {"PreToolUse": hooks}}, indent=2)


# --------------------------------------------------------------------------- #
# Build / teardown                                                            #
# --------------------------------------------------------------------------- #
def _make_executable(p: Path) -> None:
    try:
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass


def _write_shim(bindir: Path, real_claude: Optional[str], child_log: Optional[str]) -> None:
    bindir.mkdir(parents=True, exist_ok=True)
    body = (SHIM_PY
            .replace("@@REAL_CLAUDE@@", repr(real_claude) if real_claude else "None")
            .replace("@@CHILD_LOG@@", repr(child_log) if child_log else "None"))
    (bindir / "claude_shim.py").write_text(body, encoding="utf-8")
    sh = bindir / "claude"
    sh.write_text(SHIM_SH, encoding="utf-8", newline="\n")
    _make_executable(sh)
    (bindir / "claude.cmd").write_text(SHIM_CMD, encoding="utf-8", newline="")


# env-free leaf accounting: make the copied rlm_repl read the log path from a sandbox
# file when RLM_LEAF_USAGE_LOG is not in its environment.
_REPL_OLD = ('def _leaf_usage_log_path() -> Optional[str]:\n'
             '    p = os.environ.get("RLM_LEAF_USAGE_LOG", "").strip()\n'
             '    return p or None')
_REPL_NEW = ('def _leaf_usage_log_path() -> Optional[str]:\n'
             '    p = os.environ.get("RLM_LEAF_USAGE_LOG", "").strip()\n'
             '    if not p:  # env may not reach git-bash; fall back to a sandbox file\n'
             '        try:\n'
             '            _cfg = Path(__file__).resolve().parent / "leaf_log_path.txt"\n'
             '            if _cfg.exists():\n'
             '                p = _cfg.read_text(encoding="utf-8").strip()\n'
             '        except Exception:\n'
             '            p = ""\n'
             '    return p or None')


def build(task_root: Path, ctx_src: Path, mode: str, repo: Path, skill_src: Path,
          real_claude: Optional[str] = None, usage_log: Optional[str] = None) -> Dict[str, Any]:
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
        repl_dst = dst_skill / "scripts" / "rlm_repl.py"
        # env-free leaf accounting: patch the COPY + drop a config file
        try:
            txt = repl_dst.read_text(encoding="utf-8")
            if _REPL_OLD in txt:
                repl_dst.write_text(txt.replace(_REPL_OLD, _REPL_NEW), encoding="utf-8")
        except Exception:
            pass
        if usage_log:
            (dst_skill / "scripts" / "leaf_log_path.txt").write_text(str(usage_log), encoding="utf-8")
        info["repl"] = repl_dst.resolve()
    else:
        bindir = task_root / "bin"
        _write_shim(bindir, real_claude, usage_log)
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
# Static self-test (no model calls): build dummy sandboxes + exercise the shim #
#   python eval_sandbox.py selftest                                            #
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

        rlm_log = tmp / "rlm_leaf.jsonl"
        info = build(tmp / "rlm", src_ctx, "rlm", repo, skill_src, usage_log=str(rlm_log))
        assert (tmp / "rlm/context.txt").exists(), "ctx missing"
        assert info["repl"].exists(), "repl not copied"
        assert (tmp / "rlm/.claude/skills/rlm/SKILL.md").exists(), "SKILL.md not copied"
        assert not (tmp / "rlm/.claude/skills/rlm/eval").exists(), "eval/ leaked into sandbox!"
        assert (tmp / "rlm/.claude/skills/rlm/scripts/leaf_log_path.txt").exists(), "leaf cfg missing"
        assert "leaf_log_path.txt" in info["repl"].read_text(encoding="utf-8"), "rlm_repl not patched"
        json.loads((tmp / "rlm/.claude/settings.json").read_text(encoding="utf-8"))
        print("[selftest] RLM sandbox OK (skill copied, no eval/, leaf cfg + patch present)")

        stub = tmp / "stub_claude.py"
        stub.write_text(
            'import json,sys\n'
            'print(json.dumps({"result":"STUB-RESULT","is_error":False,'
            '"total_cost_usd":0.01,"usage":{"input_tokens":3,"output_tokens":5}}))\n',
            encoding="utf-8")
        child_log = tmp / "child_usage.jsonl"
        info2 = build(tmp / "ctl", src_ctx, "agent", repo, skill_src,
                      real_claude=sys.executable, usage_log=str(child_log))
        for f in ("claude", "claude.cmd", "claude_shim.py"):
            assert (info2["bin"] / f).exists(), f"shim file missing: {f}"
        assert not (tmp / "ctl/.claude/skills").exists(), "skill leaked into control sandbox!"
        shimsrc = (info2["bin"] / "claude_shim.py").read_text(encoding="utf-8")
        assert "@@REAL_CLAUDE@@" not in shimsrc and "@@CHILD_LOG@@" not in shimsrc, "shim not baked"
        # exercise the baked shim against the stub (REAL_CLAUDE baked = sys.executable)
        res = subprocess.run([sys.executable, str(info2["bin"] / "claude_shim.py"), str(stub), "-p", "hi"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        transparent = res.stdout.strip() == "STUB-RESULT"
        logged = child_log.exists() and "total_tokens" in child_log.read_text(encoding="utf-8")
        print(f"[selftest] control sandbox OK; baked shim transparent={transparent} usage_logged={logged}")
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
