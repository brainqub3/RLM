#!/usr/bin/env python3
"""Fetch trec_coarse @131072 rows by reading the HF parquet directly (reliable path).

Uses pyarrow dataset scanning with predicate pushdown over the auto-converted
parquet on the HF CDN, so only the row groups whose statistics overlap the
filter (dataset == 'trec_coarse' AND context_len == 131072) are downloaded.
Streams row-group batches and stops once enough matching rows are collected.
Writes full, untruncated rows to raw_131072.jsonl (the format build_eval.py reads).
"""
import json, time, sys
from pathlib import Path

import pyarrow.dataset as ds
import pyarrow.compute as pc
from huggingface_hub import HfFileSystem

TARGET_LEN = 131072
WANT = 50  # grab the whole 131072 block; build_eval selects 10 from it
OUT = Path(__file__).resolve().parent / "raw_131072.jsonl"
COLS = ["id", "context_len", "dataset", "context_window_text",
        "context_window_text_with_labels", "question", "task_group", "task",
        "answer", "answer_type", "input_subset", "num_labels", "context_window_id"]

VAL_SHARDS = [
    "datasets/oolongbench/oolong-synth@refs/convert/parquet/default/partial-validation/0000.parquet",
    "datasets/oolongbench/oolong-synth@refs/convert/parquet/default/partial-validation/0001.parquet",
]


def main():
    fs = HfFileSystem()
    filt = (pc.field("dataset") == "trec_coarse") & (pc.field("context_len") == TARGET_LEN)
    collected = []
    t0 = time.time()
    for shard in VAL_SHARDS:
        if len(collected) >= WANT:
            break
        print(f"scanning {shard.split('/')[-2]}/{shard.split('/')[-1]} ...", flush=True)
        dataset = ds.dataset(shard, filesystem=fs, format="parquet")
        scanner = dataset.scanner(columns=COLS, filter=filt, batch_size=8)
        for batch in scanner.to_batches():
            if batch.num_rows == 0:
                continue
            for rec in batch.to_pylist():
                rec["__truncated"] = []
                collected.append(rec)
            print(f"  +{batch.num_rows} (total {len(collected)})  t={time.time()-t0:.0f}s", flush=True)
            if len(collected) >= WANT:
                break
    with OUT.open("w", encoding="utf-8") as f:
        for rec in collected:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    # sanity summary
    from collections import Counter
    print(f"\nWROTE {len(collected)} rows to {OUT.name} in {time.time()-t0:.0f}s")
    print("ctx_len set:", sorted({r['context_len'] for r in collected}))
    print("task mix:", dict(Counter(r['task'] for r in collected)))
    print("group mix:", dict(Counter(r['task_group'] for r in collected)))
    if collected:
        c = collected[0]
        print("sample chars (text/with_labels):",
              len(c['context_window_text']), "/", len(c['context_window_text_with_labels']))


if __name__ == "__main__":
    sys.exit(main())
