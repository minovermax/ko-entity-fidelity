#!/usr/bin/env python3
"""Build deterministic local dev/test splits from Korean validation references."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "validation_ko_with_baselines.jsonl"
FALLBACK_INPUT_PATH = ROOT / "data" / "processed" / "validation_ko_merged.jsonl"
PROCESSED_DIR = ROOT / "data" / "processed"
METRICS_DIR = ROOT / "outputs" / "metrics"

DEV_OUTPUT_PATH = PROCESSED_DIR / "local_dev_ko_with_baselines.jsonl"
TEST_OUTPUT_PATH = PROCESSED_DIR / "local_test_ko_with_baselines.jsonl"
SUMMARY_JSON_PATH = PROCESSED_DIR / "local_eval_split_summary.json"
COUNTS_CSV_PATH = METRICS_DIR / "local_eval_split_counts.csv"

TEST_SIZE = 150
RANDOM_SEED = 4650


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def primary_entity_type(record: dict[str, Any]) -> str:
    entity_types = record.get("entity_types") or []
    return str(entity_types[0]) if entity_types else "Unknown"


def allocate_test_counts(records: list[dict[str, Any]], test_size: int) -> dict[str, int]:
    counts = Counter(primary_entity_type(record) for record in records)
    quotas = {
        entity_type: (count * test_size) / len(records)
        for entity_type, count in counts.items()
    }
    allocations = {
        entity_type: min(math.floor(quota), max(counts[entity_type] - 1, 0))
        for entity_type, quota in quotas.items()
    }

    while sum(allocations.values()) < test_size:
        candidates = [
            entity_type
            for entity_type, count in counts.items()
            if allocations[entity_type] < max(count - 1, 0)
        ]
        if not candidates:
            break
        candidates.sort(
            key=lambda entity_type: (
                quotas[entity_type] - math.floor(quotas[entity_type]),
                counts[entity_type],
                entity_type,
            ),
            reverse=True,
        )
        allocations[candidates[0]] += 1

    while sum(allocations.values()) > test_size:
        candidates = [
            entity_type for entity_type, value in allocations.items() if value > 0
        ]
        candidates.sort(
            key=lambda entity_type: (
                quotas[entity_type] - math.floor(quotas[entity_type]),
                counts[entity_type],
                entity_type,
            )
        )
        allocations[candidates[0]] -= 1

    return allocations


def split_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(RANDOM_SEED)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[primary_entity_type(record)].append(record)

    test_counts = allocate_test_counts(records, TEST_SIZE)
    test_ids: set[str] = set()
    for entity_type, group_records in grouped.items():
        shuffled = sorted(group_records, key=lambda record: str(record["id"]))
        rng.shuffle(shuffled)
        test_ids.update(str(record["id"]) for record in shuffled[: test_counts[entity_type]])

    dev_records: list[dict[str, Any]] = []
    test_records: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda item: str(item["id"])):
        updated = dict(record)
        if str(record["id"]) in test_ids:
            updated["local_eval_split"] = "test"
            test_records.append(updated)
        else:
            updated["local_eval_split"] = "dev"
            dev_records.append(updated)

    return dev_records, test_records


def build_count_rows(dev_records: list[dict[str, Any]], test_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dev_counts = Counter(primary_entity_type(record) for record in dev_records)
    test_counts = Counter(primary_entity_type(record) for record in test_records)
    entity_types = sorted(set(dev_counts) | set(test_counts))
    rows: list[dict[str, Any]] = []
    for entity_type in entity_types:
        rows.append(
            {
                "primary_entity_type": entity_type,
                "dev_count": dev_counts[entity_type],
                "test_count": test_counts[entity_type],
                "total_count": dev_counts[entity_type] + test_counts[entity_type],
            }
        )
    return rows


def main() -> None:
    input_path = INPUT_PATH if INPUT_PATH.exists() else FALLBACK_INPUT_PATH
    records = load_jsonl(input_path)
    records_with_references = [
        record for record in records if record.get("reference_translations")
    ]
    if len(records_with_references) != len(records):
        raise SystemExit(
            "Local evaluation splits require reference translations for every row."
        )

    dev_records, test_records = split_records(records_with_references)
    write_jsonl(DEV_OUTPUT_PATH, dev_records)
    write_jsonl(TEST_OUTPUT_PATH, test_records)
    write_csv(COUNTS_CSV_PATH, build_count_rows(dev_records, test_records))

    summary = {
        "source_input": str(input_path.relative_to(ROOT)),
        "random_seed": RANDOM_SEED,
        "split_method": "stratified deterministic holdout by primary entity type",
        "official_hidden_test_note": (
            "data/processed/test_ko.jsonl has no targets and cannot be scored locally."
        ),
        "dev": {
            "record_count": len(dev_records),
            "output_jsonl": str(DEV_OUTPUT_PATH.relative_to(ROOT)),
        },
        "test": {
            "record_count": len(test_records),
            "output_jsonl": str(TEST_OUTPUT_PATH.relative_to(ROOT)),
        },
        "entity_type_count_csv": str(COUNTS_CSV_PATH.relative_to(ROOT)),
    }
    SUMMARY_JSON_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Saved {DEV_OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Saved {TEST_OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Saved {SUMMARY_JSON_PATH.relative_to(ROOT)}")
    print(f"Saved {COUNTS_CSV_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
