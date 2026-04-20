#!/usr/bin/env python3
"""Run lightweight general MT metrics on the Korean validation set."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from metrics_utils import chrf_score, corpus_bleu, load_jsonl, normalized_exact_match, write_csv


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "validation_ko_merged.jsonl"
OUTPUT_DIR = ROOT / "outputs" / "metrics"

MODEL_FIELDS = {
    "gpt4o": "gpt4o_prediction",
    "gpt4o_mini": "gpt4o_mini_prediction",
}


def aggregate_group(model_name: str, rows: list[dict[str, object]], group_name: str, group_value: str) -> dict[str, object]:
    predictions = [str(row["prediction"]) for row in rows]
    references = [list(row["reference_translations"]) for row in rows]
    sentence_bleu_scores = [float(row["sentence_bleu"]) for row in rows]
    sentence_chrf_scores = [float(row["sentence_chrf"]) for row in rows]
    normalized_exact_matches = [int(row["normalized_reference_exact_match"]) for row in rows]

    return {
        "model_name": model_name,
        group_name: group_value,
        "example_count": len(rows),
        "corpus_bleu": round(corpus_bleu(predictions, references), 4),
        "average_sentence_bleu": round(sum(sentence_bleu_scores) / len(sentence_bleu_scores), 4),
        "average_sentence_chrf": round(sum(sentence_chrf_scores) / len(sentence_chrf_scores), 4),
        "normalized_reference_exact_match_rate": round(
            sum(normalized_exact_matches) / len(normalized_exact_matches), 4
        ),
    }


def main() -> None:
    records = load_jsonl(INPUT_PATH)
    by_example_rows: list[dict[str, object]] = []
    grouped_rows: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    overall_rows: dict[str, list[dict[str, object]]] = defaultdict(list)

    for record in records:
        primary_entity_type = (record.get("entity_types") or ["Unknown"])[0]
        references = record.get("reference_translations") or []
        for model_name, field_name in MODEL_FIELDS.items():
            prediction = record.get(field_name, "")
            row = {
                "id": record["id"],
                "model_name": model_name,
                "primary_entity_type": primary_entity_type,
                "prediction": prediction,
                "reference_translations": references,
                "reference_count": len(references),
                "sentence_bleu": round(corpus_bleu([prediction], [references]), 4),
                "sentence_chrf": round(chrf_score(prediction, references), 4),
                "normalized_reference_exact_match": normalized_exact_match(prediction, references),
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

    write_csv(OUTPUT_DIR / "general_metrics_by_example.csv", by_example_rows)
    write_csv(OUTPUT_DIR / "general_metrics_overall.csv", overall_output)
    write_csv(OUTPUT_DIR / "general_metrics_by_entity_type.csv", by_entity_type_output)

    print(f"Saved {OUTPUT_DIR.relative_to(ROOT) / 'general_metrics_by_example.csv'}")
    print(f"Saved {OUTPUT_DIR.relative_to(ROOT) / 'general_metrics_overall.csv'}")
    print(f"Saved {OUTPUT_DIR.relative_to(ROOT) / 'general_metrics_by_entity_type.csv'}")


if __name__ == "__main__":
    main()
