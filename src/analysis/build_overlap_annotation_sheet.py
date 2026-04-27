#!/usr/bin/env python3
"""Build a fresh overlap sheet so both annotators can label the same examples."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_subset import compute_selection_metadata


ROOT = Path(__file__).resolve().parents[2]
VALIDATION_PATH = ROOT / "data" / "processed" / "validation_ko_merged.jsonl"
MAIN_SHEET_PATH = ROOT / "data" / "human_eval" / "human_eval_sheet.csv"
ANNOTATOR_EXPORT_DIR = ROOT / "data" / "human_eval" / "annotator_exports"
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
OUTPUT_FIELDNAMES = [
    "id",
    "split",
    "primary_entity_type",
    "entity_types",
    "wikidata_id",
    "source",
    "reference_translation",
    "reference_translations",
    "reference_mention",
    "reference_mentions",
    "gpt4o_prediction",
    "gpt4o_mini_prediction",
    "selection_score",
    "selection_reasons",
    *EDITABLE_FIELDS,
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def load_previously_annotated_ids() -> set[str]:
    annotated_ids = {row["id"] for row in read_csv(MAIN_SHEET_PATH)}
    for path in sorted(ANNOTATOR_EXPORT_DIR.glob("*_annotations.csv")):
        annotated_ids.update(row["id"] for row in read_csv(path))
    return annotated_ids


def select_overlap_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(RANDOM_SEED)
    enriched_rows = [compute_selection_metadata(row, rng) for row in rows]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in enriched_rows:
        grouped[row["primary_entity_type"]].append(row)

    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    for entity_type in sorted(grouped):
        bucket = list(grouped[entity_type])
        bucket.sort(
            key=lambda row: (
                -row["selection_score"],
                row["_random_tiebreaker"],
                row["id"],
            )
        )
        row = bucket[0]
        selected.append(row)
        used_ids.add(row["id"])

    remaining = [row for row in enriched_rows if row["id"] not in used_ids]
    remaining.sort(
        key=lambda row: (
            -row["selection_score"],
            row["_random_tiebreaker"],
            row["id"],
        )
    )
    selected.extend(remaining[: max(0, OVERLAP_SIZE - len(selected))])
    return sorted(selected[:OVERLAP_SIZE], key=lambda row: row["id"])


def build_annotation_row(record: dict[str, Any]) -> dict[str, str]:
    row = {
        "id": stringify(record.get("id")),
        "split": stringify(record.get("split")),
        "primary_entity_type": stringify(record.get("primary_entity_type")),
        "entity_types": stringify(record.get("entity_types")),
        "wikidata_id": stringify(record.get("wikidata_id")),
        "source": stringify(record.get("source")),
        "reference_translation": stringify(record.get("reference_translation")),
        "reference_translations": stringify(record.get("reference_translations")),
        "reference_mention": stringify(record.get("reference_mention")),
        "reference_mentions": stringify(record.get("reference_mentions")),
        "gpt4o_prediction": stringify(record.get("gpt4o_prediction")),
        "gpt4o_mini_prediction": stringify(record.get("gpt4o_mini_prediction")),
        "selection_score": stringify(record.get("selection_score")),
        "selection_reasons": stringify(record.get("selection_reasons")),
    }
    for field in EDITABLE_FIELDS:
        row[field] = ""
    return row


def main() -> None:
    previously_annotated_ids = load_previously_annotated_ids()
    validation_rows = [
        row for row in load_jsonl(VALIDATION_PATH) if row["id"] not in previously_annotated_ids
    ]
    if len(validation_rows) < OVERLAP_SIZE:
        raise SystemExit(
            f"Need at least {OVERLAP_SIZE} unused rows, found {len(validation_rows)}"
        )

    selected_records = select_overlap_rows(validation_rows)
    selected = [build_annotation_row(record) for record in selected_records]
    write_csv(OUTPUT_SHEET_PATH, selected, OUTPUT_FIELDNAMES)

    summary = {
        "source_data": str(VALIDATION_PATH.relative_to(ROOT)),
        "excluded_main_sheet": str(MAIN_SHEET_PATH.relative_to(ROOT)),
        "output_sheet": str(OUTPUT_SHEET_PATH.relative_to(ROOT)),
        "overlap_size": len(selected),
        "available_unused_validation_examples": len(validation_rows),
        "excluded_previously_annotated_examples": len(previously_annotated_ids),
        "random_seed": RANDOM_SEED,
        "note": (
            "Both annotators should annotate every row in this overlap sheet. "
            "Rows are selected from validation examples outside the original human-eval sheet."
        ),
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
