#!/usr/bin/env python3
"""Build a reproducible Korean analysis subset from validation data."""

from __future__ import annotations

import csv
import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data" / "processed" / "validation_ko_merged.jsonl"
OUTPUT_JSONL_PATH = ROOT / "data" / "processed" / "ko_analysis_subset.jsonl"
OUTPUT_CSV_PATH = ROOT / "data" / "processed" / "ko_analysis_subset.csv"
SUMMARY_PATH = ROOT / "data" / "processed" / "ko_analysis_subset_summary.json"

SUBSET_SIZE = 200
RANDOM_SEED = 42
SEED_PER_PRIMARY_ENTITY_TYPE = 6
HARD_CASE_FRACTION = 0.6
EASY_CASE_FRACTION = 0.2


ASCII_LETTER_RE = re.compile(r"[A-Za-z]")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        writer.writeheader()
        for record in records:
            writer.writerow({key: stringify(value) for key, value in record.items()})


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    normalized_chars: list[str] = []
    for char in text.lower():
        category = unicodedata.category(char)
        if char.isspace() or category.startswith("P") or category.startswith("S"):
            continue
        normalized_chars.append(char)
    return "".join(normalized_chars)


def contains_any_mention_normalized(prediction: str, mentions: list[str]) -> bool:
    normalized_prediction = normalize_text(prediction)
    return any(normalize_text(mention) in normalized_prediction for mention in mentions if mention)


def compute_selection_metadata(record: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    entity_types = record.get("entity_types") or []
    primary_entity_type = entity_types[0] if entity_types else "Unknown"
    reference_mentions = record.get("reference_mentions") or []
    gpt4o_prediction = record.get("gpt4o_prediction", "")
    gpt4o_mini_prediction = record.get("gpt4o_mini_prediction", "")

    gpt4o_normalized = normalize_text(gpt4o_prediction)
    gpt4o_mini_normalized = normalize_text(gpt4o_mini_prediction)
    predictions_differ = gpt4o_normalized != gpt4o_mini_normalized

    gpt4o_any_mention_match = contains_any_mention_normalized(gpt4o_prediction, reference_mentions)
    gpt4o_mini_any_mention_match = contains_any_mention_normalized(
        gpt4o_mini_prediction, reference_mentions
    )
    mention_match_disagree = gpt4o_any_mention_match != gpt4o_mini_any_mention_match
    one_model_misses_reference_mention = not (gpt4o_any_mention_match and gpt4o_mini_any_mention_match)
    multi_reference = len(record.get("reference_translations") or []) > 1
    multi_entity_type = len(entity_types) > 1
    ascii_preservation_disagree = bool(ASCII_LETTER_RE.search(gpt4o_prediction)) != bool(
        ASCII_LETTER_RE.search(gpt4o_mini_prediction)
    )

    selection_score = 0
    selection_reasons: list[str] = []

    if predictions_differ:
        selection_score += 3
        selection_reasons.append("model_text_disagreement")
    if mention_match_disagree:
        selection_score += 4
        selection_reasons.append("entity_mention_match_disagreement")
    if one_model_misses_reference_mention:
        selection_score += 2
        selection_reasons.append("at_least_one_model_misses_reference_mention")
    if multi_reference:
        selection_score += 1
        selection_reasons.append("multi_reference_example")
    if multi_entity_type:
        selection_score += 1
        selection_reasons.append("multiple_entity_types")
    if ascii_preservation_disagree:
        selection_score += 1
        selection_reasons.append("ascii_preservation_disagreement")
    if not selection_reasons:
        selection_reasons.append("entity_type_coverage")

    enriched = dict(record)
    enriched["primary_entity_type"] = primary_entity_type
    enriched["selection_score"] = selection_score
    enriched["selection_reasons"] = selection_reasons
    enriched["gpt_models_differ"] = predictions_differ
    enriched["gpt4o_any_reference_mention_match"] = gpt4o_any_mention_match
    enriched["gpt4o_mini_any_reference_mention_match"] = gpt4o_mini_any_mention_match
    enriched["model_mention_match_disagree"] = mention_match_disagree
    enriched["multi_reference_example"] = multi_reference
    enriched["ascii_preservation_disagreement"] = ascii_preservation_disagree
    enriched["_random_tiebreaker"] = rng.random()
    return enriched


def round_robin_pick(
    ordered_entity_types: list[str],
    buckets: dict[str, list[dict[str, Any]]],
    cursors: dict[str, int],
    selected: list[dict[str, Any]],
    selected_ids: set[str],
    target_total: int,
    stage_name: str,
    per_type_limit: int | None = None,
) -> None:
    per_type_counts = Counter()

    while len(selected) < target_total:
        added_in_round = False
        for entity_type in ordered_entity_types:
            if per_type_limit is not None and per_type_counts[entity_type] >= per_type_limit:
                continue

            index = cursors[entity_type]
            while index < len(buckets[entity_type]) and buckets[entity_type][index]["id"] in selected_ids:
                index += 1
            cursors[entity_type] = index

            if index >= len(buckets[entity_type]):
                continue

            candidate = dict(buckets[entity_type][index])
            cursors[entity_type] += 1
            if candidate["id"] in selected_ids:
                continue

            candidate["selection_stage"] = stage_name
            selected.append(candidate)
            selected_ids.add(candidate["id"])
            per_type_counts[entity_type] += 1
            added_in_round = True

            if len(selected) >= target_total:
                break

        if not added_in_round:
            break


def select_subset(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(RANDOM_SEED)
    enriched_records = [compute_selection_metadata(record, rng) for record in records]

    desc_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in enriched_records:
        desc_buckets[record["primary_entity_type"]].append(record)

    ordered_entity_types = sorted(desc_buckets)
    for entity_type in ordered_entity_types:
        desc_buckets[entity_type].sort(
            key=lambda record: (
                -record["selection_score"],
                -int(record["gpt_models_differ"]),
                -int(record["model_mention_match_disagree"]),
                record["_random_tiebreaker"],
                record["id"],
            )
        )

    asc_buckets: dict[str, list[dict[str, Any]]] = {
        entity_type: sorted(
            desc_buckets[entity_type],
            key=lambda record: (
                record["selection_score"],
                int(record["model_mention_match_disagree"]),
                record["_random_tiebreaker"],
                record["id"],
            ),
        )
        for entity_type in ordered_entity_types
    }
    random_buckets: dict[str, list[dict[str, Any]]] = {
        entity_type: list(desc_buckets[entity_type]) for entity_type in ordered_entity_types
    }
    for entity_type in ordered_entity_types:
        rng.shuffle(random_buckets[entity_type])

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    max_total = min(SUBSET_SIZE, len(records))

    desc_cursors = {entity_type: 0 for entity_type in ordered_entity_types}
    asc_cursors = {entity_type: 0 for entity_type in ordered_entity_types}
    random_cursors = {entity_type: 0 for entity_type in ordered_entity_types}

    hard_target = min(max_total, max(int(SUBSET_SIZE * HARD_CASE_FRACTION), len(ordered_entity_types)))
    easy_target = min(max_total, hard_target + int(SUBSET_SIZE * EASY_CASE_FRACTION))

    round_robin_pick(
        ordered_entity_types,
        desc_buckets,
        desc_cursors,
        selected,
        selected_ids,
        min(max_total, SEED_PER_PRIMARY_ENTITY_TYPE * len(ordered_entity_types)),
        "seed",
        per_type_limit=SEED_PER_PRIMARY_ENTITY_TYPE,
    )
    round_robin_pick(
        ordered_entity_types,
        desc_buckets,
        desc_cursors,
        selected,
        selected_ids,
        hard_target,
        "hard_case",
    )
    round_robin_pick(
        ordered_entity_types,
        asc_buckets,
        asc_cursors,
        selected,
        selected_ids,
        easy_target,
        "easy_case",
    )
    round_robin_pick(
        ordered_entity_types,
        random_buckets,
        random_cursors,
        selected,
        selected_ids,
        max_total,
        "random_fill",
    )

    return selected


def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    primary_counts = Counter(record["primary_entity_type"] for record in records)
    reason_counts = Counter(
        reason for record in records for reason in record.get("selection_reasons", [])
    )
    return {
        "input_path": str(INPUT_PATH.relative_to(ROOT)),
        "subset_size": len(records),
        "config": {
            "subset_size": SUBSET_SIZE,
            "random_seed": RANDOM_SEED,
            "seed_per_primary_entity_type": SEED_PER_PRIMARY_ENTITY_TYPE,
            "hard_case_fraction": HARD_CASE_FRACTION,
            "easy_case_fraction": EASY_CASE_FRACTION,
        },
        "primary_entity_type_counts": dict(primary_counts.most_common()),
        "selection_reason_counts": dict(reason_counts.most_common()),
        "selection_stage_counts": dict(
            Counter(record.get("selection_stage", "unknown") for record in records).most_common()
        ),
        "gpt_models_differ_count": sum(int(record["gpt_models_differ"]) for record in records),
        "model_mention_match_disagree_count": sum(
            int(record["model_mention_match_disagree"]) for record in records
        ),
        "multi_reference_count": sum(int(record["multi_reference_example"]) for record in records),
        "ascii_preservation_disagreement_count": sum(
            int(record["ascii_preservation_disagreement"]) for record in records
        ),
    }


def main() -> None:
    records = load_jsonl(INPUT_PATH)
    subset = select_subset(records)

    cleaned_subset: list[dict[str, Any]] = []
    for record in subset:
        cleaned_record = {key: value for key, value in record.items() if not key.startswith("_")}
        cleaned_subset.append(cleaned_record)

    write_jsonl(OUTPUT_JSONL_PATH, cleaned_subset)
    write_csv(OUTPUT_CSV_PATH, cleaned_subset)

    summary = build_summary(cleaned_subset)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Built subset with {len(cleaned_subset)} examples")
    print(f"Saved {OUTPUT_JSONL_PATH.relative_to(ROOT)}")
    print(f"Saved {OUTPUT_CSV_PATH.relative_to(ROOT)}")
    print(f"Saved {SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
