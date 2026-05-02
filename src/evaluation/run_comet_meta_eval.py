#!/usr/bin/env python3
"""Run official-style COMET/M-ETA evaluation on local reference splits.

M-ETA follows the public SapienzaNLP EA-MT eval notebook: for each example,
count the prediction correct if any gold target mention casefold-matches as a
substring of the model output. COMET is optional because it requires the
external `unbabel-comet` package and model downloads.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "processed" / "local_test_ko_with_baselines.jsonl"
DEFAULT_OUTPUT = ROOT / "outputs" / "metrics" / "comet_meta_results.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-path", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--model-field",
        action="append",
        default=[],
        help="Prediction field to score. Repeat for multiple fields. Defaults to all *_prediction fields.",
    )
    parser.add_argument(
        "--entity-type",
        action="append",
        default=[],
        help="Optional entity type filter. Repeat to include multiple types.",
    )
    parser.add_argument(
        "--run-comet",
        action="store_true",
        help="Run COMET with unbabel-comet. Requires package/model download.",
    )
    parser.add_argument("--comet-model", default="Unbabel/wmt22-comet-da")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gpus", type=int, default=0)
    parser.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="DataLoader workers for COMET. Explicitly positive avoids a Torch/COMET num_workers=0 issue.",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def discover_model_fields(records: list[dict[str, Any]]) -> dict[str, str]:
    if not records:
        return {}
    fields = [
        key
        for key in records[0]
        if isinstance(key, str) and key.endswith("_prediction")
    ]
    return {field.removesuffix("_prediction"): field for field in sorted(fields)}


def filter_records(records: list[dict[str, Any]], entity_types: list[str]) -> list[dict[str, Any]]:
    if not entity_types:
        return records
    wanted = set(entity_types)
    return [
        record
        for record in records
        if wanted.intersection(set(record.get("entity_types") or []))
    ]


def m_eta_for_model(records: list[dict[str, Any]], prediction_field: str) -> dict[str, Any]:
    correct = 0
    total = 0
    missing_predictions = 0

    for record in records:
        mentions = [mention for mention in record.get("reference_mentions", []) if mention]
        if not mentions:
            continue
        total += 1

        prediction = str(record.get(prediction_field, "") or "")
        if not prediction:
            missing_predictions += 1
            continue

        normalized_prediction = prediction.casefold()
        if any(mention.casefold() in normalized_prediction for mention in mentions):
            correct += 1

    return {
        "m_eta_correct": correct,
        "m_eta_total": total,
        "m_eta_missing_predictions": missing_predictions,
        "m_eta": round(100.0 * correct / total, 4) if total else 0.0,
    }


def comet_for_models(
    records: list[dict[str, Any]],
    model_fields: dict[str, str],
    comet_model: str,
    batch_size: int,
    gpus: int,
    num_workers: int,
) -> dict[str, dict[str, Any]]:
    try:
        from comet import download_model, load_from_checkpoint
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "COMET is not installed. Install with `python3 -m pip install unbabel-comet==2.2.4`."
        ) from exc

    model_path = download_model(comet_model)
    model = load_from_checkpoint(model_path)
    results: dict[str, dict[str, Any]] = {}

    for model_name, prediction_field in model_fields.items():
        instances: list[dict[str, str]] = []
        index_spans: dict[str, tuple[int, int]] = {}
        missing_predictions = 0
        current_index = 0

        for record in records:
            references = [
                target.get("translation", "")
                for target in record.get("targets", [])
                if isinstance(target, dict) and target.get("translation")
            ]
            prediction = str(record.get(prediction_field, "") or "")
            if not references:
                continue
            if not prediction:
                missing_predictions += 1
                continue

            start = current_index
            for reference in references:
                instances.append(
                    {
                        "src": str(record.get("source", "")),
                        "mt": prediction,
                        "ref": reference,
                    }
                )
                current_index += 1
            index_spans[str(record["id"])] = (start, current_index)

        if not instances:
            results[model_name] = {
                "comet_score": "",
                "comet_model": comet_model,
                "comet_status": "no_instances",
                "comet_missing_predictions": missing_predictions,
            }
            continue

        output = model.predict(
            instances,
            batch_size=batch_size,
            gpus=gpus,
            num_workers=num_workers,
        )
        scores = output.scores
        max_scores = [
            max(scores[start:end])
            for start, end in index_spans.values()
            if start < end
        ]
        denominator = len(max_scores) + missing_predictions
        score = sum(max_scores) / denominator if denominator else 0.0
        results[model_name] = {
            "comet_score": round(100.0 * score, 4),
            "comet_model": comet_model,
            "comet_status": "ok",
            "comet_missing_predictions": missing_predictions,
        }

    return results


def harmonic_mean(left: Any, right: Any) -> str:
    if left == "" or right == "":
        return ""
    left_float = float(left)
    right_float = float(right)
    if left_float + right_float == 0.0:
        return "0.0"
    return str(round(2 * (left_float * right_float) / (left_float + right_float), 4))


def main() -> None:
    args = parse_args()
    records = filter_records(load_jsonl(args.input_path), args.entity_type)
    model_fields = discover_model_fields(records)
    if args.model_field:
        requested = {
            field.removesuffix("_prediction"): field if field.endswith("_prediction") else f"{field}_prediction"
            for field in args.model_field
        }
        model_fields = {name: field for name, field in requested.items() if field in model_fields.values()}
    if not model_fields:
        raise SystemExit(f"No prediction fields found in {args.input_path}")

    comet_results: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "comet_score": "",
            "comet_model": args.comet_model,
            "comet_status": "not_run",
            "comet_missing_predictions": "",
        }
    )
    if args.run_comet:
        comet_results = comet_for_models(
            records=records,
            model_fields=model_fields,
            comet_model=args.comet_model,
            batch_size=args.batch_size,
            gpus=args.gpus,
            num_workers=args.num_workers,
        )

    output_rows: list[dict[str, Any]] = []
    split_name = records[0].get("local_eval_split") or records[0].get("split") if records else ""
    for model_name, prediction_field in sorted(model_fields.items()):
        m_eta = m_eta_for_model(records, prediction_field)
        comet = comet_results[model_name]
        output_rows.append(
            {
                "input_path": str(args.input_path.relative_to(ROOT)),
                "split": split_name,
                "model_name": model_name,
                "example_count": len(records),
                "prediction_field": prediction_field,
                "m_eta_correct": m_eta["m_eta_correct"],
                "m_eta_total": m_eta["m_eta_total"],
                "m_eta_missing_predictions": m_eta["m_eta_missing_predictions"],
                "m_eta": m_eta["m_eta"],
                "comet_score": comet["comet_score"],
                "comet_model": comet["comet_model"],
                "comet_status": comet["comet_status"],
                "comet_missing_predictions": comet["comet_missing_predictions"],
                "final_hmean_comet_meta": harmonic_mean(comet["comet_score"], m_eta["m_eta"]),
            }
        )

    write_csv(args.output_path, output_rows)
    print(f"Saved {args.output_path.relative_to(ROOT)}")
    if not args.run_comet:
        print(
            "COMET not run. Re-run with --run-comet after installing unbabel-comet "
            "to populate comet_score and final_hmean_comet_meta."
        )


if __name__ == "__main__":
    main()
