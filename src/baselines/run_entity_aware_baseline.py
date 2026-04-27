#!/usr/bin/env python3
"""Run a lightweight entity-aware EN->KO baseline using Wikidata label injection."""

from __future__ import annotations

import argparse
from pathlib import Path

from baseline_utils import (
    BASE_INPUT_PATH,
    build_entity_aware_source,
    fetch_wikidata_entities,
    load_jsonl,
    translate_texts,
    update_combined_baseline_dataset,
    write_prediction_artifacts,
)


DEFAULT_MODEL_NAME = "facebook/m2m100_418M"
PREDICTION_FIELD = "entity_aware_mt_prediction"
OUTPUT_STEM = "validation_ko_entity_aware_mt_predictions"


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

    unique_ids = sorted({str(record.get("wikidata_id", "")) for record in records if record.get("wikidata_id")})
    entity_map = fetch_wikidata_entities(unique_ids)

    rewrite_metadata = []
    rewritten_sources = []
    for record in records:
        entity_info = entity_map.get(str(record.get("wikidata_id", "")), {})
        metadata = build_entity_aware_source(str(record["source"]), entity_info)
        rewrite_metadata.append(metadata)
        rewritten_sources.append(str(metadata["rewritten_source"]))

    predictions = translate_texts(
        rewritten_sources,
        model_name=args.model_name,
        batch_size=args.batch_size,
        max_new_tokens=args.max_new_tokens,
    )

    rows = []
    for record, metadata, prediction in zip(records, rewrite_metadata, predictions):
        rows.append(
            {
                "id": record["id"],
                "split": record.get("split", ""),
                "source": record["source"],
                "rewritten_source": metadata["rewritten_source"],
                "rewrite_applied": metadata["rewrite_applied"],
                "matched_source_entity": metadata["matched_source_entity"],
                "replacement_text": metadata["replacement_text"],
                "replacement_origin": metadata["replacement_origin"],
                "entity_label_en": metadata["entity_label_en"],
                "entity_label_ko": metadata["entity_label_ko"],
                "wikidata_id": record.get("wikidata_id", ""),
                "entity_types": record.get("entity_types", []),
                "baseline_name": "entity_aware_mt",
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
