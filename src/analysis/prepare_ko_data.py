#!/usr/bin/env python3
"""Prepare Korean-only SemEval analysis assets from the downloaded zip archives."""

from __future__ import annotations

import csv
import json
import random
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
HUMAN_EVAL_DIR = ROOT / "data" / "human_eval"
OUTPUTS_METRICS_DIR = ROOT / "outputs" / "metrics"

LOCALE = "ko"
LOCALE_FILE = "ko_KR.jsonl"
ANALYSIS_SUBSET_SIZE = 250
RANDOM_SEED = 42

ARCHIVE_PATTERNS = {
    "sample": "semeval.sample*.zip",
    "validation": "semeval.validation*.zip",
    "test": "semeval.test_hidden*.zip",
    "predictions": "semeval.predictions*.zip",
}

ARCHIVE_MEMBERS = {
    "sample": f"semeval/sample/{LOCALE_FILE}",
    "validation": f"validation/{LOCALE_FILE}",
    "test": f"test_without_targets/{LOCALE_FILE}",
}

MODEL_MEMBERS = {
    "gpt4o_prediction": f"predictions/gpt-4o-2024-08-06/validation/{LOCALE_FILE}",
    "gpt4o_mini_prediction": (
        f"predictions/gpt-4o-mini-2024-07-18/validation/{LOCALE_FILE}"
    ),
}

RAW_OUTPUTS = {
    "sample": RAW_DIR / "sample" / LOCALE_FILE,
    "validation": RAW_DIR / "validation" / LOCALE_FILE,
    "test": RAW_DIR / "test" / LOCALE_FILE,
    "gpt4o_prediction": (
        RAW_DIR / "predictions" / "gpt-4o-2024-08-06" / "validation" / LOCALE_FILE
    ),
    "gpt4o_mini_prediction": (
        RAW_DIR
        / "predictions"
        / "gpt-4o-mini-2024-07-18"
        / "validation"
        / LOCALE_FILE
    ),
}


def find_archive(pattern: str) -> Path:
    matches = sorted(ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No archive found for pattern: {pattern}")
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise RuntimeError(f"Expected one archive for {pattern}, found: {names}")
    return matches[0]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_jsonl_from_zip(archive_path: Path, member_name: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive_path) as archive:
        with archive.open(member_name) as fh:
            for raw_line in fh:
                line = raw_line.decode("utf-8").strip()
                if line:
                    records.append(json.loads(line))
    return records


def extract_member_to_path(archive_path: Path, member_name: str, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    with zipfile.ZipFile(archive_path) as archive:
        data = archive.read(member_name)
    output_path.write_bytes(data)


def flatten_record(record: dict[str, Any], split: str) -> dict[str, Any]:
    targets = record.get("targets") or []
    translations = [
        target.get("translation")
        for target in targets
        if isinstance(target, dict) and target.get("translation")
    ]
    mentions = [
        target.get("mention")
        for target in targets
        if isinstance(target, dict) and target.get("mention")
    ]
    first_target = targets[0] if targets else {}

    return {
        "id": record.get("id"),
        "split": split,
        "source": record.get("source"),
        "source_locale": record.get("source_locale"),
        "target_locale": record.get("target_locale"),
        "wikidata_id": record.get("wikidata_id"),
        "entity_types": record.get("entity_types") or [],
        "targets": targets,
        "reference_translation": first_target.get("translation"),
        "reference_mention": first_target.get("mention"),
        "reference_translations": translations,
        "reference_mentions": mentions,
    }


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    ensure_dir(output_path.parent)
    with output_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def stringify_for_csv(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_csv(records: list[dict[str, Any]], output_path: Path) -> None:
    ensure_dir(output_path.parent)
    if not records:
        raise ValueError(f"No records to write for {output_path}")

    fieldnames = list(records[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({key: stringify_for_csv(value) for key, value in record.items()})


def load_prediction_map(
    archive_path: Path, member_name: str, output_path: Path
) -> dict[str, str]:
    extract_member_to_path(archive_path, member_name, output_path)
    records = load_jsonl_from_zip(archive_path, member_name)
    prediction_map: dict[str, str] = {}
    for record in records:
        prediction_map[record["id"]] = record.get("prediction", "")
    return prediction_map


def build_merged_validation(
    validation_records: list[dict[str, Any]],
    gpt4o_predictions: dict[str, str],
    gpt4o_mini_predictions: dict[str, str],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for record in validation_records:
        merged_record = dict(record)
        merged_record["gpt4o_prediction"] = gpt4o_predictions.get(record["id"], "")
        merged_record["gpt4o_mini_prediction"] = gpt4o_mini_predictions.get(record["id"], "")
        merged.append(merged_record)
    return merged


def build_combined_table(
    sample_records: list[dict[str, Any]], validation_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    combined: list[dict[str, Any]] = []
    for record in sample_records:
        combined_record = dict(record)
        combined_record["gpt4o_prediction"] = ""
        combined_record["gpt4o_mini_prediction"] = ""
        combined.append(combined_record)
    combined.extend(validation_records)
    return combined


def pick_analysis_subset(records: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    rng = random.Random(RANDOM_SEED)
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        entity_types = record.get("entity_types") or []
        primary_type = entity_types[0] if entity_types else "Unknown"
        buckets[primary_type].append(record)

    for bucket in buckets.values():
        rng.shuffle(bucket)

    ordered_types = sorted(buckets)
    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()

    if sample_size >= len(ordered_types):
        for entity_type in ordered_types:
            if buckets[entity_type]:
                record = buckets[entity_type].pop()
                selected.append(record)
                used_ids.add(record["id"])

    while len(selected) < min(sample_size, len(records)):
        added_in_round = False
        for entity_type in ordered_types:
            while buckets[entity_type]:
                record = buckets[entity_type].pop()
                if record["id"] in used_ids:
                    continue
                selected.append(record)
                used_ids.add(record["id"])
                added_in_round = True
                break
            if len(selected) >= sample_size:
                break
        if not added_in_round:
            break

    return selected


def build_annotation_template(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    template_rows: list[dict[str, Any]] = []
    for record in records:
        template_rows.append(
            {
                "id": record["id"],
                "split": record["split"],
                "source": record["source"],
                "reference_translation": record["reference_translation"],
                "reference_mention": record["reference_mention"],
                "gpt4o_prediction": record.get("gpt4o_prediction", ""),
                "gpt4o_mini_prediction": record.get("gpt4o_mini_prediction", ""),
                "wikidata_id": record["wikidata_id"],
                "entity_types": record["entity_types"],
                "should_translate": "",
                "should_transliterate": "",
                "should_preserve": "",
                "requires_cultural_adaptation": "",
                "automatic_metric_says_ok": "",
                "human_says_ok": "",
                "notes": "",
            }
        )
    return template_rows


def main() -> None:
    ensure_dir(RAW_DIR)
    ensure_dir(PROCESSED_DIR)
    ensure_dir(HUMAN_EVAL_DIR)
    ensure_dir(OUTPUTS_METRICS_DIR)

    archive_paths = {name: find_archive(pattern) for name, pattern in ARCHIVE_PATTERNS.items()}

    flattened_splits: dict[str, list[dict[str, Any]]] = {}
    summary: dict[str, Any] = {
        "locale": LOCALE,
        "raw_archives": {name: str(path.name) for name, path in archive_paths.items()},
        "splits": {},
    }

    for split, member_name in ARCHIVE_MEMBERS.items():
        extract_member_to_path(archive_paths[split], member_name, RAW_OUTPUTS[split])
        records = load_jsonl_from_zip(archive_paths[split], member_name)
        ko_records = [record for record in records if record.get("target_locale") == LOCALE]
        flattened_records = [flatten_record(record, split=split) for record in ko_records]
        flattened_splits[split] = flattened_records
        write_jsonl(flattened_records, PROCESSED_DIR / f"{split}_ko.jsonl")
        summary["splits"][split] = {
            "record_count": len(flattened_records),
            "output_jsonl": str((PROCESSED_DIR / f"{split}_ko.jsonl").relative_to(ROOT)),
        }

    gpt4o_predictions = load_prediction_map(
        archive_paths["predictions"],
        MODEL_MEMBERS["gpt4o_prediction"],
        RAW_OUTPUTS["gpt4o_prediction"],
    )
    gpt4o_mini_predictions = load_prediction_map(
        archive_paths["predictions"],
        MODEL_MEMBERS["gpt4o_mini_prediction"],
        RAW_OUTPUTS["gpt4o_mini_prediction"],
    )

    merged_validation = build_merged_validation(
        flattened_splits["validation"], gpt4o_predictions, gpt4o_mini_predictions
    )
    write_jsonl(merged_validation, PROCESSED_DIR / "validation_ko_merged.jsonl")
    write_csv(merged_validation, OUTPUTS_METRICS_DIR / "validation_ko_merged.csv")

    combined_table = build_combined_table(flattened_splits["sample"], merged_validation)
    write_jsonl(combined_table, PROCESSED_DIR / "ko_analysis_table.jsonl")
    write_csv(combined_table, OUTPUTS_METRICS_DIR / "ko_analysis_table.csv")

    analysis_subset = pick_analysis_subset(merged_validation, ANALYSIS_SUBSET_SIZE)
    write_csv(analysis_subset, HUMAN_EVAL_DIR / "ko_validation_analysis_subset_250.csv")

    annotation_template = build_annotation_template(analysis_subset)
    write_csv(annotation_template, HUMAN_EVAL_DIR / "ko_annotation_template.csv")

    summary["splits"]["validation"]["gpt4o_predictions"] = len(gpt4o_predictions)
    summary["splits"]["validation"]["gpt4o_mini_predictions"] = len(gpt4o_mini_predictions)
    summary["outputs"] = {
        "merged_validation_jsonl": "data/processed/validation_ko_merged.jsonl",
        "merged_validation_csv": "outputs/metrics/validation_ko_merged.csv",
        "combined_analysis_jsonl": "data/processed/ko_analysis_table.jsonl",
        "combined_analysis_csv": "outputs/metrics/ko_analysis_table.csv",
        "analysis_subset_csv": "data/human_eval/ko_validation_analysis_subset_250.csv",
        "annotation_template_csv": "data/human_eval/ko_annotation_template.csv",
    }
    summary["subset_size"] = len(analysis_subset)

    with (PROCESSED_DIR / "ko_dataset_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main()
