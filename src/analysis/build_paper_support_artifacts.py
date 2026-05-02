#!/usr/bin/env python3
"""Build manuscript-support summaries from existing annotations and metrics."""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HUMAN_PATH = ROOT / "data" / "human_eval" / "human_eval_sheet.csv"
COMPARISON_PATH = ROOT / "outputs" / "metrics" / "metric_human_comparison_by_example.csv"
IAA_PATH = ROOT / "outputs" / "metrics" / "inter_annotator_agreement.csv"
METRICS_DIR = ROOT / "outputs" / "metrics"
FIGURES_DIR = ROOT / "outputs" / "figures"

MODEL_SPECS = [
    {
        "model_name": "gpt4o",
        "entity_correct_field": "gpt4o_entity_correct",
        "quality_label_field": "gpt4o_quality_label",
        "metric_likely_miss_field": "gpt4o_metric_likely_miss",
    },
    {
        "model_name": "gpt4o_mini",
        "entity_correct_field": "gpt4o_mini_entity_correct",
        "quality_label_field": "gpt4o_mini_quality_label",
        "metric_likely_miss_field": "gpt4o_mini_metric_likely_miss",
    },
]

ACCEPTANCE_ORDER = ["acceptable", "borderline", "unacceptable"]
STRATEGY_ORDER = ["translate", "transliterate", "adapt", "preserve"]
MENTION_MATCH_ORDER = ["True", "False"]
HUMAN_ACCEPTABLE_QUALITY = {"correct", "acceptable_alias"}
HUMAN_BORDERLINE_QUALITY = {"partial_entity_error"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def human_acceptance_label(entity_correct: str, quality_label: str) -> str:
    if quality_label in HUMAN_ACCEPTABLE_QUALITY:
        return "acceptable"
    if quality_label in HUMAN_BORDERLINE_QUALITY or entity_correct == "partly":
        return "borderline"
    return "unacceptable"


def model_rows(human_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for human_row in human_rows:
        for spec in MODEL_SPECS:
            quality_label = human_row[spec["quality_label_field"]]
            entity_correct = human_row[spec["entity_correct_field"]]
            rows.append(
                {
                    "id": human_row["id"],
                    "model_name": spec["model_name"],
                    "target_rendering_strategy": human_row["target_rendering_strategy"],
                    "human_quality_label": quality_label,
                    "human_entity_correct": entity_correct,
                    "human_acceptance_label": human_acceptance_label(entity_correct, quality_label),
                    "human_metric_likely_miss": human_row[spec["metric_likely_miss_field"]],
                    "preferred_model": human_row["preferred_model"],
                }
            )
    return rows


def summarize_acceptability(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["model_name"]].append(row)

    output: list[dict[str, Any]] = []
    for model_name in sorted(grouped):
        total = len(grouped[model_name])
        counts = Counter(row["human_acceptance_label"] for row in grouped[model_name])
        for label in ACCEPTANCE_ORDER:
            count = counts.get(label, 0)
            output.append(
                {
                    "model_name": model_name,
                    "human_acceptance_label": label,
                    "count": count,
                    "total": total,
                    "proportion": round(count / total, 4),
                }
            )
    return output


def summarize_preferred_model(human_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    total = len(human_rows)
    counter = Counter(row["preferred_model"] for row in human_rows)
    labels = ["gpt4o", "gpt4o_mini", "tie", "neither"]
    return [
        {
            "preferred_model": label,
            "count": counter.get(label, 0),
            "total": total,
            "proportion": round(counter.get(label, 0) / total, 4),
            "rate": round(counter.get(label, 0) / total, 4),
        }
        for label in labels
    ]


def summarize_metric_miss(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["model_name"]].append(row)

    output: list[dict[str, Any]] = []
    for model_name in sorted(grouped):
        total = len(grouped[model_name])
        counter = Counter(row["human_metric_likely_miss"] or "blank" for row in grouped[model_name])
        for label in ["yes", "no", "maybe", "blank"]:
            count = counter.get(label, 0)
            output.append(
                {
                    "model_name": model_name,
                    "metric_likely_miss": label,
                    "count": count,
                    "total": total,
                    "proportion": round(count / total, 4),
                }
            )
    return output


def summarize_strategy_breakdown(
    human_rows: list[dict[str, str]], rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []

    strategy_counts = Counter(row["target_rendering_strategy"] for row in human_rows)
    total_examples = len(human_rows)
    for strategy in STRATEGY_ORDER:
        count = strategy_counts.get(strategy, 0)
        output.append(
            {
                "summary_type": "target_strategy_distribution",
                "model_name": "",
                "target_rendering_strategy": strategy,
                "human_acceptance_label": "all",
                "count": count,
                "total": total_examples,
                "proportion": round(count / total_examples, 4),
            }
        )

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_name"], row["target_rendering_strategy"])].append(row)

    for model_name, strategy in sorted(grouped):
        group_rows = grouped[(model_name, strategy)]
        total = len(group_rows)
        counts = Counter(row["human_acceptance_label"] for row in group_rows)
        for label in ACCEPTANCE_ORDER:
            count = counts.get(label, 0)
            output.append(
                {
                    "summary_type": "acceptability_by_target_strategy",
                    "model_name": model_name,
                    "target_rendering_strategy": strategy,
                    "human_acceptance_label": label,
                    "count": count,
                    "total": total,
                    "proportion": round(count / total, 4),
                }
            )
    return output


def summarize_mention_match_confusion(comparison_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], int] = Counter()
    model_totals: Counter[str] = Counter()
    match_totals: Counter[tuple[str, str]] = Counter()
    for row in comparison_rows:
        model = row["model_name"]
        mention_match = row["any_reference_mention_normalized_match"]
        label = row["human_acceptance_label"]
        grouped[(model, mention_match, label)] += 1
        model_totals[model] += 1
        match_totals[(model, mention_match)] += 1

    output: list[dict[str, Any]] = []
    for model in sorted(model_totals):
        for mention_match in MENTION_MATCH_ORDER:
            for label in ACCEPTANCE_ORDER:
                count = grouped.get((model, mention_match, label), 0)
                output.append(
                    {
                        "model_name": model,
                        "any_reference_mention_normalized_match": mention_match,
                        "human_acceptance_label": label,
                        "count": count,
                        "model_total": model_totals[model],
                        "mention_match_total": match_totals[(model, mention_match)],
                        "proportion_within_model": round(count / model_totals[model], 4),
                        "proportion_within_mention_match": round(
                            count / match_totals[(model, mention_match)], 4
                        )
                        if match_totals[(model, mention_match)]
                        else 0.0,
                    }
                )
    return output


def summarize_overlap_agreement() -> list[dict[str, Any]]:
    if not IAA_PATH.exists():
        return [
            {
                "field_group": "missing",
                "field": "missing_overlap_agreement_file",
                "overlap_count": 0,
                "agreement_count": 0,
                "percent_agreement": "",
                "cohen_kappa": "",
            }
        ]

    field_groups = {
        "target_rendering_strategy": "target_strategy",
        "official_korean_title_preferred": "target_strategy",
        "preserve_english_preferred": "target_strategy",
        "adaptation_needed": "target_strategy",
        "preferred_model": "model_preference",
    }
    output: list[dict[str, Any]] = []
    for row in read_csv(IAA_PATH):
        field = row["field"]
        output.append(
            {
                "field_group": field_groups.get(field, "model_output_judgment"),
                "field": field,
                "overlap_count": row["overlap_count"],
                "agreement_count": row["agreement_count"],
                "percent_agreement": row["percent_agreement"],
                "cohen_kappa": row["cohen_kappa"],
            }
        )
    return output


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    phat = successes / total
    denom = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denom
    half_width = z * math.sqrt((phat * (1 - phat) / total) + (z * z / (4 * total * total))) / denom
    return max(0.0, center - half_width), min(1.0, center + half_width)


def exact_two_sided_sign_p(smaller_count: int, total: int) -> float:
    if total == 0:
        return 1.0
    tail = sum(math.comb(total, value) for value in range(smaller_count + 1)) / (2**total)
    return min(1.0, 2 * tail)


def format_p_value(value: float) -> str:
    return f"{value:.6g}"


def summarize_stats(human_rows: list[dict[str, str]], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["model_name"]].append(row)

    for model_name in sorted(grouped):
        total = len(grouped[model_name])
        successes = sum(row["human_acceptance_label"] == "acceptable" for row in grouped[model_name])
        low, high = wilson_interval(successes, total)
        output.append(
            {
                "test": "wilson_95_ci_acceptability",
                "comparison": model_name,
                "n": total,
                "statistic": round(successes / total, 4),
                "p_value": "",
                "ci_low": round(low, 4),
                "ci_high": round(high, 4),
                "details": f"{successes}/{total} acceptable",
            }
        )

    gpt4o_only = 0
    mini_only = 0
    both_same = 0
    for human_row in human_rows:
        gpt4o_label = human_acceptance_label(
            human_row["gpt4o_entity_correct"], human_row["gpt4o_quality_label"]
        )
        mini_label = human_acceptance_label(
            human_row["gpt4o_mini_entity_correct"], human_row["gpt4o_mini_quality_label"]
        )
        gpt4o_ok = gpt4o_label == "acceptable"
        mini_ok = mini_label == "acceptable"
        if gpt4o_ok and not mini_ok:
            gpt4o_only += 1
        elif mini_ok and not gpt4o_ok:
            mini_only += 1
        else:
            both_same += 1
    discordant = gpt4o_only + mini_only
    output.append(
        {
            "test": "mcnemar_exact_acceptability",
            "comparison": "gpt4o_vs_gpt4o_mini",
            "n": len(human_rows),
            "statistic": f"b={gpt4o_only}; c={mini_only}; ties={both_same}",
            "p_value": format_p_value(
                exact_two_sided_sign_p(min(gpt4o_only, mini_only), discordant)
            ),
            "ci_low": "",
            "ci_high": "",
            "details": "b counts gpt4o acceptable and gpt4o_mini not acceptable; c counts reverse",
        }
    )

    preferred_counts = Counter(row["preferred_model"] for row in human_rows)
    preferred_total = preferred_counts["gpt4o"] + preferred_counts["gpt4o_mini"]
    output.append(
        {
            "test": "sign_test_preferred_model",
            "comparison": "gpt4o_vs_gpt4o_mini_excluding_tie_neither",
            "n": preferred_total,
            "statistic": f"gpt4o={preferred_counts['gpt4o']}; gpt4o_mini={preferred_counts['gpt4o_mini']}",
            "p_value": format_p_value(
                exact_two_sided_sign_p(
                    min(preferred_counts["gpt4o"], preferred_counts["gpt4o_mini"]),
                    preferred_total,
                )
            ),
            "ci_low": "",
            "ci_high": "",
            "details": "Two-sided exact sign test, excluding tie/neither labels",
        }
    )
    return output


def write_svg(path: Path, parts: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def draw_stacked_acceptability(summary_rows: list[dict[str, Any]]) -> None:
    colors = {
        "acceptable": "#4f7f58",
        "borderline": "#d4a94f",
        "unacceptable": "#c95f50",
    }
    models = sorted({str(row["model_name"]) for row in summary_rows})
    rows_by_key = {
        (str(row["model_name"]), str(row["human_acceptance_label"])): row
        for row in summary_rows
    }
    width = 760
    height = 240
    left = 145
    bar_width = 480
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="32" font-family="Arial, sans-serif" font-size="18" fill="#202422">Human Acceptability by Model</text>',
        '<text x="24" y="52" font-family="Arial, sans-serif" font-size="12" fill="#5d665f">Counts from the 200-example human evaluation subset</text>',
    ]
    for index, model in enumerate(models):
        y = 88 + index * 58
        x = left
        parts.append(f'<text x="24" y="{y + 18}" font-family="Arial, sans-serif" font-size="13" fill="#202422">{svg_escape(model)}</text>')
        for label in ACCEPTANCE_ORDER:
            row = rows_by_key[(model, label)]
            segment = bar_width * float(row["proportion"])
            parts.append(f'<rect x="{x:.2f}" y="{y}" width="{segment:.2f}" height="28" fill="{colors[label]}"/>')
            if segment > 34:
                parts.append(f'<text x="{x + segment / 2:.2f}" y="{y + 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#ffffff">{row["count"]}</text>')
            x += segment
    legend_x = 24
    for i, label in enumerate(ACCEPTANCE_ORDER):
        lx = legend_x + i * 150
        parts.append(f'<rect x="{lx}" y="205" width="12" height="12" fill="{colors[label]}"/>')
        parts.append(f'<text x="{lx + 18}" y="215" font-family="Arial, sans-serif" font-size="11" fill="#202422">{label}</text>')
    parts.append("</svg>")
    write_svg(FIGURES_DIR / "acceptability_by_model.svg", parts)


def draw_strategy_distribution(strategy_rows: list[dict[str, Any]]) -> None:
    rows = [row for row in strategy_rows if row["summary_type"] == "target_strategy_distribution"]
    width = 700
    height = 360
    left = 78
    bottom = 290
    plot_height = 210
    bar_width = 82
    gap = 44
    max_count = max(int(row["count"]) for row in rows) or 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="32" font-family="Arial, sans-serif" font-size="18" fill="#202422">Target Rendering Strategy Distribution</text>',
        '<text x="24" y="52" font-family="Arial, sans-serif" font-size="12" fill="#5d665f">Human target-strategy labels over 200 examples</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{width - 40}" y2="{bottom}" stroke="#d7ddd8"/>',
    ]
    for index, row in enumerate(rows):
        count = int(row["count"])
        x = left + index * (bar_width + gap)
        bar_h = plot_height * count / max_count
        y = bottom - bar_h
        parts.append(f'<rect x="{x}" y="{y:.2f}" width="{bar_width}" height="{bar_h:.2f}" rx="4" fill="#5c7d8b"/>')
        parts.append(f'<text x="{x + bar_width / 2}" y="{y - 8:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#202422">{count}</text>')
        parts.append(f'<text x="{x + bar_width / 2}" y="{bottom + 22}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#202422">{svg_escape(str(row["target_rendering_strategy"]))}</text>')
    parts.append("</svg>")
    write_svg(FIGURES_DIR / "rendering_strategy_distribution.svg", parts)


def draw_mention_match_confusion(confusion_rows: list[dict[str, Any]]) -> None:
    categories = [
        ("matched_acceptable", "match + acceptable", "#4f7f58"),
        ("matched_not_acceptable", "match + not acceptable", "#d4a94f"),
        ("missed_acceptable", "no match + acceptable", "#c95f50"),
        ("missed_not_acceptable", "no match + not acceptable", "#7b8794"),
    ]
    counts: Counter[tuple[str, str]] = Counter()
    for row in confusion_rows:
        model = str(row["model_name"])
        match = str(row["any_reference_mention_normalized_match"])
        label = str(row["human_acceptance_label"])
        count = int(row["count"])
        if match == "True" and label == "acceptable":
            category = "matched_acceptable"
        elif match == "True":
            category = "matched_not_acceptable"
        elif label == "acceptable":
            category = "missed_acceptable"
        else:
            category = "missed_not_acceptable"
        counts[(model, category)] += count

    models = sorted({str(row["model_name"]) for row in confusion_rows})
    width = 820
    height = 260
    left = 145
    bar_width = 520
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="32" font-family="Arial, sans-serif" font-size="18" fill="#202422">Mention Match vs Human Acceptability</text>',
        '<text x="24" y="52" font-family="Arial, sans-serif" font-size="12" fill="#5d665f">Cases where mention matching aligns or conflicts with human acceptability</text>',
    ]
    for index, model in enumerate(models):
        y = 88 + index * 58
        x = left
        total = sum(counts[(model, key)] for key, _, _ in categories) or 1
        parts.append(f'<text x="24" y="{y + 18}" font-family="Arial, sans-serif" font-size="13" fill="#202422">{svg_escape(model)}</text>')
        for key, _, color in categories:
            count = counts[(model, key)]
            segment = bar_width * count / total
            parts.append(f'<rect x="{x:.2f}" y="{y}" width="{segment:.2f}" height="28" fill="{color}"/>')
            if segment > 34:
                parts.append(f'<text x="{x + segment / 2:.2f}" y="{y + 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#ffffff">{count}</text>')
            x += segment
    for i, (_, label, color) in enumerate(categories):
        lx = 24 + (i % 2) * 260
        ly = 205 + (i // 2) * 20
        parts.append(f'<rect x="{lx}" y="{ly}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text x="{lx + 18}" y="{ly + 10}" font-family="Arial, sans-serif" font-size="11" fill="#202422">{svg_escape(label)}</text>')
    parts.append("</svg>")
    write_svg(FIGURES_DIR / "mention_match_confusion.svg", parts)


def draw_strategy_acceptability(strategy_rows: list[dict[str, Any]]) -> None:
    rows = [
        row
        for row in strategy_rows
        if row["summary_type"] == "acceptability_by_target_strategy"
        and row["human_acceptance_label"] == "acceptable"
    ]
    values = {(row["model_name"], row["target_rendering_strategy"]): float(row["proportion"]) for row in rows}
    width = 780
    height = 390
    left = 74
    bottom = 310
    plot_height = 220
    group_gap = 58
    bar_width = 44
    colors = {"gpt4o": "#d0624a", "gpt4o_mini": "#5b7f4a"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="32" font-family="Arial, sans-serif" font-size="18" fill="#202422">Acceptability by Target Rendering Strategy</text>',
        '<text x="24" y="52" font-family="Arial, sans-serif" font-size="12" fill="#5d665f">Acceptable proportion within each target-strategy group</text>',
        f'<line x1="{left}" y1="{bottom}" x2="{width - 40}" y2="{bottom}" stroke="#d7ddd8"/>',
    ]
    for index, strategy in enumerate(STRATEGY_ORDER):
        group_x = left + index * (bar_width * 2 + group_gap)
        for model_index, model in enumerate(["gpt4o", "gpt4o_mini"]):
            value = values.get((model, strategy), 0.0)
            x = group_x + model_index * bar_width
            bar_h = plot_height * value
            y = bottom - bar_h
            parts.append(f'<rect x="{x}" y="{y:.2f}" width="{bar_width - 6}" height="{bar_h:.2f}" rx="4" fill="{colors[model]}"/>')
            parts.append(f'<text x="{x + (bar_width - 6) / 2}" y="{y - 7:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#202422">{value:.2f}</text>')
        parts.append(f'<text x="{group_x + bar_width - 3}" y="{bottom + 22}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#202422">{svg_escape(strategy)}</text>')
    for i, model in enumerate(["gpt4o", "gpt4o_mini"]):
        lx = 24 + i * 145
        parts.append(f'<rect x="{lx}" y="360" width="12" height="12" fill="{colors[model]}"/>')
        parts.append(f'<text x="{lx + 18}" y="370" font-family="Arial, sans-serif" font-size="11" fill="#202422">{model}</text>')
    parts.append("</svg>")
    write_svg(FIGURES_DIR / "strategy_acceptability_by_model.svg", parts)


def main() -> None:
    human_rows = read_csv(HUMAN_PATH)
    comparison_rows = read_csv(COMPARISON_PATH)
    expanded_rows = model_rows(human_rows)

    acceptability_rows = summarize_acceptability(expanded_rows)
    preferred_rows = summarize_preferred_model(human_rows)
    metric_miss_rows = summarize_metric_miss(expanded_rows)
    strategy_rows = summarize_strategy_breakdown(human_rows, expanded_rows)
    mention_confusion_rows = summarize_mention_match_confusion(comparison_rows)
    overlap_rows = summarize_overlap_agreement()
    stat_rows = summarize_stats(human_rows, expanded_rows)

    write_csv(METRICS_DIR / "human_acceptability_summary.csv", acceptability_rows)
    write_csv(METRICS_DIR / "preferred_model_summary.csv", preferred_rows)
    write_csv(METRICS_DIR / "metric_miss_summary.csv", metric_miss_rows)
    write_csv(METRICS_DIR / "strategy_breakdown.csv", strategy_rows)
    write_csv(METRICS_DIR / "mention_match_confusion.csv", mention_confusion_rows)
    write_csv(METRICS_DIR / "overlap_agreement_summary.csv", overlap_rows)
    write_csv(METRICS_DIR / "stat_tests.csv", stat_rows)

    draw_stacked_acceptability(acceptability_rows)
    draw_strategy_distribution(strategy_rows)
    draw_mention_match_confusion(mention_confusion_rows)
    draw_strategy_acceptability(strategy_rows)

    for path in [
        METRICS_DIR / "human_acceptability_summary.csv",
        METRICS_DIR / "preferred_model_summary.csv",
        METRICS_DIR / "metric_miss_summary.csv",
        METRICS_DIR / "strategy_breakdown.csv",
        METRICS_DIR / "mention_match_confusion.csv",
        METRICS_DIR / "overlap_agreement_summary.csv",
        METRICS_DIR / "stat_tests.csv",
        FIGURES_DIR / "acceptability_by_model.svg",
        FIGURES_DIR / "rendering_strategy_distribution.svg",
        FIGURES_DIR / "mention_match_confusion.svg",
        FIGURES_DIR / "strategy_acceptability_by_model.svg",
    ]:
        print(f"Saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
