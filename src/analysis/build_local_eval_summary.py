#!/usr/bin/env python3
"""Combine local dev/test metric outputs into one report table."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = ROOT / "outputs" / "metrics"
OUTPUT_PATH = METRICS_DIR / "local_eval_model_summary.csv"

SPLITS = {
    "dev": {
        "general": METRICS_DIR / "local_dev_all_models_general_metrics_overall.csv",
        "entity": METRICS_DIR / "local_dev_all_models_entity_metrics_overall.csv",
    },
    "test": {
        "general": METRICS_DIR / "local_test_all_models_general_metrics_overall.csv",
        "entity": METRICS_DIR / "local_test_all_models_entity_metrics_overall.csv",
    },
}


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


def main() -> None:
    rows: list[dict[str, Any]] = []
    for split_name, paths in SPLITS.items():
        general_rows = {row["model_name"]: row for row in read_csv(paths["general"])}
        entity_rows = {row["model_name"]: row for row in read_csv(paths["entity"])}
        for model_name in sorted(general_rows):
            general = general_rows[model_name]
            entity = entity_rows[model_name]
            rows.append(
                {
                    "split": split_name,
                    "model_name": model_name,
                    "example_count": general["example_count"],
                    "corpus_bleu": general["corpus_bleu"],
                    "average_sentence_chrf": general["average_sentence_chrf"],
                    "normalized_reference_exact_match_rate": general[
                        "normalized_reference_exact_match_rate"
                    ],
                    "any_reference_mention_normalized_match_rate": entity[
                        "any_reference_mention_normalized_match_rate"
                    ],
                    "average_mention_substring_recall_proxy": entity[
                        "average_mention_substring_recall_proxy"
                    ],
                }
            )

    write_csv(OUTPUT_PATH, rows)
    print(f"Saved {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
