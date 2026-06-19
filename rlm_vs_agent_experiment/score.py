#!/usr/bin/env python3
"""Scorer for the OOLONG (trec_coarse) long-context eval subset.

Method-agnostic: it scores a predictions file produced by ANY system (a base
model call, an agent, a long-context scaffold, the RLM skill, etc.) and -- if the
predictions include token/cost usage -- reports the totals consumed in the run.

This is a faithful, dependency-free re-implementation of the official
OOLONG-synth scorer (`synth_process_response` / `synth_attempt_answer_parse`)
from https://github.com/abertsch72/oolong (src/eval/eval_helpers.py).
A copy of the upstream reference is kept in ./_upstream_ref/ for provenance.

Scoring rules (per item), mirroring upstream:
  * The gold `answer` is a stringified list; the scored gold is its FIRST element
    (`ast.literal_eval(answer)[0]`), or a date if the answer encodes a datetime.
  * The model's free-text output is parsed: take the text after the last ':',
    strip markdown '*' and brackets '[' ']'.
  * Exact string match -> score 1.0.
  * COMPARISON answers ('more common than' / 'less common than' /
    'same frequency as') are matched by substring (wording may vary slightly).
  * NUMERIC answers get partial credit: 0.75 ** abs(gold - pred).
  * DATE answers are parsed and compared for equality.

Usage:
  # Score model predictions against the manifest:
  python score.py --predictions preds.jsonl
  # preds.jsonl: one JSON object per line:
  #   {"id": <int>, "output": "<model text>"}
  # Optionally record usage to have it aggregated and reported:
  #   {"id": <int>, "output": "...", "total_tokens": 12345, "total_cost_usd": 0.01}
  # (or input_tokens/output_tokens/cache_* fields, or a nested "usage" object such
  #  as the one returned by `claude -p --output-format json`.)

  # Sanity check the eval itself (feed gold answers back in -> should be ~1.0):
  python score.py --self-test

  # Use a non-default manifest location:
  python score.py --manifest data/oolong_trec_coarse.jsonl --predictions preds.jsonl

Exit code is 0 on success regardless of score; non-zero only on usage errors.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
# The manifest lives at the experiment root (same place the driver reads it from,
# run_rlm_skill_eval.py: MANIFEST = HERE / "oolong_trec_coarse.jsonl"). Fall back to
# the legacy data/ subdir layout if a root copy isn't present.
DEFAULT_MANIFEST = HERE / "oolong_trec_coarse.jsonl"
if not DEFAULT_MANIFEST.exists():
    DEFAULT_MANIFEST = HERE / "data" / "oolong_trec_coarse.jsonl"

COMPARISON_PHRASES = ("more common", "less common", "same frequency")


# --- upstream: synth_attempt_answer_parse -----------------------------------
def attempt_answer_parse(answer: str) -> Tuple[str, str]:
    """Port of synth_attempt_answer_parse. Returns (candidate, confidence)."""
    parse_confidence = "low"
    if ":" not in answer:  # bad start
        if len(answer) < 20:  # short -> return whole thing
            return answer, parse_confidence
        # Deliberate deviation from upstream: guard the empty/all-whitespace case
        # (bare `answer.split()[-1]` would IndexError there). Real outputs never hit it.
        return answer.split()[-1] if answer.split() else answer, parse_confidence

    candidate = answer.split(":")[-1].strip()
    candidate = candidate.replace("*", "")  # models like bolding
    candidate = candidate.replace("[", "").replace("]", "")  # and bracketing
    parse_confidence = "med"
    if ("User:" in answer or "Answer:" in answer
            or "Date:" in answer or "Label" in answer):
        parse_confidence = "high"
    if len(candidate) < 20:
        parse_confidence = "vhigh"
    elif "more common" in candidate:
        candidate = "more common"
    elif "less common" in candidate:
        candidate = "less common"
    elif "same frequency" in candidate:
        candidate = "same frequency"
    return candidate, parse_confidence


def _gold_value(answer_field: str) -> Any:
    """Port of the gold extraction in synth_process_response.

    NOTE: like upstream, this takes element [0] of the gold list — it assumes a
    single-element gold. If the gold is a genuine tie (>1 valid label), only the
    first is credited. This subset has no multi-element golds (see verify_eval.py).
    """
    if "datetime" not in answer_field:
        return ast.literal_eval(answer_field)[0]
    return datetime.strptime(answer_field, "[datetime.date(%Y, %m, %d)]")


# --- upstream: synth_process_response (scoring core) ------------------------
def score_one(answer_field: str, answer_type: str, output: str) -> Dict[str, Any]:
    """Score a single model `output` against the stringified gold `answer_field`."""
    score: float = 0.0
    gold = _gold_value(answer_field)
    trimmed, conf = attempt_answer_parse(output)

    if str(trimmed) == str(gold):
        score = 1.0
    elif str(trimmed) in ("more common", "less common", "same frequency"):
        if str(trimmed) in str(gold):
            score = 1.0
    elif answer_type == "ANSWER_TYPE.NUMERIC":  # partial credit for numbers
        try:
            score = 0.75 ** (abs(int(gold) - int(trimmed)))
        except Exception:
            conf = "low"
    elif answer_type == "ANSWER_TYPE.DATE":
        try:
            import dateutil.parser  # optional; only needed for date tasks
            parsed = dateutil.parser.parse(trimmed)
            score = float(parsed == gold)
        except Exception:
            # No dateutil available: best-effort match on the date-only form. `gold`
            # is a datetime, so str(gold) carries a time component; compare against
            # its YYYY-MM-DD form too, so a correctly-formatted date still scores 1.
            gold_date = gold.date() if hasattr(gold, "date") else gold
            score = float(str(trimmed).strip() in (str(gold), str(gold_date)))
            conf = "low"

    return {
        "attempted_parse": str(trimmed),
        "parse_confidence": conf,
        "score": float(score),
        "gold": str(gold),
    }


def load_manifest(path: Path) -> List[Dict[str, Any]]:
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def _extract_usage(obj: Dict[str, Any]) -> Tuple[Optional[int], Optional[float]]:
    """Pull a total-token count and (optional) USD cost from a prediction line.

    All fields are optional -- the eval is method-agnostic, so a runner records
    whatever its system reports. Token sources, in priority order:
      1. obj["total_tokens"] or obj["tokens"]
      2. obj["usage"]["total_tokens"]
      3. sum of the *_tokens components found at obj-level or in obj["usage"]
         (input_tokens, output_tokens, cache_creation_input_tokens,
          cache_read_input_tokens) -- matches `claude -p --output-format json`.
    Cost sources: obj["total_cost_usd"] / obj["cost_usd"] / obj["cost"].
    """
    usage = obj.get("usage") if isinstance(obj.get("usage"), dict) else {}
    tokens: Optional[int] = None
    for k in ("total_tokens", "tokens"):
        if isinstance(obj.get(k), (int, float)):
            tokens = int(obj[k])
            break
    if tokens is None and isinstance(usage.get("total_tokens"), (int, float)):
        tokens = int(usage["total_tokens"])
    if tokens is None:
        parts = []
        for k in ("input_tokens", "output_tokens",
                  "cache_creation_input_tokens", "cache_read_input_tokens"):
            v = obj.get(k, usage.get(k))
            if isinstance(v, (int, float)):
                parts.append(int(v))
        if parts:
            tokens = sum(parts)
    cost: Optional[float] = None
    for k in ("total_cost_usd", "cost_usd", "cost"):
        if isinstance(obj.get(k), (int, float)):
            cost = float(obj[k])
            break
    return tokens, cost


def load_predictions(path: Path) -> Dict[int, Dict[str, Any]]:
    preds: Dict[int, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            tokens, cost = _extract_usage(obj)
            preds[int(obj["id"])] = {
                "output": obj.get("output", ""),
                "tokens": tokens,
                "cost": cost,
            }
    return preds


def gold_as_text(item: Dict[str, Any]) -> str:
    """Render the gold answer the way the question asks for it (for self-test)."""
    gold = _gold_value(item["answer"])
    at = item["answer_type"]
    if at == "ANSWER_TYPE.LABEL":
        return f"Label: {gold}"
    if at == "ANSWER_TYPE.NUMERIC":
        return f"Answer: {gold}"
    if at == "ANSWER_TYPE.COMPARISON":
        # question wants "Answer: A is [X] B"; the parser keys off the phrase
        return f"Answer: {gold}"
    if at == "ANSWER_TYPE.DATE":
        return f"Date: {gold}"
    return f"Answer: {gold}"


def run(items: List[Dict[str, Any]], preds: Dict[int, Dict[str, Any]], verbose: bool) -> float:
    total = 0.0
    n = 0
    missing = 0
    tok_total, tok_items = 0, 0
    cost_total, cost_items = 0.0, 0
    print(f"{'id':>11}  {'score':>5}  {'answer_type':<22} {'gold':<22} {'tokens':>10}  parse")
    print("-" * 100)
    for it in items:
        iid = int(it["id"])
        if iid not in preds:
            missing += 1
            if verbose:
                print(f"{iid:>11}  {'--':>5}  (no prediction)")
            continue
        entry = preds[iid]
        res = score_one(it["answer"], it["answer_type"], entry["output"])
        total += res["score"]
        n += 1
        tok = entry.get("tokens")
        if tok is not None:
            tok_total += tok
            tok_items += 1
        if entry.get("cost") is not None:
            cost_total += entry["cost"]
            cost_items += 1
        tok_str = f"{tok:,}" if tok is not None else "-"
        print(f"{iid:>11}  {res['score']:>5.2f}  {it['answer_type']:<22} "
              f"{res['gold'][:22]:<22} {tok_str:>10}  {res['attempted_parse'][:30]!r}")
    print("-" * 100)
    avg = (total / n) if n else 0.0
    print(f"Scored {n} items | mean score = {avg:.4f} ({avg*100:.1f}%)"
          + (f" | {missing} without predictions" if missing else ""))
    if tok_items:
        print(f"Tokens | total = {tok_total:,} | mean/item = {tok_total / tok_items:,.0f}"
              f" (reported for {tok_items}/{n} items)")
    if cost_items:
        print(f"Cost   | total = ${cost_total:.4f} | mean/item = ${cost_total / cost_items:.4f}"
              f" (reported for {cost_items}/{n} items)")
    return avg


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST),
                    help=f"Path to manifest JSONL (default: {DEFAULT_MANIFEST})")
    ap.add_argument("--predictions", default=None,
                    help="JSONL of {'id':int,'output':str} model predictions")
    ap.add_argument("--self-test", action="store_true",
                    help="Feed gold answers back as predictions (should score ~1.0)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        sys.stderr.write(f"ERROR: manifest not found: {manifest_path}\n")
        return 2
    items = load_manifest(manifest_path)

    if args.self_test:
        preds = {int(it["id"]): {"output": gold_as_text(it), "tokens": None, "cost": None}
                 for it in items}
        avg = run(items, preds, args.verbose)
        if avg < 0.999:
            sys.stderr.write("WARNING: self-test below 1.0 — scorer/manifest mismatch.\n")
        return 0

    if not args.predictions:
        sys.stderr.write("ERROR: provide --predictions FILE or --self-test\n")
        return 2
    preds_path = Path(args.predictions)
    if not preds_path.exists():
        sys.stderr.write(f"ERROR: predictions not found: {preds_path}\n")
        return 2
    preds = load_predictions(preds_path)
    run(items, preds, args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
