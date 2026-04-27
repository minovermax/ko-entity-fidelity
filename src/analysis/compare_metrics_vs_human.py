#!/usr/bin/env python3
"""Compare automatic metrics against human judgments on the annotated subset."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HUMAN_SHEET_PATH = ROOT / "data" / "human_eval" / "human_eval_sheet.csv"
GENERAL_METRICS_PATH = ROOT / "outputs" / "metrics" / "general_metrics_by_example.csv"
ENTITY_METRICS_PATH = ROOT / "outputs" / "metrics" / "entity_metrics_by_example.csv"

OUTPUT_DIR = ROOT / "outputs" / "metrics"
FIGURE_DIR = ROOT / "outputs" / "figures"

BY_EXAMPLE_PATH = OUTPUT_DIR / "metric_human_comparison_by_example.csv"
SUMMARY_PATH = OUTPUT_DIR / "metric_human_summary.csv"
DISAGREEMENT_CASES_PATH = OUTPUT_DIR / "disagreement_cases.csv"
DISAGREEMENT_SUMMARY_PATH = OUTPUT_DIR / "disagreement_summary.csv"
ENTITY_TYPE_SUMMARY_PATH = OUTPUT_DIR / "metric_human_summary_by_entity_type.csv"
FIGURE_PATH = FIGURE_DIR / "metric_human_disagreement.svg"

GENERAL_CHRF_PASS_THRESHOLD = 50.0
GENERAL_BLEU_PASS_THRESHOLD = 35.0

MODEL_SPECS = [
    {
        "model_name": "gpt4o",
        "entity_correct_field": "gpt4o_entity_correct",
        "rendering_strategy_field": "gpt4o_rendering_strategy",
        "quality_label_field": "gpt4o_quality_label",
        "metric_likely_miss_field": "gpt4o_metric_likely_miss",
        "notes_field": "gpt4o_notes",
        "prediction_field": "gpt4o_prediction",
    },
    {
        "model_name": "gpt4o_mini",
        "entity_correct_field": "gpt4o_mini_entity_correct",
        "rendering_strategy_field": "gpt4o_mini_rendering_strategy",
        "quality_label_field": "gpt4o_mini_quality_label",
        "metric_likely_miss_field": "gpt4o_mini_metric_likely_miss",
        "notes_field": "gpt4o_mini_notes",
        "prediction_field": "gpt4o_mini_prediction",
    },
]

HUMAN_ACCEPTABLE_QUALITY = {"correct", "acceptable_alias"}
HUMAN_BORDERLINE_QUALITY = {"partial_entity_error"}
ALIGNMENT_CATEGORIES = {
    "all_signals_align_on_acceptance",
    "all_signals_align_on_rejection",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: stringify(value) for key, value in row.items()})


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def parse_bool(raw_value: str) -> bool:
    return raw_value.strip().lower() == "true"


def human_acceptance_label(entity_correct: str, quality_label: str) -> str:
    if quality_label in HUMAN_ACCEPTABLE_QUALITY:
        return "acceptable"
    if quality_label in HUMAN_BORDERLINE_QUALITY or entity_correct == "partly":
        return "borderline"
    return "unacceptable"


def disagreement_category(
    human_acceptance: str,
    general_pass: bool,
    entity_pass: bool,
) -> str:
    if human_acceptance == "acceptable":
        if general_pass and entity_pass:
            return "all_signals_align_on_acceptance"
        if general_pass and not entity_pass:
            return "entity_metric_too_harsh_on_acceptable_output"
        if not general_pass and entity_pass:
            return "general_metric_too_harsh_on_acceptable_output"
        return "both_metrics_too_harsh_on_acceptable_output"

    if human_acceptance == "unacceptable":
        if general_pass and entity_pass:
            return "both_metrics_miss_human_rejection"
        if general_pass and not entity_pass:
            return "general_metric_miss_human_rejection"
        if not general_pass and entity_pass:
            return "entity_metric_miss_human_rejection"
        return "all_signals_align_on_rejection"

    if general_pass and entity_pass:
        return "borderline_human_but_metrics_pass"
    if general_pass and not entity_pass:
        return "borderline_human_general_pass_entity_fail"
    if not general_pass and entity_pass:
        return "borderline_human_general_fail_entity_pass"
    return "borderline_human_and_metrics_fail"


def load_metric_maps() -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], dict[str, str]]]:
    general_rows = read_csv_rows(GENERAL_METRICS_PATH)
    entity_rows = read_csv_rows(ENTITY_METRICS_PATH)
    general_map = {(row["id"], row["model_name"]): row for row in general_rows}
    entity_map = {(row["id"], row["model_name"]): row for row in entity_rows}
    return general_map, entity_map


def build_by_example_rows() -> list[dict[str, Any]]:
    human_rows = read_csv_rows(HUMAN_SHEET_PATH)
    general_map, entity_map = load_metric_maps()

    rows: list[dict[str, Any]] = []
    for human_row in human_rows:
        for spec in MODEL_SPECS:
            key = (human_row["id"], spec["model_name"])
            if key not in general_map or key not in entity_map:
                raise KeyError(f"Missing metric rows for {key}")

            general_row = general_map[key]
            entity_row = entity_map[key]
            entity_correct = human_row[spec["entity_correct_field"]]
            quality_label = human_row[spec["quality_label_field"]]
            human_acceptance = human_acceptance_label(entity_correct, quality_label)

            sentence_bleu = float(general_row["sentence_bleu"])
            sentence_chrf = float(general_row["sentence_chrf"])
            general_bleu_pass = sentence_bleu >= GENERAL_BLEU_PASS_THRESHOLD
            general_chrf_pass = sentence_chrf >= GENERAL_CHRF_PASS_THRESHOLD
            entity_metric_pass = parse_bool(entity_row["any_reference_mention_normalized_match"])

            category = disagreement_category(
                human_acceptance=human_acceptance,
                general_pass=general_chrf_pass,
                entity_pass=entity_metric_pass,
            )

            row = {
                "id": human_row["id"],
                "model_name": spec["model_name"],
                "primary_entity_type": human_row["primary_entity_type"],
                "source": human_row["source"],
                "prediction": human_row[spec["prediction_field"]],
                "reference_translation": human_row["reference_translation"],
                "reference_mention": human_row["reference_mention"],
                "target_rendering_strategy": human_row["target_rendering_strategy"],
                "official_korean_title_preferred": human_row["official_korean_title_preferred"],
                "preserve_english_preferred": human_row["preserve_english_preferred"],
                "adaptation_needed": human_row["adaptation_needed"],
                "human_entity_correct": entity_correct,
                "human_rendering_strategy": human_row[spec["rendering_strategy_field"]],
                "human_quality_label": quality_label,
                "human_metric_likely_miss": human_row[spec["metric_likely_miss_field"]],
                "human_notes": human_row[spec["notes_field"]],
                "preferred_model": human_row["preferred_model"],
                "human_acceptance_label": human_acceptance,
                "strategy_matches_target": (
                    human_row["target_rendering_strategy"] == human_row[spec["rendering_strategy_field"]]
                ),
                "sentence_bleu": round(sentence_bleu, 4),
                "sentence_chrf": round(sentence_chrf, 4),
                "normalized_reference_exact_match": parse_bool(
                    general_row["normalized_reference_exact_match"]
                ),
                "general_bleu_pass": general_bleu_pass,
                "general_chrf_pass": general_chrf_pass,
                "primary_mention_exact_match": parse_bool(entity_row["primary_mention_exact_match"]),
                "any_reference_mention_exact_match": parse_bool(
                    entity_row["any_reference_mention_exact_match"]
                ),
                "primary_mention_normalized_match": parse_bool(
                    entity_row["primary_mention_normalized_match"]
                ),
                "any_reference_mention_normalized_match": entity_metric_pass,
                "mention_substring_recall_proxy": float(
                    entity_row["mention_substring_recall_proxy"]
                ),
                "disagreement_category": category,
                "metric_human_disagreement": category not in ALIGNMENT_CATEGORIES,
                "korean_strategy_issue": quality_label == "wrong_rendering_strategy",
                "acceptable_alias_case": quality_label == "acceptable_alias",
                "both_metrics_pass": general_chrf_pass and entity_metric_pass,
                "both_metrics_fail": (not general_chrf_pass) and (not entity_metric_pass),
            }
            rows.append(row)
    return rows


def summarize_by_model(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["model_name"]].append(row)

    summary_rows: list[dict[str, Any]] = []
    for model_name, group_rows in sorted(grouped.items()):
        total = len(group_rows)
        summary_rows.append(
            {
                "model_name": model_name,
                "example_count": total,
                "acceptable_count": sum(
                    row["human_acceptance_label"] == "acceptable" for row in group_rows
                ),
                "borderline_count": sum(
                    row["human_acceptance_label"] == "borderline" for row in group_rows
                ),
                "unacceptable_count": sum(
                    row["human_acceptance_label"] == "unacceptable" for row in group_rows
                ),
                "general_chrf_pass_rate": round(
                    sum(row["general_chrf_pass"] for row in group_rows) / total, 4
                ),
                "entity_metric_pass_rate": round(
                    sum(row["any_reference_mention_normalized_match"] for row in group_rows)
                    / total,
                    4,
                ),
                "strategy_match_rate": round(
                    sum(row["strategy_matches_target"] for row in group_rows) / total, 4
                ),
                "metric_human_disagreement_rate": round(
                    sum(row["metric_human_disagreement"] for row in group_rows) / total, 4
                ),
                "metric_likely_miss_yes_rate": round(
                    sum(row["human_metric_likely_miss"] == "yes" for row in group_rows) / total,
                    4,
                ),
            }
        )
    return summary_rows


def summarize_disagreements(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str]] = Counter(
        (row["model_name"], row["disagreement_category"]) for row in rows
    )
    summary_rows: list[dict[str, Any]] = []
    for (model_name, category), count in sorted(counter.items()):
        summary_rows.append(
            {
                "model_name": model_name,
                "disagreement_category": category,
                "count": count,
            }
        )
    return summary_rows


def summarize_by_entity_type(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_name"], row["primary_entity_type"])].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (model_name, entity_type), group_rows in sorted(grouped.items()):
        total = len(group_rows)
        summary_rows.append(
            {
                "model_name": model_name,
                "primary_entity_type": entity_type,
                "example_count": total,
                "acceptable_rate": round(
                    sum(row["human_acceptance_label"] == "acceptable" for row in group_rows)
                    / total,
                    4,
                ),
                "general_chrf_pass_rate": round(
                    sum(row["general_chrf_pass"] for row in group_rows) / total, 4
                ),
                "entity_metric_pass_rate": round(
                    sum(row["any_reference_mention_normalized_match"] for row in group_rows)
                    / total,
                    4,
                ),
                "disagreement_rate": round(
                    sum(row["metric_human_disagreement"] for row in group_rows) / total, 4
                ),
            }
        )
    return summary_rows


def disagreement_case_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    case_rows = [row for row in rows if row["metric_human_disagreement"]]
    case_rows.sort(
        key=lambda row: (
            row["model_name"],
            row["disagreement_category"],
            row["primary_entity_type"],
            row["id"],
        )
    )
    return case_rows


def svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_disagreement_svg(summary_rows: list[dict[str, Any]]) -> None:
    filtered = [
        row
        for row in summary_rows
        if row["disagreement_category"] not in ALIGNMENT_CATEGORIES
    ]
    if not filtered:
        return

    categories = sorted(
        {row["disagreement_category"] for row in filtered},
        key=lambda category: sum(
            row["count"] for row in filtered if row["disagreement_category"] == category
        ),
        reverse=True,
    )
    models = ["gpt4o", "gpt4o_mini"]
    counts = {
        (row["model_name"], row["disagreement_category"]): int(row["count"])
        for row in filtered
    }

    left_margin = 240
    right_margin = 32
    top_margin = 48
    row_height = 42
    bar_height = 14
    bar_gap = 6
    max_count = max(counts.values()) if counts else 1
    plot_width = 640
    width = left_margin + plot_width + right_margin
    height = top_margin + row_height * len(categories) + 48

    colors = {"gpt4o": "#d0624a", "gpt4o_mini": "#5b7f4a"}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="28" font-family="Arial, sans-serif" font-size="18" fill="#1f2321">Metric vs Human Disagreement Cases</text>',
        '<text x="24" y="44" font-family="Arial, sans-serif" font-size="11" fill="#5c655f">Counts by disagreement category and model on the human-annotated subset</text>',
    ]

    for index, category in enumerate(categories):
        y_base = top_margin + index * row_height
        label = category.replace("_", " ")
        parts.append(
            f'<text x="24" y="{y_base + 18}" font-family="Arial, sans-serif" font-size="12" fill="#1f2321">{svg_escape(label)}</text>'
        )
        for model_index, model_name in enumerate(models):
            count = counts.get((model_name, category), 0)
            bar_width = 0 if max_count == 0 else (count / max_count) * plot_width
            bar_y = y_base + 4 + model_index * (bar_height + bar_gap)
            parts.append(
                f'<rect x="{left_margin}" y="{bar_y}" width="{bar_width:.2f}" height="{bar_height}" rx="4" fill="{colors[model_name]}"/>'
            )
            parts.append(
                f'<text x="{left_margin + bar_width + 8:.2f}" y="{bar_y + 11}" font-family="Arial, sans-serif" font-size="11" fill="#1f2321">{model_name}: {count}</text>'
            )

    parts.append("</svg>")
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_by_example_rows()
    summary_rows = summarize_by_model(rows)
    disagreement_rows = summarize_disagreements(rows)
    by_entity_type_rows = summarize_by_entity_type(rows)
    case_rows = disagreement_case_rows(rows)

    write_csv_rows(BY_EXAMPLE_PATH, rows)
    write_csv_rows(SUMMARY_PATH, summary_rows)
    write_csv_rows(DISAGREEMENT_SUMMARY_PATH, disagreement_rows)
    write_csv_rows(ENTITY_TYPE_SUMMARY_PATH, by_entity_type_rows)
    write_csv_rows(DISAGREEMENT_CASES_PATH, case_rows)
    write_disagreement_svg(disagreement_rows)

    print(f"Saved {BY_EXAMPLE_PATH.relative_to(ROOT)}")
    print(f"Saved {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Saved {DISAGREEMENT_SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Saved {ENTITY_TYPE_SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Saved {DISAGREEMENT_CASES_PATH.relative_to(ROOT)}")
    if FIGURE_PATH.exists():
        print(f"Saved {FIGURE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
