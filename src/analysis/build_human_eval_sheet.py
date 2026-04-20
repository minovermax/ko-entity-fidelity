#!/usr/bin/env python3
"""Build the human evaluation sheet from the formal Korean analysis subset."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "ko_analysis_subset.jsonl"
OUTPUT_DIR = ROOT / "data" / "human_eval"
HUMAN_EVAL_SHEET_PATH = OUTPUT_DIR / "human_eval_sheet.csv"
ANNOTATION_TEMPLATE_PATH = OUTPUT_DIR / "annotation_template.csv"
KO_TEMPLATE_PATH = OUTPUT_DIR / "ko_annotation_template.csv"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: stringify(value) for key, value in row.items()})


def build_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.append(
            {
                "id": record["id"],
                "split": record["split"],
                "primary_entity_type": record.get("primary_entity_type", ""),
                "entity_types": record.get("entity_types", []),
                "wikidata_id": record["wikidata_id"],
                "source": record["source"],
                "reference_translation": record["reference_translation"],
                "reference_translations": record.get("reference_translations", []),
                "reference_mention": record["reference_mention"],
                "reference_mentions": record.get("reference_mentions", []),
                "gpt4o_prediction": record.get("gpt4o_prediction", ""),
                "gpt4o_mini_prediction": record.get("gpt4o_mini_prediction", ""),
                "selection_score": record.get("selection_score", ""),
                "selection_reasons": record.get("selection_reasons", []),
                "target_rendering_strategy": "",
                "official_korean_title_preferred": "",
                "preserve_english_preferred": "",
                "adaptation_needed": "",
                "gpt4o_entity_correct": "",
                "gpt4o_rendering_strategy": "",
                "gpt4o_quality_label": "",
                "gpt4o_metric_likely_miss": "",
                "gpt4o_notes": "",
                "gpt4o_mini_entity_correct": "",
                "gpt4o_mini_rendering_strategy": "",
                "gpt4o_mini_quality_label": "",
                "gpt4o_mini_metric_likely_miss": "",
                "gpt4o_mini_notes": "",
                "preferred_model": "",
                "overall_comments": "",
            }
        )
    return rows


def main() -> None:
    records = load_jsonl(INPUT_PATH)
    rows = build_rows(records)

    write_csv(HUMAN_EVAL_SHEET_PATH, rows)
    write_csv(ANNOTATION_TEMPLATE_PATH, rows)
    write_csv(KO_TEMPLATE_PATH, rows)

    print(f"Saved {HUMAN_EVAL_SHEET_PATH.relative_to(ROOT)}")
    print(f"Saved {ANNOTATION_TEMPLATE_PATH.relative_to(ROOT)}")
    print(f"Saved {KO_TEMPLATE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
