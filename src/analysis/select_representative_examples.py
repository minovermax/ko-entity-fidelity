#!/usr/bin/env python3
"""Select qualitative examples for the final report."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "outputs" / "metrics" / "disagreement_cases.csv"
OUTPUT_CSV_PATH = ROOT / "outputs" / "metrics" / "representative_examples.csv"
OUTPUT_MD_PATH = ROOT / "docs" / "notes" / "representative_examples.md"

RowFilter = Callable[[dict[str, str]], bool]


BUCKETS: list[tuple[str, str, RowFilter]] = [
    (
        "Acceptable alias penalized by entity metric",
        "A Korean-valid alias or variant is acceptable to humans but fails strict mention matching.",
        lambda row: row["human_quality_label"] == "acceptable_alias"
        and row["any_reference_mention_normalized_match"] == "False",
    ),
    (
        "General metric too harsh",
        "The translation is human-acceptable, but chrF/BLEU-style overlap is low.",
        lambda row: row["disagreement_category"] == "general_metric_too_harsh_on_acceptable_output",
    ),
    (
        "Both metrics too harsh",
        "Both general and entity metrics reject an output that Korean annotation accepts.",
        lambda row: row["disagreement_category"] == "both_metrics_too_harsh_on_acceptable_output",
    ),
    (
        "Wrong Korean rendering strategy",
        "The entity is recognizable, but the Korean form is judged to use the wrong rendering strategy.",
        lambda row: row["korean_strategy_issue"] == "True",
    ),
    (
        "Adaptation needed",
        "The case needs Korean cultural/title adaptation rather than direct translation alone.",
        lambda row: row["adaptation_needed"] == "yes",
    ),
    (
        "Preserve-English case",
        "Acronyms or source forms may be better preserved in Korean context.",
        lambda row: row["preserve_english_preferred"] == "yes",
    ),
    (
        "Metric misses human rejection",
        "An automatic metric passes an output that humans reject.",
        lambda row: "miss_human_rejection" in row["disagreement_category"],
    ),
    (
        "Borderline strategy-sensitive case",
        "The output is not simply right or wrong; entity strategy is the issue.",
        lambda row: row["disagreement_category"] == "borderline_human_general_pass_entity_fail",
    ),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def score_candidate(row: dict[str, str]) -> tuple[float, float, str]:
    chrf = float(row["sentence_chrf"])
    mention_recall = float(row["mention_substring_recall_proxy"])
    return (abs(50.0 - chrf), -mention_recall, row["id"])


def select_examples(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    used_ids: set[tuple[str, str]] = set()
    for bucket_name, bucket_reason, row_filter in BUCKETS:
        candidates = [
            row for row in rows if row_filter(row) and (row["id"], row["model_name"]) not in used_ids
        ]
        if not candidates:
            continue
        candidates.sort(key=score_candidate)
        chosen = dict(candidates[0])
        chosen["example_bucket"] = bucket_name
        chosen["why_this_example"] = bucket_reason
        selected.append(chosen)
        used_ids.add((chosen["id"], chosen["model_name"]))
    return selected


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines = [
        "# Representative Examples",
        "",
        "These examples are selected from `outputs/metrics/disagreement_cases.csv` for the final report discussion.",
        "",
    ]
    for index, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"## {index}. {row['example_bucket']}",
                "",
                f"- id: `{row['id']}`",
                f"- model: `{row['model_name']}`",
                f"- entity type: `{row['primary_entity_type']}`",
                f"- source: {row['source']}",
                f"- reference: {row['reference_translation']}",
                f"- reference mention: `{row['reference_mention']}`",
                f"- prediction: {row['prediction']}",
                f"- human label: `{row['human_acceptance_label']}` / `{row['human_quality_label']}`",
                f"- automatic pattern: `{row['disagreement_category']}`",
                f"- why it matters: {row['why_this_example']}",
                "",
            ]
        )
    OUTPUT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = read_csv(INPUT_PATH)
    selected = select_examples(rows)
    write_csv(OUTPUT_CSV_PATH, selected)
    write_markdown(selected)
    print(f"Saved {OUTPUT_CSV_PATH.relative_to(ROOT)}")
    print(f"Saved {OUTPUT_MD_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
