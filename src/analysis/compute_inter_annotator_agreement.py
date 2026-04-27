#!/usr/bin/env python3
"""Compute simple inter-annotator agreement on the optional overlap set."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OVERLAP_EXPORT_DIR = ROOT / "data" / "human_eval" / "overlap" / "annotator_exports"
OUTPUT_CSV_PATH = ROOT / "outputs" / "metrics" / "inter_annotator_agreement.csv"
OUTPUT_MD_PATH = ROOT / "docs" / "notes" / "inter_annotator_agreement.md"

ANNOTATOR_PATHS = {
    "minseo": OVERLAP_EXPORT_DIR / "minseo_annotations.csv",
    "siwan": OVERLAP_EXPORT_DIR / "siwan_annotations.csv",
}

FIELDS_TO_SCORE = [
    "target_rendering_strategy",
    "official_korean_title_preferred",
    "preserve_english_preferred",
    "adaptation_needed",
    "gpt4o_entity_correct",
    "gpt4o_rendering_strategy",
    "gpt4o_quality_label",
    "gpt4o_metric_likely_miss",
    "gpt4o_mini_entity_correct",
    "gpt4o_mini_rendering_strategy",
    "gpt4o_mini_quality_label",
    "gpt4o_mini_metric_likely_miss",
    "preferred_model",
]


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


def cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    if not pairs:
        return 0.0
    total = len(pairs)
    observed = sum(left == right for left, right in pairs) / total

    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    labels = set(left_counts) | set(right_counts)
    expected = sum(
        (left_counts[label] / total) * (right_counts[label] / total)
        for label in labels
    )
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def main() -> None:
    missing = [path for path in ANNOTATOR_PATHS.values() if not path.exists()]
    if missing:
        missing_text = "\n".join(f"- `{path.relative_to(ROOT)}`" for path in missing)
        OUTPUT_MD_PATH.write_text(
            "# Inter-Annotator Agreement\n\n"
            "Agreement has not been computed yet because the overlap exports are missing.\n\n"
            "Missing files:\n\n"
            f"{missing_text}\n",
            encoding="utf-8",
        )
        raise SystemExit(f"Missing overlap exports:\n{missing_text}")

    rows_by_annotator = {
        slug: {row["id"]: row for row in read_csv(path)}
        for slug, path in ANNOTATOR_PATHS.items()
    }
    common_ids = sorted(set.intersection(*(set(rows) for rows in rows_by_annotator.values())))
    if not common_ids:
        raise SystemExit("No overlapping IDs found in overlap exports.")

    output_rows: list[dict[str, Any]] = []
    for field in FIELDS_TO_SCORE:
        pairs = []
        for row_id in common_ids:
            left = rows_by_annotator["minseo"][row_id].get(field, "").strip()
            right = rows_by_annotator["siwan"][row_id].get(field, "").strip()
            if left and right:
                pairs.append((left, right))
        agreement = sum(left == right for left, right in pairs)
        total = len(pairs)
        output_rows.append(
            {
                "field": field,
                "overlap_count": total,
                "agreement_count": agreement,
                "percent_agreement": round(agreement / total, 4) if total else 0.0,
                "cohen_kappa": round(cohen_kappa(pairs), 4) if total else 0.0,
            }
        )

    write_csv(OUTPUT_CSV_PATH, output_rows)

    lines = [
        "# Inter-Annotator Agreement",
        "",
        f"Overlap examples scored: {len(common_ids)}",
        "",
        "| field | agreement | kappa |",
        "| --- | ---: | ---: |",
    ]
    for row in output_rows:
        lines.append(
            f"| `{row['field']}` | {row['percent_agreement']} | {row['cohen_kappa']} |"
        )
    lines.append("")
    OUTPUT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Saved {OUTPUT_CSV_PATH.relative_to(ROOT)}")
    print(f"Saved {OUTPUT_MD_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
