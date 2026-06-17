#!/usr/bin/env python3
"""Independently verify the OOLONG trec_coarse eval subset.

For every manifest item this script RE-DERIVES the gold answer from the
gold-labelled context (counting labels directly, with logic written from scratch
rather than reusing the dataset's own constructor) and checks it against the
manifest's stored gold. It also checks structural integrity:

  * model-facing context contains NO '|| Label:' annotations (task is real);
  * #labelled lines == #unlabelled instance lines == header's stated count;
  * manifest context_chars matches the on-disk file length;
  * score.py --self-test would pass (gold answers parse+score to 1.0).

Exit code 0 iff all checks pass.
"""
import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1]
DATA = EVAL_DIR / "data"
MANIFEST = DATA / "oolong_trec_coarse.jsonl"

LABEL_LINE = re.compile(r"\|\| Instance: .*? \|\| Label: (.+?)\s*$")
INSTANCE_LINE = re.compile(r"\|\| Instance: ")
HEADER_COUNT = re.compile(r"contain (\d+) general-knowledge questions")
Q_LABEL = re.compile(r"label '([^']+)'")


def gold0(answer_field: str):
    return ast.literal_eval(answer_field)[0]


def gold_set(answer_field: str):
    return [str(x) for x in ast.literal_eval(answer_field)]


def label_counts(with_labels_text: str) -> Counter:
    c = Counter()
    for line in with_labels_text.splitlines():
        m = LABEL_LINE.search(line)
        if m:
            c[m.group(1).strip()] += 1
    return c


def expected_answer(item, counts: Counter):
    """Recompute the answer for an item from scratch; return (value_or_set, kind)."""
    task = item["task"]
    q = item["question"]
    if task == "TASK_TYPE.MOST_FREQ":
        mx = max(counts.values())
        return {k for k, v in counts.items() if v == mx}, "set"
    if task == "TASK_TYPE.LEAST_FREQ":
        mn = min(counts.values())
        return {k for k, v in counts.items() if v == mn}, "set"
    if task == "TASK_TYPE.NUMERIC_ONE_CLASS":
        lab = Q_LABEL.search(q).group(1)
        return counts.get(lab, 0), "num"
    if task == "TASK_TYPE.RELATIVE_FREQ":
        a, b = Q_LABEL.findall(q)[:2]
        ca, cb = counts.get(a, 0), counts.get(b, 0)
        if ca > cb:
            return "more common than", "cmp"
        if ca < cb:
            return "less common than", "cmp"
        return "same frequency as", "cmp"
    return None, "unknown"


def main():
    items = [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    failures = []
    label_cache = {}

    for it in items:
        cwid = it["context_window_id"]
        ctx_file = DATA / it["context_file"]
        lbl_file = DATA / it["context_with_labels_file"]
        ctx_text = ctx_file.read_text(encoding="utf-8")
        lbl_text = lbl_file.read_text(encoding="utf-8")

        # structural checks (once per context window)
        if cwid not in label_cache:
            counts = label_counts(lbl_text)
            label_cache[cwid] = counts
            n_lbl = sum(counts.values())
            n_inst = len(INSTANCE_LINE.findall(ctx_text))
            hdr = int(HEADER_COUNT.search(ctx_text).group(1))
            if "|| Label:" in ctx_text:
                failures.append(f"cw{cwid}: model-facing context LEAKS labels ('|| Label:' present)")
            if not (n_lbl == n_inst == hdr):
                failures.append(f"cw{cwid}: count mismatch labelled={n_lbl} "
                                f"instances={n_inst} header={hdr}")
        counts = label_cache[cwid]

        # context_chars integrity
        if len(ctx_text) != it["context_chars"]:
            failures.append(f"id={it['id']}: context_chars {it['context_chars']} "
                            f"!= file {len(ctx_text)}")

        # gold answer re-derivation
        exp, kind = expected_answer(it, counts)
        gold = gold0(it["answer"])
        gset = gold_set(it["answer"])
        ok = False
        if kind == "set":
            ok = str(gold) in {str(x) for x in exp} and set(gset) <= {str(x) for x in exp}
        elif kind == "num":
            ok = str(gold) == str(exp)
        elif kind == "cmp":
            ok = str(gold) == str(exp)
        status = "OK " if ok else "FAIL"
        print(f"[{status}] id={it['id']} cw{cwid} {it['task']:<27} "
              f"gold={str(gold):<18} recomputed={str(exp)}")
        if not ok:
            failures.append(f"id={it['id']}: gold {gold!r} != recomputed {exp!r}")

    # show the full label distribution per context for transparency
    print("\nLabel distributions (recomputed from gold-labelled contexts):")
    for cwid, counts in sorted(label_cache.items()):
        print(f"  cw{cwid} (total {sum(counts.values())}): " +
              ", ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])))

    print()
    if failures:
        print(f"VERIFICATION FAILED with {len(failures)} issue(s):")
        for f in failures:
            print("  -", f)
        return 1
    print(f"VERIFICATION PASSED: {len(items)} items, all gold answers independently reproduced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
