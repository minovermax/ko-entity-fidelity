#!/usr/bin/env python3
"""Run lightweight entity-sensitive metrics on the Korean validation set."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from metrics_utils import load_jsonl, longest_common_substring_length, normalize_text, write_csv


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "validation_ko_merged.jsonl"
OUTPUT_DIR = ROOT / "outputs" / "metrics"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-path", type=Path, default=INPUT_PATH)
    parser.add_argument(
        "--model-field",
        action="append",
        default=[],
        help="Prediction field to score. Repeat for multiple fields. Defaults to auto-detected *_prediction fields.",
    )
    parser.add_argument(
        "--output-prefix",
        default="",
        help="Optional filename prefix for outputs, e.g. all_models",
    )
    return parser.parse_args()


def discover_model_fields(records: list[dict[str, object]]) -> dict[str, str]:
    if not records:
        return {}
    prediction_fields = [
        key for key in records[0].keys() if isinstance(key, str) and key.endswith("_prediction")
    ]
    return {field.removesuffix("_prediction"): field for field in sorted(prediction_fields)}


def contains_exact_mention(prediction: str, mentions: list[str]) -> bool:
    return any(mention and mention in prediction for mention in mentions)


def contains_normalized_mention(prediction: str, mentions: list[str]) -> bool:
    normalized_prediction = normalize_text(prediction)
    return any(normalize_text(mention) in normalized_prediction for mention in mentions if mention)


def mention_substring_recall_proxy(prediction: str, mentions: list[str]) -> float:
    normalized_prediction = normalize_text(prediction)
    best_score = 0.0
    for mention in mentions:
        normalized_mention = normalize_text(mention)
        if not normalized_mention:
            continue
        overlap = longest_common_substring_length(normalized_prediction, normalized_mention)
        best_score = max(best_score, overlap / len(normalized_mention))
    return best_score


def aggregate_group(model_name: str, rows: list[dict[str, object]], group_name: str, group_value: str) -> dict[str, object]:
    return {
        "model_name": model_name,
        group_name: group_value,
        "example_count": len(rows),
        "primary_mention_exact_match_rate": round(
            sum(int(row["primary_mention_exact_match"]) for row in rows) / len(rows), 4
        ),
        "any_reference_mention_exact_match_rate": round(
            sum(int(row["any_reference_mention_exact_match"]) for row in rows) / len(rows), 4
        ),
        "primary_mention_normalized_match_rate": round(
            sum(int(row["primary_mention_normalized_match"]) for row in rows) / len(rows), 4
        ),
        "any_reference_mention_normalized_match_rate": round(
            sum(int(row["any_reference_mention_normalized_match"]) for row in rows) / len(rows), 4
        ),
        "average_mention_substring_recall_proxy": round(
            sum(float(row["mention_substring_recall_proxy"]) for row in rows) / len(rows), 4
        ),
    }


def output_path(filename: str, prefix: str) -> Path:
    if prefix:
        return OUTPUT_DIR / f"{prefix}_{filename}"
    return OUTPUT_DIR / filename


def main() -> None:
    args = parse_args()
    records = load_jsonl(args.input_path)
    model_fields = discover_model_fields(records)
    if args.model_field:
        requested = {
            field.removesuffix("_prediction"): field if field.endswith("_prediction") else f"{field}_prediction"
            for field in args.model_field
        }
        model_fields = {name: field for name, field in requested.items() if field in model_fields.values()}
    if not model_fields:
        raise SystemExit(f"No prediction fields found in {args.input_path}")

    by_example_rows: list[dict[str, object]] = []
    grouped_rows: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    overall_rows: dict[str, list[dict[str, object]]] = defaultdict(list)

    for record in records:
        primary_entity_type = (record.get("entity_types") or ["Unknown"])[0]
        primary_mention = record.get("reference_mention", "")
        all_mentions = record.get("reference_mentions") or []
        for model_name, field_name in model_fields.items():
            prediction = record.get(field_name, "")
            row = {
                "id": record["id"],
                "model_name": model_name,
                "primary_entity_type": primary_entity_type,
                "prediction": prediction,
                "primary_reference_mention": primary_mention,
                "reference_mentions": all_mentions,
                "primary_mention_exact_match": contains_exact_mention(prediction, [primary_mention]),
                "any_reference_mention_exact_match": contains_exact_mention(prediction, all_mentions),
                "primary_mention_normalized_match": contains_normalized_mention(
                    prediction, [primary_mention]
                ),
                "any_reference_mention_normalized_match": contains_normalized_mention(
                    prediction, all_mentions
                ),
                "mention_substring_recall_proxy": round(
                    mention_substring_recall_proxy(prediction, all_mentions), 4
                ),
            }
            by_example_rows.append(row)
            grouped_rows[(model_name, primary_entity_type)].append(row)
            overall_rows[model_name].append(row)

    overall_output = [
        aggregate_group(model_name, rows, "scope", "overall")
        for model_name, rows in sorted(overall_rows.items())
    ]
    by_entity_type_output = [
        aggregate_group(model_name, rows, "primary_entity_type", primary_entity_type)
        for (model_name, primary_entity_type), rows in sorted(grouped_rows.items())
    ]

    by_example_path = output_path("entity_metrics_by_example.csv", args.output_prefix)
    overall_path = output_path("entity_metrics_overall.csv", args.output_prefix)
    by_entity_type_path = output_path("entity_metrics_by_entity_type.csv", args.output_prefix)

    write_csv(by_example_path, by_example_rows)
    write_csv(overall_path, overall_output)
    write_csv(by_entity_type_path, by_entity_type_output)

    print(f"Saved {by_example_path.relative_to(ROOT)}")
    print(f"Saved {overall_path.relative_to(ROOT)}")
    print(f"Saved {by_entity_type_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
