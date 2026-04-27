#!/usr/bin/env python3
"""Build a small overlap sheet so both annotators can label the same examples."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHEET_PATH = ROOT / "data" / "human_eval" / "human_eval_sheet.csv"
OUTPUT_DIR = ROOT / "data" / "human_eval" / "overlap"
OUTPUT_SHEET_PATH = OUTPUT_DIR / "overlap_annotation_sheet.csv"
SUMMARY_PATH = OUTPUT_DIR / "overlap_annotation_summary.json"

OVERLAP_SIZE = 30
RANDOM_SEED = 4651

EDITABLE_FIELDS = [
    "target_rendering_strategy",
    "official_korean_title_preferred",
    "preserve_english_preferred",
    "adaptation_needed",
    "gpt4o_entity_correct",
    "gpt4o_rendering_strategy",
    "gpt4o_quality_label",
    "gpt4o_metric_likely_miss",
    "gpt4o_notes",
    "gpt4o_mini_entity_correct",
    "gpt4o_mini_rendering_strategy",
    "gpt4o_mini_quality_label",
    "gpt4o_mini_metric_likely_miss",
    "gpt4o_mini_notes",
    "preferred_model",
    "overall_comments",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def select_overlap_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rng = random.Random(RANDOM_SEED)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["primary_entity_type"]].append(row)

    selected: list[dict[str, str]] = []
    used_ids: set[str] = set()

    for entity_type in sorted(grouped):
        bucket = list(grouped[entity_type])
        rng.shuffle(bucket)
        row = bucket[0]
        selected.append(row)
        used_ids.add(row["id"])

    remaining = [row for row in rows if row["id"] not in used_ids]
    rng.shuffle(remaining)
    selected.extend(remaining[: max(0, OVERLAP_SIZE - len(selected))])
    return sorted(selected[:OVERLAP_SIZE], key=lambda row: row["id"])


def clear_annotations(row: dict[str, str]) -> dict[str, str]:
    cleared = dict(row)
    for field in EDITABLE_FIELDS:
        cleared[field] = ""
    return cleared


def main() -> None:
    rows = read_csv(SOURCE_SHEET_PATH)
    if len(rows) < OVERLAP_SIZE:
        raise SystemExit(f"Need at least {OVERLAP_SIZE} rows, found {len(rows)}")

    selected = [clear_annotations(row) for row in select_overlap_rows(rows)]
    fieldnames = list(rows[0].keys())
    write_csv(OUTPUT_SHEET_PATH, selected, fieldnames)

    summary = {
        "source_sheet": str(SOURCE_SHEET_PATH.relative_to(ROOT)),
        "output_sheet": str(OUTPUT_SHEET_PATH.relative_to(ROOT)),
        "overlap_size": len(selected),
        "random_seed": RANDOM_SEED,
        "note": "Both annotators should annotate every row in this overlap sheet.",
        "run_app_command": (
            "ANNOTATION_BASE_SHEET=data/human_eval/overlap/overlap_annotation_sheet.csv "
            "ANNOTATION_EXPORT_DIR=data/human_eval/overlap/annotator_exports "
            "ANNOTATION_ASSIGNMENTS_PATH=annotation_app/data/overlap_annotator_assignments.json "
            "ANNOTATION_ASSIGNMENT_MODE=all ANNOTATION_PORT=8766 "
            "python3 annotation_app/server.py"
        ),
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Saved {OUTPUT_SHEET_PATH.relative_to(ROOT)}")
    print(f"Saved {SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
