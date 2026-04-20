#!/usr/bin/env python3
"""Run lightweight entity-sensitive metrics on the Korean validation set."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from metrics_utils import load_jsonl, longest_common_substring_length, normalize_text, write_csv


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "validation_ko_merged.jsonl"
OUTPUT_DIR = ROOT / "outputs" / "metrics"

MODEL_FIELDS = {
    "gpt4o": "gpt4o_prediction",
    "gpt4o_mini": "gpt4o_mini_prediction",
}


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


def main() -> None:
    records = load_jsonl(INPUT_PATH)
    by_example_rows: list[dict[str, object]] = []
    grouped_rows: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    overall_rows: dict[str, list[dict[str, object]]] = defaultdict(list)

    for record in records:
        primary_entity_type = (record.get("entity_types") or ["Unknown"])[0]
        primary_mention = record.get("reference_mention", "")
        all_mentions = record.get("reference_mentions") or []
        for model_name, field_name in MODEL_FIELDS.items():
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

    write_csv(OUTPUT_DIR / "entity_metrics_by_example.csv", by_example_rows)
    write_csv(OUTPUT_DIR / "entity_metrics_overall.csv", overall_output)
    write_csv(OUTPUT_DIR / "entity_metrics_by_entity_type.csv", by_entity_type_output)

    print(f"Saved {OUTPUT_DIR.relative_to(ROOT) / 'entity_metrics_by_example.csv'}")
    print(f"Saved {OUTPUT_DIR.relative_to(ROOT) / 'entity_metrics_overall.csv'}")
    print(f"Saved {OUTPUT_DIR.relative_to(ROOT) / 'entity_metrics_by_entity_type.csv'}")


if __name__ == "__main__":
    main()
