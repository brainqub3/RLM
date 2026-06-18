#!/usr/bin/env python3
"""Run the OOLONG (trec_coarse) eval end-to-end with the RLM method, capturing
per-item score-ready predictions PLUS token/cost usage and wall-clock time.

This is a faithful, automated driver of the `rlm` skill's strategy for the
homogeneous OOLONG aggregation task. It reproduces the skill's leaf mechanism
EXACTLY -- a nested headless Claude Code (`claude -p`), tools OFF, default model
`haiku`, the skill's leaf system prompt -- adding only `--output-format json` so
each leaf call's `usage` and `total_cost_usd` can be summed. The decomposition is
the one the skill's SKILL.md prescribes for OOLONG:

    LLM does the SEMANTICS  -> classify every question into one of the 6 labels
    Python does the ARITHMETIC -> count the labels, then answer the distributional
                                  question (most/least common, how many, A vs B)

The "root model" orchestration here is deterministic Python (this file), so the
method consumes NO root-LLM tokens -- the reported tokens are the leaf classifier
calls only, which is the dominant and the only LLM cost of the RLM loop for this
task. Each of the 10 manifest items is run as an INDEPENDENT RLM pass (its whole
context is re-classified from scratch), so the per-item tokens/cost/time are what
one isolated `/rlm` invocation on that item would consume.

Outputs (under eval/):
  preds_rlm.jsonl     -- {id, output, total_tokens, total_cost_usd} per item (scorer input)
  _runs/rlm_run.json  -- full diagnostics (per-item timing, counts, coverage, calls)

Usage:
  python run_rlm_eval.py                 # run all 10 items
  python run_rlm_eval.py --batch 120 --workers 10 --model haiku
  python run_rlm_eval.py --ids 17000206,17000208   # subset (e.g. one per context)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "data" / "oolong_trec_coarse.jsonl"
PREDS_OUT = HERE / "preds_rlm.jsonl"
RUNLOG_OUT = HERE / "_runs" / "rlm_run.json"

# Faithful copy of the skill's leaf system prompt (rlm_repl.DEFAULT_LEAF_SYSTEM).
LEAF_SYSTEM = (
    "You are a sub-LLM invoked programmatically inside a larger system. "
    "Answer the query precisely using only the provided text. "
    "Output only the answer in the exact format requested, with no preamble, "
    "explanation, or markdown fences unless explicitly asked."
)

# The 6 trec_coarse labels, verbatim as they appear in the questions / gold.
CANON = [
    "numeric value", "entity", "human being",
    "location", "abbreviation", "description and abstract concept",
]
CANON_SET = set(CANON)

INSTANCE_RE = re.compile(r"\|\| Instance:\s?(.*)$")
HEADER_COUNT_RE = re.compile(r"contain (\d+) general-knowledge questions")
Q_LABEL_RE = re.compile(r"label '([^']+)'")
LINE_RE = re.compile(r"^\s*(\d+)\s*[:.\)]\s*(.+?)\s*$")


# --------------------------------------------------------------------------- #
# Leaf call: the skill's `claude -p` sub-LM, with JSON usage capture          #
# --------------------------------------------------------------------------- #
def _claude_exe() -> str:
    exe = shutil.which("claude")
    if not exe:
        sys.exit("ERROR: `claude` CLI not found on PATH.")
    return exe


CLAUDE = None  # resolved lazily


def leaf_call(prompt: str, model: str, timeout: int = 240) -> Dict[str, Any]:
    """One sub-LM leaf call (tools OFF, JSON output). Returns
    {ok, text, tokens, cost, err}. Never raises -- a failed call yields ok=False
    and its items get re-classified by the coverage loop."""
    global CLAUDE
    CLAUDE = CLAUDE or _claude_exe()
    cmd = [CLAUDE, "-p", "--model", model, "--allowedTools", "",
           "--append-system-prompt", LEAF_SYSTEM, "--output-format", "json"]
    try:
        res = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                             timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {"ok": False, "text": "", "tokens": 0, "cost": 0.0, "err": f"TIMEOUT/{timeout}s"}
    except Exception as e:  # pragma: no cover
        return {"ok": False, "text": "", "tokens": 0, "cost": 0.0, "err": f"{type(e).__name__}:{e}"}
    if res.returncode != 0 and not (res.stdout or "").strip():
        return {"ok": False, "text": "", "tokens": 0, "cost": 0.0,
                "err": f"rc={res.returncode} {(res.stderr or '')[:160]}"}
    try:
        d = json.loads(res.stdout)
    except Exception as e:
        return {"ok": False, "text": "", "tokens": 0, "cost": 0.0, "err": f"jsonparse:{e}"}
    u = d.get("usage") or {}
    tokens = sum(int(u.get(k, 0) or 0) for k in (
        "input_tokens", "output_tokens",
        "cache_creation_input_tokens", "cache_read_input_tokens"))
    cost = float(d.get("total_cost_usd") or 0.0)
    text = (d.get("result") or "").strip()
    is_err = bool(d.get("is_error"))
    return {"ok": (not is_err) and bool(text), "text": text,
            "tokens": tokens, "cost": cost, "err": "" if not is_err else "is_error"}


# --------------------------------------------------------------------------- #
# Classification (LLM = semantics)                                            #
# --------------------------------------------------------------------------- #
def normalize_label(raw: str) -> Optional[str]:
    s = raw.strip().lower().strip("*[]().:'\" ").strip()
    s = re.sub(r"\s+", " ", s)
    if s in CANON_SET:
        return s
    if "numeric" in s or s in {"number", "num", "value", "count", "quantity",
                               "date", "expression", "ranking", "code", "money", "distance"}:
        return "numeric value"
    if "abbrev" in s or "acronym" in s:
        return "abbreviation"
    if "human" in s or "person" in s or "people" in s or "individual" in s or "group" in s:
        return "human being"
    if "location" in s or "place" in s or "country" in s or "city" in s:
        return "location"
    if ("description" in s or "abstract" in s or "concept" in s or "definition" in s
            or s.startswith("desc") or "manner" in s or "reason" in s):
        return "description and abstract concept"
    if "entity" in s or "entities" in s or "thing" in s or "object" in s:
        return "entity"
    return None


def build_classify_prompt(numbered: List[Tuple[int, str]]) -> str:
    body = "\n".join(f"{i}: {q}" for i, q in numbered)
    return (
        "Classify each general-knowledge question by the TYPE OF ANSWER it expects, "
        "into EXACTLY ONE of these six categories (use the exact category string):\n"
        "- numeric value  (a number, count, date, quantity, percentage, or amount)\n"
        "- entity  (a thing/animal/plant/object/organization/product/work/substance)\n"
        "- human being  (a person, group of people, or who-question)\n"
        "- location  (a place: city, country, region, geographic feature)\n"
        "- abbreviation  (an acronym, or the expansion of an abbreviation)\n"
        "- description and abstract concept  (a definition, reason, manner, or abstract idea)\n\n"
        "For EACH numbered question output exactly one line in the form:\n"
        "<number>: <category>\n"
        "Output one line per question, in order, and NOTHING else.\n\n"
        + body
    )


def classify_all(questions: List[str], model: str, batch: int, workers: int,
                 timeout: int, log) -> Dict[str, Any]:
    """Classify every question. Returns labels list (len==len(questions); None for
    unmapped/missing) plus accumulated usage and call diagnostics."""
    n = len(questions)
    labels: List[Optional[str]] = [None] * n
    tokens_total = 0
    cost_total = 0.0
    n_calls = 0
    n_failed = 0
    n_unmapped = 0

    def run_indices(indices: List[int]) -> None:
        nonlocal tokens_total, cost_total, n_calls, n_failed, n_unmapped
        # group into contiguous-ish batches of `batch`
        groups = [indices[i:i + batch] for i in range(0, len(indices), batch)]
        prompts = [build_classify_prompt([(i, questions[i]) for i in g]) for g in groups]

        def worker(p):
            return leaf_call(p, model=model, timeout=timeout)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(worker, prompts))
        for g, r in zip(groups, results):
            n_calls += 1
            tokens_total += r["tokens"]
            cost_total += r["cost"]
            if not r["ok"]:
                n_failed += 1
                continue
            gset = set(g)
            for ln in r["text"].splitlines():
                m = LINE_RE.match(ln)
                if not m:
                    continue
                idx = int(m.group(1))
                if idx not in gset:
                    continue
                lab = normalize_label(m.group(2))
                if lab is None:
                    n_unmapped += 1
                labels[idx] = lab  # may be None if unmapped

    # round 0: all questions
    run_indices(list(range(n)))
    # coverage re-runs: re-classify any index still without a mapped label
    for rnd in range(1, 6):
        missing = [i for i in range(n) if labels[i] is None]
        if not missing:
            break
        log(f"      re-run {rnd}: {len(missing)} unlabeled/unmapped item(s)")
        run_indices(missing)

    labeled = [l for l in labels if l is not None]
    return {
        "labels": labels,
        "counts": Counter(labeled),
        "n_questions": n,
        "n_labeled": len(labeled),
        "tokens": tokens_total,
        "cost": cost_total,
        "n_calls": n_calls,
        "n_failed_calls": n_failed,
        "n_unmapped": n_unmapped,
    }


# --------------------------------------------------------------------------- #
# Aggregation (Python = arithmetic) -> answer in the exact requested format    #
# --------------------------------------------------------------------------- #
def answer_for(item: Dict[str, Any], counts: Counter) -> str:
    task = item["task"]
    q = item["question"]
    # restrict to the 6 canonical labels for argmin/argmax determinism
    canon_counts = {c: counts.get(c, 0) for c in CANON}
    if task == "TASK_TYPE.MOST_FREQ":
        top = max(CANON, key=lambda c: (canon_counts[c], -CANON.index(c)))
        return f"Label: {top}"
    if task == "TASK_TYPE.LEAST_FREQ":
        bot = min(CANON, key=lambda c: (canon_counts[c], CANON.index(c)))
        return f"Label: {bot}"
    if task == "TASK_TYPE.NUMERIC_ONE_CLASS":
        lab = Q_LABEL_RE.search(q).group(1)
        return f"Answer: {counts.get(lab, 0)}"
    if task == "TASK_TYPE.RELATIVE_FREQ":
        a, b = Q_LABEL_RE.findall(q)[:2]
        ca, cb = counts.get(a, 0), counts.get(b, 0)
        rel = ("more common than" if ca > cb
               else "less common than" if ca < cb else "same frequency as")
        return f"Answer: {a} is {rel} {b}"
    return "Answer: unknown"


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #
def load_manifest() -> List[Dict[str, Any]]:
    return [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]


def extract_questions(ctx_path: Path) -> Tuple[List[str], Optional[int]]:
    text = ctx_path.read_text(encoding="utf-8")
    qs: List[str] = []
    for line in text.splitlines():
        m = INSTANCE_RE.search(line)
        if m:
            qs.append(m.group(1).strip())
    hdr = HEADER_COUNT_RE.search(text)
    return qs, (int(hdr.group(1)) if hdr else None)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--batch", type=int, default=120)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--ids", default=None, help="comma-separated subset of item ids")
    args = ap.parse_args(argv)

    items = load_manifest()
    if args.ids:
        want = {int(x) for x in args.ids.split(",") if x.strip()}
        items = [it for it in items if int(it["id"]) in want]

    def log(msg: str) -> None:
        print(msg, flush=True)

    RUNLOG_OUT.parent.mkdir(parents=True, exist_ok=True)
    run_started = time.time()
    log(f"RLM OOLONG eval | model={args.model} batch={args.batch} workers={args.workers} "
        f"| {len(items)} items")
    log("=" * 78)

    diagnostics: List[Dict[str, Any]] = []
    preds_lines: List[str] = []
    qcache: Dict[str, Tuple[List[str], Optional[int]]] = {}

    for n_done, item in enumerate(items, 1):
        iid = int(item["id"])
        cf = item["context_file"]
        log(f"[{n_done}/{len(items)}] id={iid} {item['task']} cw{item['context_window_id']} "
            f"({cf})")
        t0 = time.time()
        if cf not in qcache:
            qcache[cf] = extract_questions(HERE / "data" / Path(cf))
        questions, header_n = qcache[cf]
        if header_n is not None and header_n != len(questions):
            log(f"      WARN: header says {header_n} but extracted {len(questions)} questions")

        cls = classify_all(questions, model=args.model, batch=args.batch,
                           workers=args.workers, timeout=args.timeout, log=log)
        output = answer_for(item, cls["counts"])
        dt = time.time() - t0

        dist = ", ".join(f"{c}={cls['counts'].get(c, 0)}" for c in CANON)
        log(f"      coverage {cls['n_labeled']}/{cls['n_questions']} "
            f"| calls={cls['n_calls']} (failed={cls['n_failed_calls']}, unmapped={cls['n_unmapped']})")
        log(f"      dist: {dist}")
        log(f"      -> {output}   [{dt:.1f}s, {cls['tokens']:,} tok, ${cls['cost']:.4f}]")
        log("-" * 78)

        preds_lines.append(json.dumps({
            "id": iid, "output": output,
            "total_tokens": cls["tokens"], "total_cost_usd": round(cls["cost"], 6),
        }))
        diagnostics.append({
            "id": iid, "task": item["task"], "answer_type": item["answer_type"],
            "context_window_id": item["context_window_id"], "context_file": cf,
            "gold": item["answer"], "question": item["question"],
            "output": output, "wall_seconds": round(dt, 2),
            "total_tokens": cls["tokens"], "total_cost_usd": round(cls["cost"], 6),
            "n_calls": cls["n_calls"], "n_failed_calls": cls["n_failed_calls"],
            "n_questions": cls["n_questions"], "n_labeled": cls["n_labeled"],
            "n_unmapped": cls["n_unmapped"],
            "label_counts": {c: cls["counts"].get(c, 0) for c in CANON},
        })
        # write incrementally so a crash still leaves partial results
        PREDS_OUT.write_text("\n".join(preds_lines) + "\n", encoding="utf-8")
        RUNLOG_OUT.write_text(json.dumps({
            "model": args.model, "batch": args.batch, "workers": args.workers,
            "started_unix": run_started, "items": diagnostics,
            "elapsed_seconds_so_far": round(time.time() - run_started, 2),
        }, indent=2), encoding="utf-8")

    total_dt = time.time() - run_started
    tok = sum(d["total_tokens"] for d in diagnostics)
    cost = sum(d["total_cost_usd"] for d in diagnostics)
    calls = sum(d["n_calls"] for d in diagnostics)
    log("=" * 78)
    log(f"DONE {len(items)} items in {total_dt:.1f}s ({total_dt/60:.1f} min) "
        f"| {calls} leaf calls | {tok:,} tokens | ${cost:.4f}")
    log(f"predictions -> {PREDS_OUT}")
    log(f"diagnostics -> {RUNLOG_OUT}")
    # stamp final totals into the run log
    rl = json.loads(RUNLOG_OUT.read_text(encoding="utf-8"))
    rl["elapsed_seconds_total"] = round(total_dt, 2)
    rl["total_tokens"] = tok
    rl["total_cost_usd"] = round(cost, 6)
    rl["total_leaf_calls"] = calls
    RUNLOG_OUT.write_text(json.dumps(rl, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
