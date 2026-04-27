#!/usr/bin/env python3
"""Run a plain pretrained EN->KO MT baseline on the Korean validation set."""

from __future__ import annotations

import argparse
from pathlib import Path

from baseline_utils import (
    BASE_INPUT_PATH,
    load_jsonl,
    translate_texts,
    update_combined_baseline_dataset,
    write_prediction_artifacts,
)


DEFAULT_MODEL_NAME = "facebook/m2m100_418M"
PREDICTION_FIELD = "vanilla_mt_prediction"
OUTPUT_STEM = "validation_ko_vanilla_mt_predictions"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-path", type=Path, default=BASE_INPUT_PATH)
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-augmented-dataset", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl(args.input_path)
    if args.limit > 0:
        records = records[: args.limit]

    sources = [str(record["source"]) for record in records]
    predictions = translate_texts(
        sources,
        model_name=args.model_name,
        batch_size=args.batch_size,
        max_new_tokens=args.max_new_tokens,
    )

    rows = []
    for record, prediction in zip(records, predictions):
        rows.append(
            {
                "id": record["id"],
                "split": record.get("split", ""),
                "source": record["source"],
                "wikidata_id": record.get("wikidata_id", ""),
                "entity_types": record.get("entity_types", []),
                "baseline_name": "vanilla_mt",
                "hf_model_name": args.model_name,
                "prediction_field": PREDICTION_FIELD,
                "prediction": prediction,
            }
        )

    jsonl_path, csv_path = write_prediction_artifacts(OUTPUT_STEM, rows)
    print(f"Saved {jsonl_path.relative_to(Path.cwd())}")
    print(f"Saved {csv_path.relative_to(Path.cwd())}")

    if not args.skip_augmented_dataset:
        dataset_path = update_combined_baseline_dataset(
            prediction_field=PREDICTION_FIELD,
            prediction_rows=rows,
            base_input_path=args.input_path,
        )
        print(f"Saved {dataset_path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
