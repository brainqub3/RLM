#!/usr/bin/env python3
"""Build the RLM eval subset from the cached trec_coarse @131072 rows.

Reads _cache/raw_131072.jsonl and selects a balanced subset of N=10 'counting'-group
tasks. The 'counting' group holds the canonical OOLONG aggregations whose answer is a
deterministic function of ALL items in the context (so we can independently verify them):

  * MOST_FREQ / LEAST_FREQ   -> most / least common semantic label   (LABEL)
  * RELATIVE_FREQ            -> is label A more/less common than B?   (COMPARISON)
  * NUMERIC_ONE_CLASS        -> how many items are label X?           (NUMERIC)

Selection goals (deterministic, sorted by id for reproducibility):
  - both available long contexts (context_window_id) are represented;
  - comparison items maximise gold-answer diversity (>=1 each of more/less/same if present);
  - numeric items have distinct gold values;
  - composition ~ {1 MOST, 1 LEAST, 4 RELATIVE, 4 NUMERIC}.

Emits:
  data/oolong_trec_coarse.jsonl                       -- manifest (one JSON line per item)
  data/contexts/trec_coarse_cw<cwid>.txt              -- FULL model-facing context (no labels)
  data/contexts_with_labels/trec_coarse_cw<cwid>.txt  -- same context WITH gold labels (verify only)

Contexts are de-duplicated by context window and never trimmed.
"""
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1]   # .../rlm/eval
RAW = EVAL_DIR / "_cache" / "raw_131072.jsonl"
DATA = EVAL_DIR / "data"
CTX = DATA / "contexts"
CTX_LBL = DATA / "contexts_with_labels"
MANIFEST = DATA / "oolong_trec_coarse.jsonl"
TARGET_LEN = 131072


def gold0(answer_field: str):
    try:
        return ast.literal_eval(answer_field)[0]
    except Exception:
        return answer_field


def load_rows():
    rows = [json.loads(l) for l in RAW.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [r for r in rows
            if r["context_len"] == TARGET_LEN
            and not r.get("__truncated")
            and r["dataset"] == "trec_coarse"
            and r["task_group"] == "counting"]


def pick_comparisons(rows, k=4):
    """Pick k RELATIVE_FREQ rows maximising gold-answer diversity and cwid spread."""
    comps = sorted([r for r in rows if r["task"] == "TASK_TYPE.RELATIVE_FREQ"],
                   key=lambda r: r["id"])
    by_ans = defaultdict(list)
    for r in comps:
        by_ans[gold0(r["answer"])].append(r)
    chosen, used = [], set()
    # round-robin over distinct answer values to guarantee diversity
    while len(chosen) < k and any(by_ans[a] for a in by_ans):
        for a in list(by_ans.keys()):
            if by_ans[a] and len(chosen) < k:
                r = by_ans[a].pop(0)
                chosen.append(r); used.add(r["id"])
    return chosen


def pick_numerics(rows, k=4):
    """Pick k NUMERIC_ONE_CLASS rows with distinct gold values, balanced across cwids."""
    nums = sorted([r for r in rows if r["task"] == "TASK_TYPE.NUMERIC_ONE_CLASS"],
                  key=lambda r: r["id"])
    by_cwid = defaultdict(list)
    for r in nums:
        by_cwid[r["context_window_id"]].append(r)
    chosen, seen_vals = [], set()
    cwids = sorted(by_cwid)
    i = 0
    while len(chosen) < k and any(by_cwid[c] for c in cwids):
        c = cwids[i % len(cwids)]
        i += 1
        while by_cwid[c]:
            r = by_cwid[c].pop(0)
            v = gold0(r["answer"])
            if v not in seen_vals:
                chosen.append(r); seen_vals.add(v)
                break
    return chosen


def pick_labels(rows):
    """1 MOST_FREQ and 1 LEAST_FREQ, preferring different context windows."""
    most = sorted([r for r in rows if r["task"] == "TASK_TYPE.MOST_FREQ"], key=lambda r: r["id"])
    least = sorted([r for r in rows if r["task"] == "TASK_TYPE.LEAST_FREQ"], key=lambda r: r["id"])
    chosen = []
    if most:
        chosen.append(most[0])
    # pick a LEAST from a different cwid than the MOST, if possible
    if least:
        if chosen:
            alt = [r for r in least if r["context_window_id"] != chosen[0]["context_window_id"]]
            chosen.append(alt[0] if alt else least[0])
        else:
            chosen.append(least[0])
    return chosen


def select(rows):
    chosen, used = [], set()
    for r in pick_labels(rows) + pick_comparisons(rows, 4) + pick_numerics(rows, 4):
        if r["id"] not in used:
            chosen.append(r); used.add(r["id"])
    # top up to 10 if any picker came up short
    if len(chosen) < 10:
        for r in sorted(rows, key=lambda r: r["id"]):
            if r["id"] not in used:
                chosen.append(r); used.add(r["id"])
                if len(chosen) == 10:
                    break
    return sorted(chosen[:10], key=lambda r: (r["task"], r["id"]))


def main():
    rows = load_rows()
    chosen = select(rows)
    CTX.mkdir(parents=True, exist_ok=True)
    CTX_LBL.mkdir(parents=True, exist_ok=True)

    # de-duplicate context storage by context window id
    written = set()
    manifest = []
    for r in chosen:
        cwid = r["context_window_id"]
        name = f"trec_coarse_cw{cwid}.txt"
        if cwid not in written:
            # write exact bytes (newline='\n' preserved; no CRLF translation on Windows)
            (CTX / name).write_bytes(r["context_window_text"].encode("utf-8"))
            (CTX_LBL / name).write_bytes(r["context_window_text_with_labels"].encode("utf-8"))
            written.add(cwid)
        manifest.append({
            "id": r["id"],
            "dataset": r["dataset"],
            "context_window_id": cwid,
            "context_len_tokens": r["context_len"],
            "context_chars": len(r["context_window_text"]),
            "num_labels": r["num_labels"],
            "task": r["task"],
            "task_group": r["task_group"],
            "answer_type": r["answer_type"],
            "question": r["question"],
            "answer": r["answer"],
            "context_file": f"contexts/{name}",
            "context_with_labels_file": f"contexts_with_labels/{name}",
            "source": "oolongbench/oolong-synth (split=validation, dataset=trec_coarse)",
        })

    manifest.sort(key=lambda m: (m["task"], m["id"]))
    with MANIFEST.open("w", encoding="utf-8") as f:
        for m in manifest:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    # summary
    print(f"selected {len(manifest)} items over {len(written)} context windows {sorted(written)}")
    print("task mix:", dict(Counter(m["task"] for m in manifest)))
    print("answer_type mix:", dict(Counter(m["answer_type"] for m in manifest)))
    print("comparison golds:", dict(Counter(gold0(m["answer"]) for m in manifest
                                             if m["answer_type"] == "ANSWER_TYPE.COMPARISON")))
    uniq = sum(len((CTX / f"trec_coarse_cw{c}.txt").read_text(encoding='utf-8')) for c in written)
    print(f"unique context bytes on disk (no-labels): {uniq:,}")
    for m in manifest:
        print(f"  id={m['id']} cw{m['context_window_id']} {m['task']:<27} "
              f"gold={str(gold0(m['answer'])):<18} chars={m['context_chars']:,}")


if __name__ == "__main__":
    main()
