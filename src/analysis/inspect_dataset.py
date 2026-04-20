#!/usr/bin/env python3
"""Inspect the Korean validation dataset and verify prediction alignment."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "validation_ko_merged.jsonl"
RAW_VALIDATION_PATH = ROOT / "data" / "raw" / "validation" / "ko_KR.jsonl"
RAW_GPT4O_PATH = (
    ROOT / "data" / "raw" / "predictions" / "gpt-4o-2024-08-06" / "validation" / "ko_KR.jsonl"
)
RAW_GPT4O_MINI_PATH = (
    ROOT
    / "data"
    / "raw"
    / "predictions"
    / "gpt-4o-mini-2024-07-18"
    / "validation"
    / "ko_KR.jsonl"
)
OUTPUT_DIR = ROOT / "outputs" / "metrics"
SUMMARY_JSON_PATH = OUTPUT_DIR / "validation_ko_inspection_summary.json"
SUMMARY_CSV_PATH = OUTPUT_DIR / "validation_ko_inspection_summary.csv"
ENTITY_COUNTS_CSV_PATH = OUTPUT_DIR / "validation_ko_entity_type_counts.csv"
EXAMPLES_JSONL_PATH = OUTPUT_DIR / "validation_ko_inspection_examples.jsonl"
EXAMPLE_COUNT = 5


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_summary_csv(path: Path, summary_rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(summary_rows)


def write_entity_counts(path: Path, counter: Counter[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["entity_type", "count"])
        writer.writeheader()
        for entity_type, count in counter.most_common():
            writer.writerow({"entity_type": entity_type, "count": count})


def write_examples(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def summarize_predictions(records: list[dict[str, Any]], field_name: str) -> dict[str, Any]:
    missing_ids = [record["id"] for record in records if not record.get(field_name)]
    return {
        "missing_count": len(missing_ids),
        "missing_ids": missing_ids[:20],
    }


def build_alignment_report(
    merged_records: list[dict[str, Any]],
    validation_records: list[dict[str, Any]],
    gpt4o_records: list[dict[str, Any]],
    gpt4o_mini_records: list[dict[str, Any]],
) -> dict[str, Any]:
    merged_ids = {record["id"] for record in merged_records}
    validation_ids = {record["id"] for record in validation_records}
    gpt4o_map = {record["id"]: record.get("prediction", "") for record in gpt4o_records}
    gpt4o_mini_map = {record["id"]: record.get("prediction", "") for record in gpt4o_mini_records}
    gpt4o_ids = set(gpt4o_map)
    gpt4o_mini_ids = set(gpt4o_mini_map)

    merged_gpt4o_mismatches: list[str] = []
    merged_gpt4o_mini_mismatches: list[str] = []
    for record in merged_records:
        record_id = record["id"]
        if record.get("gpt4o_prediction", "") != gpt4o_map.get(record_id, ""):
            merged_gpt4o_mismatches.append(record_id)
        if record.get("gpt4o_mini_prediction", "") != gpt4o_mini_map.get(record_id, ""):
            merged_gpt4o_mini_mismatches.append(record_id)

    return {
        "validation_vs_merged_ids_match": validation_ids == merged_ids,
        "validation_vs_gpt4o_ids_match": validation_ids == gpt4o_ids,
        "validation_vs_gpt4o_mini_ids_match": validation_ids == gpt4o_mini_ids,
        "validation_only_ids": sorted(validation_ids - merged_ids)[:20],
        "merged_only_ids": sorted(merged_ids - validation_ids)[:20],
        "gpt4o_missing_from_validation": sorted(validation_ids - gpt4o_ids)[:20],
        "gpt4o_extra_vs_validation": sorted(gpt4o_ids - validation_ids)[:20],
        "gpt4o_mini_missing_from_validation": sorted(validation_ids - gpt4o_mini_ids)[:20],
        "gpt4o_mini_extra_vs_validation": sorted(gpt4o_mini_ids - validation_ids)[:20],
        "merged_gpt4o_value_mismatch_count": len(merged_gpt4o_mismatches),
        "merged_gpt4o_value_mismatch_ids": merged_gpt4o_mismatches[:20],
        "merged_gpt4o_mini_value_mismatch_count": len(merged_gpt4o_mini_mismatches),
        "merged_gpt4o_mini_value_mismatch_ids": merged_gpt4o_mini_mismatches[:20],
    }


def select_example_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    def add_example(example_type: str, record: dict[str, Any], include_reference_lists: bool = False) -> None:
        if record["id"] in used_ids or len(examples) >= EXAMPLE_COUNT:
            return

        example = {
            "example_type": example_type,
            "id": record["id"],
            "source": record["source"],
            "reference_translation": record.get("reference_translation"),
            "reference_mention": record.get("reference_mention"),
            "gpt4o_prediction": record.get("gpt4o_prediction", ""),
            "gpt4o_mini_prediction": record.get("gpt4o_mini_prediction", ""),
            "entity_types": record.get("entity_types", []),
            "reference_count": len(record.get("reference_translations", [])),
        }
        if include_reference_lists:
            example["reference_translations"] = record.get("reference_translations", [])
            example["reference_mentions"] = record.get("reference_mentions", [])

        examples.append(example)
        used_ids.add(record["id"])

    first_record = records[0]
    add_example("first_record", first_record)

    multi_reference = next(
        (
            record
            for record in records
            if record["id"] not in used_ids and len(record.get("reference_translations", [])) > 1
        ),
        None,
    )
    if multi_reference is not None:
        add_example("multi_reference", multi_reference, include_reference_lists=True)

    model_disagreement = next(
        (
            record
            for record in records
            if record["id"] not in used_ids
            if record.get("gpt4o_prediction", "") != record.get("gpt4o_mini_prediction", "")
        ),
        None,
    )
    if model_disagreement is not None:
        add_example("model_disagreement", model_disagreement)

    missing_mention = next(
        (
            record
            for record in records
            if record["id"] not in used_ids and not record.get("reference_mention")
        ),
        None,
    )
    if missing_mention is not None:
        add_example("missing_reference_mention", missing_mention)

    for record in records:
        if len(examples) >= EXAMPLE_COUNT:
            break
        add_example(f"preview_{len(examples)}", record)

    return examples[:EXAMPLE_COUNT]


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def main() -> None:
    merged_records = load_jsonl(INPUT_PATH)
    validation_records = load_jsonl(RAW_VALIDATION_PATH)
    gpt4o_records = load_jsonl(RAW_GPT4O_PATH)
    gpt4o_mini_records = load_jsonl(RAW_GPT4O_MINI_PATH)

    if not merged_records:
        raise ValueError(f"No records found in {INPUT_PATH}")

    columns = sorted(merged_records[0].keys())
    primary_entity_counter = Counter()
    all_entity_counter = Counter()
    multi_reference_count = 0
    missing_reference_mention_count = 0
    missing_any_reference_mention_count = 0

    for record in merged_records:
        entity_types = record.get("entity_types") or []
        if entity_types:
            primary_entity_counter[entity_types[0]] += 1
            all_entity_counter.update(entity_types)
        else:
            primary_entity_counter["Unknown"] += 1
            all_entity_counter["Unknown"] += 1

        reference_translations = record.get("reference_translations") or []
        reference_mentions = record.get("reference_mentions") or []
        if len(reference_translations) > 1:
            multi_reference_count += 1
        if not record.get("reference_mention"):
            missing_reference_mention_count += 1
        if not reference_mentions or any(not mention for mention in reference_mentions):
            missing_any_reference_mention_count += 1

    alignment_report = build_alignment_report(
        merged_records=merged_records,
        validation_records=validation_records,
        gpt4o_records=gpt4o_records,
        gpt4o_mini_records=gpt4o_mini_records,
    )
    gpt4o_summary = summarize_predictions(merged_records, "gpt4o_prediction")
    gpt4o_mini_summary = summarize_predictions(merged_records, "gpt4o_mini_prediction")

    examples = select_example_records(merged_records)

    summary = {
        "input_path": str(INPUT_PATH.relative_to(ROOT)),
        "record_count": len(merged_records),
        "columns": columns,
        "column_count": len(columns),
        "unique_primary_entity_types": len(primary_entity_counter),
        "unique_all_entity_types": len(all_entity_counter),
        "top_primary_entity_types": primary_entity_counter.most_common(15),
        "top_all_entity_types": all_entity_counter.most_common(15),
        "multi_reference_count": multi_reference_count,
        "multi_reference_rate": round(multi_reference_count / len(merged_records), 4),
        "missing_reference_mention_count": missing_reference_mention_count,
        "missing_reference_mention_rate": round(
            missing_reference_mention_count / len(merged_records), 4
        ),
        "missing_any_reference_mention_count": missing_any_reference_mention_count,
        "missing_any_reference_mention_rate": round(
            missing_any_reference_mention_count / len(merged_records), 4
        ),
        "gpt4o_prediction_summary": gpt4o_summary,
        "gpt4o_mini_prediction_summary": gpt4o_mini_summary,
        "alignment_report": alignment_report,
        "example_preview_count": len(examples),
    }

    summary_rows = [
        {"metric": "record_count", "value": str(summary["record_count"])},
        {"metric": "column_count", "value": str(summary["column_count"])},
        {
            "metric": "unique_primary_entity_types",
            "value": str(summary["unique_primary_entity_types"]),
        },
        {"metric": "unique_all_entity_types", "value": str(summary["unique_all_entity_types"])},
        {"metric": "multi_reference_count", "value": str(summary["multi_reference_count"])},
        {"metric": "multi_reference_rate", "value": str(summary["multi_reference_rate"])},
        {
            "metric": "missing_reference_mention_count",
            "value": str(summary["missing_reference_mention_count"]),
        },
        {
            "metric": "missing_any_reference_mention_count",
            "value": str(summary["missing_any_reference_mention_count"]),
        },
        {
            "metric": "gpt4o_missing_prediction_count",
            "value": str(gpt4o_summary["missing_count"]),
        },
        {
            "metric": "gpt4o_mini_missing_prediction_count",
            "value": str(gpt4o_mini_summary["missing_count"]),
        },
        {
            "metric": "validation_vs_merged_ids_match",
            "value": str(alignment_report["validation_vs_merged_ids_match"]),
        },
        {
            "metric": "validation_vs_gpt4o_ids_match",
            "value": str(alignment_report["validation_vs_gpt4o_ids_match"]),
        },
        {
            "metric": "validation_vs_gpt4o_mini_ids_match",
            "value": str(alignment_report["validation_vs_gpt4o_mini_ids_match"]),
        },
        {
            "metric": "merged_gpt4o_value_mismatch_count",
            "value": str(alignment_report["merged_gpt4o_value_mismatch_count"]),
        },
        {
            "metric": "merged_gpt4o_mini_value_mismatch_count",
            "value": str(alignment_report["merged_gpt4o_mini_value_mismatch_count"]),
        },
    ]

    write_json(SUMMARY_JSON_PATH, summary)
    write_summary_csv(SUMMARY_CSV_PATH, summary_rows)
    write_entity_counts(ENTITY_COUNTS_CSV_PATH, primary_entity_counter)
    write_examples(EXAMPLES_JSONL_PATH, examples)

    print_section("Dataset Inspection")
    print(f"Input file: {summary['input_path']}")
    print(f"Rows: {summary['record_count']}")
    print(f"Columns ({summary['column_count']}): {', '.join(columns)}")

    print_section("Reference Coverage")
    print(
        f"Rows with multiple references: {multi_reference_count} "
        f"({summary['multi_reference_rate']:.2%})"
    )
    print(
        f"Rows missing primary reference mention: {missing_reference_mention_count} "
        f"({summary['missing_reference_mention_rate']:.2%})"
    )
    print(
        f"Rows with any missing reference mention: {missing_any_reference_mention_count} "
        f"({summary['missing_any_reference_mention_rate']:.2%})"
    )

    print_section("Prediction Alignment")
    print(f"Validation IDs match merged IDs: {alignment_report['validation_vs_merged_ids_match']}")
    print(f"Validation IDs match gpt4o IDs: {alignment_report['validation_vs_gpt4o_ids_match']}")
    print(
        "Validation IDs match gpt4o-mini IDs: "
        f"{alignment_report['validation_vs_gpt4o_mini_ids_match']}"
    )
    print(f"Merged gpt4o missing predictions: {gpt4o_summary['missing_count']}")
    print(f"Merged gpt4o-mini missing predictions: {gpt4o_mini_summary['missing_count']}")
    print(
        "Merged gpt4o value mismatches vs raw predictions: "
        f"{alignment_report['merged_gpt4o_value_mismatch_count']}"
    )
    print(
        "Merged gpt4o-mini value mismatches vs raw predictions: "
        f"{alignment_report['merged_gpt4o_mini_value_mismatch_count']}"
    )

    print_section("Top Entity Types")
    for entity_type, count in primary_entity_counter.most_common(10):
        print(f"{entity_type}: {count}")

    print_section("Example Rows")
    for example in examples:
        print(f"[{example['example_type']}] {example['id']}")
        print(f"source: {example['source']}")
        print(f"reference: {example.get('reference_translation')}")
        print(f"mention: {example.get('reference_mention')}")
        print(f"gpt4o: {example.get('gpt4o_prediction')}")
        print(f"gpt4o-mini: {example.get('gpt4o_mini_prediction')}")
        print(f"entity_types: {example.get('entity_types')}")
        print(f"reference_count: {example.get('reference_count')}")
        print()

    print_section("Saved Artifacts")
    print(SUMMARY_JSON_PATH.relative_to(ROOT))
    print(SUMMARY_CSV_PATH.relative_to(ROOT))
    print(ENTITY_COUNTS_CSV_PATH.relative_to(ROOT))
    print(EXAMPLES_JSONL_PATH.relative_to(ROOT))


if __name__ == "__main__":
    main()
