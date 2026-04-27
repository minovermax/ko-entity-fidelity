#!/usr/bin/env python3
"""Build report-ready summary tables, figures, and a memo for the final write-up."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HUMAN_SHEET_PATH = ROOT / "data" / "human_eval" / "human_eval_sheet.csv"
COMPARISON_PATH = ROOT / "outputs" / "metrics" / "metric_human_comparison_by_example.csv"

METRICS_DIR = ROOT / "outputs" / "metrics"
FIGURES_DIR = ROOT / "outputs" / "figures"
DOCS_DIR = ROOT / "docs" / "notes"

PREFERRED_MODEL_PATH = METRICS_DIR / "preferred_model_summary.csv"
RENDERING_STRATEGY_PATH = METRICS_DIR / "rendering_strategy_summary.csv"
QUALITY_BY_MODEL_PATH = METRICS_DIR / "human_quality_by_model.csv"
DISAGREEMENT_ENTITY_PATH = METRICS_DIR / "disagreement_by_entity_type.csv"
RESULTS_MEMO_PATH = DOCS_DIR / "results_memo.md"

PREFERRED_MODEL_FIGURE_PATH = FIGURES_DIR / "preferred_model_summary.svg"
RENDERING_STRATEGY_FIGURE_PATH = FIGURES_DIR / "rendering_strategy_distribution.svg"
QUALITY_BY_MODEL_FIGURE_PATH = FIGURES_DIR / "human_quality_by_model.svg"

MODEL_ORDER = ["gpt4o", "gpt4o_mini"]
MODEL_COLORS = {"gpt4o": "#d0624a", "gpt4o_mini": "#5b7f4a"}


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
    return str(value)


def svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def summarize_preferred_model(human_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counter = Counter(row["preferred_model"] for row in human_rows)
    total = len(human_rows)
    order = ["gpt4o", "gpt4o_mini", "tie", "neither"]
    return [
        {
            "preferred_model": label,
            "count": counter.get(label, 0),
            "rate": round(counter.get(label, 0) / total, 4),
        }
        for label in order
    ]


def summarize_rendering_strategy(human_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counter = Counter(row["target_rendering_strategy"] for row in human_rows)
    total = len(human_rows)
    order = ["translate", "transliterate", "adapt", "preserve"]
    return [
        {
            "target_rendering_strategy": label,
            "count": counter.get(label, 0),
            "rate": round(counter.get(label, 0) / total, 4),
        }
        for label in order
    ]


def summarize_quality_by_model(human_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    specs = [
        ("gpt4o", "gpt4o_quality_label"),
        ("gpt4o_mini", "gpt4o_mini_quality_label"),
    ]
    quality_order = [
        "correct",
        "acceptable_alias",
        "partial_entity_error",
        "wrong_rendering_strategy",
        "incorrect_entity",
        "hallucinated_entity",
        "omitted_entity",
    ]
    summary_rows: list[dict[str, Any]] = []
    total = len(human_rows)
    for model_name, field_name in specs:
        counter = Counter(row[field_name] for row in human_rows)
        for quality_label in quality_order:
            count = counter.get(quality_label, 0)
            summary_rows.append(
                {
                    "model_name": model_name,
                    "quality_label": quality_label,
                    "count": count,
                    "rate": round(count / total, 4),
                }
            )
    return summary_rows


def summarize_disagreement_by_entity_type(
    comparison_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in comparison_rows:
        grouped[(row["model_name"], row["primary_entity_type"])].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (model_name, entity_type), rows in sorted(grouped.items()):
        total = len(rows)
        disagreements = sum(row["metric_human_disagreement"] == "True" for row in rows)
        acceptable = sum(row["human_acceptance_label"] == "acceptable" for row in rows)
        summary_rows.append(
            {
                "model_name": model_name,
                "primary_entity_type": entity_type,
                "example_count": total,
                "acceptable_count": acceptable,
                "disagreement_count": disagreements,
                "disagreement_rate": round(disagreements / total, 4),
            }
        )

    summary_rows.sort(
        key=lambda row: (
            row["model_name"],
            -float(row["disagreement_rate"]),
            row["primary_entity_type"],
        )
    )
    return summary_rows


def write_simple_bar_svg(
    title: str,
    subtitle: str,
    labels: list[str],
    values: list[int],
    colors: list[str],
    output_path: Path,
) -> None:
    left_margin = 72
    right_margin = 32
    top_margin = 62
    bottom_margin = 92
    plot_width = 560
    plot_height = 260
    width = left_margin + plot_width + right_margin
    height = top_margin + plot_height + bottom_margin
    max_value = max(values) if values else 1
    bar_gap = 24
    bar_width = (plot_width - bar_gap * (len(values) - 1)) / max(len(values), 1)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="28" font-family="Arial, sans-serif" font-size="18" fill="#1f2321">{svg_escape(title)}</text>',
        f'<text x="24" y="46" font-family="Arial, sans-serif" font-size="11" fill="#5c655f">{svg_escape(subtitle)}</text>',
        f'<line x1="{left_margin}" y1="{top_margin + plot_height}" x2="{left_margin + plot_width}" y2="{top_margin + plot_height}" stroke="#c9cfcb" stroke-width="1"/>',
    ]

    for index, (label, value, color) in enumerate(zip(labels, values, colors, strict=True)):
        x = left_margin + index * (bar_width + bar_gap)
        bar_height = 0 if max_value == 0 else (value / max_value) * plot_height
        y = top_margin + plot_height - bar_height
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="4" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{y - 8:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#1f2321">{value}</text>'
        )
        parts.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{top_margin + plot_height + 22:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#1f2321">{svg_escape(label)}</text>'
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts + ["</svg>"]) + "\n", encoding="utf-8")


def write_grouped_bar_svg(
    title: str,
    subtitle: str,
    category_labels: list[str],
    series: list[tuple[str, list[int], str]],
    output_path: Path,
) -> None:
    left_margin = 150
    right_margin = 32
    top_margin = 72
    row_height = 34
    group_gap = 8
    bar_height = 10
    plot_width = 520
    width = left_margin + plot_width + right_margin
    height = top_margin + row_height * len(category_labels) + 60
    max_value = max((max(values) for _, values, _ in series), default=1)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="28" font-family="Arial, sans-serif" font-size="18" fill="#1f2321">{svg_escape(title)}</text>',
        f'<text x="24" y="46" font-family="Arial, sans-serif" font-size="11" fill="#5c655f">{svg_escape(subtitle)}</text>',
    ]

    legend_x = left_margin
    for idx, (series_label, _, color) in enumerate(series):
        lx = legend_x + idx * 128
        parts.append(f'<rect x="{lx}" y="20" width="12" height="12" rx="2" fill="{color}"/>')
        parts.append(
            f'<text x="{lx + 18}" y="30" font-family="Arial, sans-serif" font-size="11" fill="#1f2321">{svg_escape(series_label)}</text>'
        )

    for row_index, category_label in enumerate(category_labels):
        y = top_margin + row_index * row_height
        parts.append(
            f'<text x="24" y="{y + 14}" font-family="Arial, sans-serif" font-size="11" fill="#1f2321">{svg_escape(category_label)}</text>'
        )
        for series_index, (series_label, values, color) in enumerate(series):
            value = values[row_index]
            bar_width = 0 if max_value == 0 else (value / max_value) * plot_width
            bar_y = y + series_index * (bar_height + group_gap)
            parts.append(
                f'<rect x="{left_margin}" y="{bar_y}" width="{bar_width:.2f}" height="{bar_height}" rx="4" fill="{color}"/>'
            )
            parts.append(
                f'<text x="{left_margin + bar_width + 8:.2f}" y="{bar_y + 9}" font-family="Arial, sans-serif" font-size="10" fill="#1f2321">{series_label}: {value}</text>'
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts + ["</svg>"]) + "\n", encoding="utf-8")


def build_results_memo(
    preferred_model_rows: list[dict[str, Any]],
    rendering_rows: list[dict[str, Any]],
    quality_rows: list[dict[str, Any]],
    disagreement_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, str]],
) -> str:
    preferred_map = {row["preferred_model"]: int(row["count"]) for row in preferred_model_rows}
    rendering_map = {
        row["target_rendering_strategy"]: int(row["count"]) for row in rendering_rows
    }

    acceptable_counts = {
        model_name: sum(
            row["human_acceptance_label"] == "acceptable"
            for row in comparison_rows
            if row["model_name"] == model_name
        )
        for model_name in MODEL_ORDER
    }
    borderline_counts = {
        model_name: sum(
            row["human_acceptance_label"] == "borderline"
            for row in comparison_rows
            if row["model_name"] == model_name
        )
        for model_name in MODEL_ORDER
    }
    unacceptable_counts = {
        model_name: sum(
            row["human_acceptance_label"] == "unacceptable"
            for row in comparison_rows
            if row["model_name"] == model_name
        )
        for model_name in MODEL_ORDER
    }

    quality_map = {
        (row["model_name"], row["quality_label"]): int(row["count"]) for row in quality_rows
    }

    disagreement_top: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in disagreement_rows:
        disagreement_top[row["model_name"]].append(row)
    for model_name in disagreement_top:
        disagreement_top[model_name].sort(
            key=lambda row: (-float(row["disagreement_rate"]), row["primary_entity_type"])
        )

    lines = [
        "# Results Memo",
        "",
        "This note summarizes the main findings from the completed 200-example Korean human evaluation subset.",
        "",
        "## What We Can Claim",
        "",
        "Current automatic evaluation methods do not fully capture entity fidelity in English-to-Korean translation.",
        "The strongest evidence is that many outputs judged acceptable by Korean annotators are still penalized by either general MT metrics or mention-match metrics, especially when Korean requires a rendering-strategy choice rather than a literal surface match.",
        "",
        "## Human Annotation Coverage",
        "",
        "- Annotated examples: 200",
        "- Model-output judgments: 400",
        "- Annotators: 2 (non-overlapping split)",
        "",
        "## Human Preference Snapshot",
        "",
        f"- Preferred `gpt4o`: {preferred_map.get('gpt4o', 0)}",
        f"- Preferred `gpt4o_mini`: {preferred_map.get('gpt4o_mini', 0)}",
        f"- Ties: {preferred_map.get('tie', 0)}",
        f"- Neither model preferred: {preferred_map.get('neither', 0)}",
        "",
        "## Korean Rendering Strategy Snapshot",
        "",
        f"- `translate`: {rendering_map.get('translate', 0)}",
        f"- `transliterate`: {rendering_map.get('transliterate', 0)}",
        f"- `adapt`: {rendering_map.get('adapt', 0)}",
        f"- `preserve`: {rendering_map.get('preserve', 0)}",
        "",
        "## Model-Level Human Outcomes",
        "",
        f"- `gpt4o`: acceptable {acceptable_counts['gpt4o']}, borderline {borderline_counts['gpt4o']}, unacceptable {unacceptable_counts['gpt4o']}",
        f"- `gpt4o_mini`: acceptable {acceptable_counts['gpt4o_mini']}, borderline {borderline_counts['gpt4o_mini']}, unacceptable {unacceptable_counts['gpt4o_mini']}",
        "",
        "## Error Pattern Snapshot",
        "",
        f"- `gpt4o` `correct`: {quality_map.get(('gpt4o', 'correct'), 0)}",
        f"- `gpt4o` `acceptable_alias`: {quality_map.get(('gpt4o', 'acceptable_alias'), 0)}",
        f"- `gpt4o` `wrong_rendering_strategy`: {quality_map.get(('gpt4o', 'wrong_rendering_strategy'), 0)}",
        f"- `gpt4o_mini` `correct`: {quality_map.get(('gpt4o_mini', 'correct'), 0)}",
        f"- `gpt4o_mini` `acceptable_alias`: {quality_map.get(('gpt4o_mini', 'acceptable_alias'), 0)}",
        f"- `gpt4o_mini` `wrong_rendering_strategy`: {quality_map.get(('gpt4o_mini', 'wrong_rendering_strategy'), 0)}",
        "",
        "## Highest-Disagreement Entity Types",
        "",
    ]

    for model_name in MODEL_ORDER:
        lines.append(f"### {model_name}")
        lines.append("")
        for row in disagreement_top[model_name][:5]:
            lines.append(
                f"- `{row['primary_entity_type']}`: disagreement rate {row['disagreement_rate']} ({row['disagreement_count']} / {row['example_count']})"
            )
        lines.append("")

    lines.extend(
        [
            "## What We Do Next",
            "",
            "1. Pull 6 to 10 representative examples from `outputs/metrics/disagreement_cases.csv`.",
            "2. Build the final report section around three stories:",
            "   - general metrics can be too harsh on acceptable Korean outputs,",
            "   - entity metrics still miss Korean rendering-strategy choices,",
            "   - `gpt4o_mini` fails more often on borderline or strategy-sensitive cases.",
            "3. Use the generated CSVs and SVGs for clean tables and figures in the write-up.",
            "",
            "## What We Do Not Need",
            "",
            "- No model training is required for the core project.",
            "- No additional large-scale machine learning experiments are required.",
            "- Extra baselines are optional only if there is time and a clear payoff.",
            "",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    human_rows = read_csv_rows(HUMAN_SHEET_PATH)
    comparison_rows = read_csv_rows(COMPARISON_PATH)

    preferred_model_rows = summarize_preferred_model(human_rows)
    rendering_rows = summarize_rendering_strategy(human_rows)
    quality_rows = summarize_quality_by_model(human_rows)
    disagreement_rows = summarize_disagreement_by_entity_type(comparison_rows)

    write_csv_rows(PREFERRED_MODEL_PATH, preferred_model_rows)
    write_csv_rows(RENDERING_STRATEGY_PATH, rendering_rows)
    write_csv_rows(QUALITY_BY_MODEL_PATH, quality_rows)
    write_csv_rows(DISAGREEMENT_ENTITY_PATH, disagreement_rows)

    write_simple_bar_svg(
        title="Preferred Model on Human-Annotated Subset",
        subtitle="Which output Korean annotators preferred for each example",
        labels=[row["preferred_model"] for row in preferred_model_rows],
        values=[int(row["count"]) for row in preferred_model_rows],
        colors=["#d0624a", "#5b7f4a", "#7c6aa6", "#8c8f91"],
        output_path=PREFERRED_MODEL_FIGURE_PATH,
    )
    write_simple_bar_svg(
        title="Korean Rendering Strategy Distribution",
        subtitle="Target rendering strategy selected by annotators for each example",
        labels=[row["target_rendering_strategy"] for row in rendering_rows],
        values=[int(row["count"]) for row in rendering_rows],
        colors=["#d0624a", "#5b7f4a", "#7c6aa6", "#8c8f91"],
        output_path=RENDERING_STRATEGY_FIGURE_PATH,
    )

    quality_order = [
        "correct",
        "acceptable_alias",
        "partial_entity_error",
        "wrong_rendering_strategy",
        "incorrect_entity",
        "hallucinated_entity",
        "omitted_entity",
    ]
    quality_map = {(row["model_name"], row["quality_label"]): int(row["count"]) for row in quality_rows}
    write_grouped_bar_svg(
        title="Human Quality Labels by Model",
        subtitle="Counts of Korean human judgments for each quality category",
        category_labels=quality_order,
        series=[
            (
                "gpt4o",
                [quality_map.get(("gpt4o", label), 0) for label in quality_order],
                MODEL_COLORS["gpt4o"],
            ),
            (
                "gpt4o_mini",
                [quality_map.get(("gpt4o_mini", label), 0) for label in quality_order],
                MODEL_COLORS["gpt4o_mini"],
            ),
        ],
        output_path=QUALITY_BY_MODEL_FIGURE_PATH,
    )

    RESULTS_MEMO_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_MEMO_PATH.write_text(
        build_results_memo(
            preferred_model_rows=preferred_model_rows,
            rendering_rows=rendering_rows,
            quality_rows=quality_rows,
            disagreement_rows=disagreement_rows,
            comparison_rows=comparison_rows,
        ),
        encoding="utf-8",
    )

    print(f"Saved {PREFERRED_MODEL_PATH.relative_to(ROOT)}")
    print(f"Saved {RENDERING_STRATEGY_PATH.relative_to(ROOT)}")
    print(f"Saved {QUALITY_BY_MODEL_PATH.relative_to(ROOT)}")
    print(f"Saved {DISAGREEMENT_ENTITY_PATH.relative_to(ROOT)}")
    print(f"Saved {PREFERRED_MODEL_FIGURE_PATH.relative_to(ROOT)}")
    print(f"Saved {RENDERING_STRATEGY_FIGURE_PATH.relative_to(ROOT)}")
    print(f"Saved {QUALITY_BY_MODEL_FIGURE_PATH.relative_to(ROOT)}")
    print(f"Saved {RESULTS_MEMO_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
