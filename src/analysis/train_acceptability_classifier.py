#!/usr/bin/env python3
"""Train a tiny supervised diagnostic classifier for human acceptability."""

from __future__ import annotations

import csv
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "outputs" / "metrics" / "metric_human_comparison_by_example.csv"
OUTPUT_METRICS_PATH = ROOT / "outputs" / "metrics" / "acceptability_classifier_summary.csv"
OUTPUT_PREDICTIONS_PATH = ROOT / "outputs" / "metrics" / "acceptability_classifier_predictions.csv"
OUTPUT_NOTES_PATH = ROOT / "docs" / "notes" / "acceptability_classifier.md"

RANDOM_SEED = 4652
EPOCHS = 2500
LEARNING_RATE = 0.08
L2 = 0.001


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_bool(raw: str) -> float:
    return 1.0 if raw.strip().lower() == "true" else 0.0


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def split_ids(rows: list[dict[str, str]]) -> tuple[set[str], set[str]]:
    ids = sorted({row["id"] for row in rows})
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(ids)
    test_count = max(1, round(len(ids) * 0.2))
    test_ids = set(ids[:test_count])
    train_ids = set(ids[test_count:])
    return train_ids, test_ids


def build_feature_maps(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    entity_types = sorted({row["primary_entity_type"] for row in rows})
    model_names = sorted({row["model_name"] for row in rows})
    return entity_types, model_names


def features(
    row: dict[str, str],
    entity_types: list[str],
    model_names: list[str],
) -> list[float]:
    values = [
        1.0,
        float(row["sentence_bleu"]) / 100.0,
        float(row["sentence_chrf"]) / 100.0,
        parse_bool(row["normalized_reference_exact_match"]),
        parse_bool(row["general_chrf_pass"]),
        parse_bool(row["any_reference_mention_normalized_match"]),
        float(row["mention_substring_recall_proxy"]),
    ]
    values.extend(1.0 if row["primary_entity_type"] == item else 0.0 for item in entity_types)
    values.extend(1.0 if row["model_name"] == item else 0.0 for item in model_names)
    return values


def label(row: dict[str, str]) -> int:
    return 1 if row["human_acceptance_label"] == "acceptable" else 0


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def train_logistic_regression(feature_rows: list[list[float]], labels: list[int]) -> list[float]:
    weights = [0.0] * len(feature_rows[0])
    order = list(range(len(feature_rows)))
    rng = random.Random(RANDOM_SEED)
    for _ in range(EPOCHS):
        rng.shuffle(order)
        for index in order:
            x = feature_rows[index]
            y = labels[index]
            pred = sigmoid(dot(weights, x))
            error = pred - y
            for feature_index, value in enumerate(x):
                regularization = 0.0 if feature_index == 0 else L2 * weights[feature_index]
                weights[feature_index] -= LEARNING_RATE * ((error * value) + regularization)
    return weights


def evaluate(predictions: list[int], gold: list[int]) -> dict[str, float]:
    total = len(gold)
    correct = sum(pred == actual for pred, actual in zip(predictions, gold))
    tp = sum(pred == 1 and actual == 1 for pred, actual in zip(predictions, gold))
    fp = sum(pred == 1 and actual == 0 for pred, actual in zip(predictions, gold))
    fn = sum(pred == 0 and actual == 1 for pred, actual in zip(predictions, gold))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "accuracy": round(correct / total, 4) if total else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def main() -> None:
    rows = read_csv(INPUT_PATH)
    train_ids, test_ids = split_ids(rows)
    train_rows = [row for row in rows if row["id"] in train_ids]
    test_rows = [row for row in rows if row["id"] in test_ids]
    entity_types, model_names = build_feature_maps(train_rows)

    x_train = [features(row, entity_types, model_names) for row in train_rows]
    y_train = [label(row) for row in train_rows]
    x_test = [features(row, entity_types, model_names) for row in test_rows]
    y_test = [label(row) for row in test_rows]

    majority_label = Counter(y_train).most_common(1)[0][0]
    majority_predictions = [majority_label] * len(y_test)
    metric_rule_predictions = [
        1
        if row["general_chrf_pass"].lower() == "true"
        and row["any_reference_mention_normalized_match"].lower() == "true"
        else 0
        for row in test_rows
    ]

    weights = train_logistic_regression(x_train, y_train)
    probabilities = [sigmoid(dot(weights, row_features)) for row_features in x_test]
    model_predictions = [1 if probability >= 0.5 else 0 for probability in probabilities]

    summary_rows = []
    for system_name, predictions in [
        ("majority_baseline", majority_predictions),
        ("metric_rule_baseline", metric_rule_predictions),
        ("logistic_regression", model_predictions),
    ]:
        metrics = evaluate(predictions, y_test)
        summary_rows.append(
            {
                "system": system_name,
                "train_rows": len(train_rows),
                "test_rows": len(test_rows),
                "train_example_ids": len(train_ids),
                "test_example_ids": len(test_ids),
                **metrics,
            }
        )

    prediction_rows = []
    for row, probability, prediction, actual in zip(test_rows, probabilities, model_predictions, y_test):
        prediction_rows.append(
            {
                "id": row["id"],
                "model_name": row["model_name"],
                "primary_entity_type": row["primary_entity_type"],
                "probability_acceptable": round(probability, 4),
                "predicted_acceptable": prediction,
                "gold_acceptable": actual,
                "human_acceptance_label": row["human_acceptance_label"],
                "sentence_chrf": row["sentence_chrf"],
                "any_reference_mention_normalized_match": row[
                    "any_reference_mention_normalized_match"
                ],
            }
        )

    write_csv(OUTPUT_METRICS_PATH, summary_rows)
    write_csv(OUTPUT_PREDICTIONS_PATH, prediction_rows)

    lines = [
        "# Acceptability Classifier",
        "",
        "This is an optional, tiny supervised diagnostic model. It is not the core contribution of the project.",
        "",
        "Task: predict whether a model output is human-acceptable using automatic metric features, model identity, and entity type.",
        "",
        f"- train rows: {len(train_rows)}",
        f"- test rows: {len(test_rows)}",
        f"- split seed: {RANDOM_SEED}",
        "",
        "| system | accuracy | precision | recall | F1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            f"| `{row['system']}` | {row['accuracy']} | {row['precision']} | {row['recall']} | {row['f1']} |"
        )
    lines.append("")
    lines.append(
        "Use this only if the final report needs an explicit trained ML component; otherwise keep it as an appendix or robustness check."
    )
    OUTPUT_NOTES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Saved {OUTPUT_METRICS_PATH.relative_to(ROOT)}")
    print(f"Saved {OUTPUT_PREDICTIONS_PATH.relative_to(ROOT)}")
    print(f"Saved {OUTPUT_NOTES_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
