#!/usr/bin/env python3
"""Merge per-annotator export files back into the shared human-eval sheet."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_SHEET_PATH = ROOT / "data" / "human_eval" / "human_eval_sheet.csv"
MERGED_OUTPUT_PATH = ROOT / "data" / "human_eval" / "human_eval_sheet_merged.csv"
EXPORT_DIR = ROOT / "data" / "human_eval" / "annotator_exports"
ANNOTATOR_EXPORTS = [
    EXPORT_DIR / "minseo_annotations.csv",
    EXPORT_DIR / "siwan_annotations.csv",
]
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-place", action="store_true", help="Overwrite human_eval_sheet.csv")
    args = parser.parse_args()

    base_rows = read_csv_rows(BASE_SHEET_PATH)
    fieldnames = list(base_rows[0].keys())
    base_by_id = {row["id"]: dict(row) for row in base_rows}

    merged_count = 0
    for export_path in ANNOTATOR_EXPORTS:
        if not export_path.exists():
            continue
        for row in read_csv_rows(export_path):
            if row["id"] not in base_by_id:
                continue
            for field in EDITABLE_FIELDS:
                if row.get(field, "").strip():
                    base_by_id[row["id"]][field] = row[field]
            merged_count += 1

    ordered_rows = [base_by_id[row["id"]] for row in base_rows]
    output_path = BASE_SHEET_PATH if args.in_place else MERGED_OUTPUT_PATH
    write_csv_rows(output_path, fieldnames, ordered_rows)

    print(f"Merged rows from annotator exports: {merged_count}")
    print(f"Saved {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
