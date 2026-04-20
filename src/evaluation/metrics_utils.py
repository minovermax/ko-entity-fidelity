#!/usr/bin/env python3
"""Shared utilities for lightweight MT and entity metrics."""

from __future__ import annotations

import csv
import json
import math
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: stringify(value) for key, value in row.items()})


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


def whitespace_tokens(text: str) -> list[str]:
    return [token for token in text.strip().split() if token]


def count_ngrams(tokens: list[str], order: int) -> Counter[tuple[str, ...]]:
    counter: Counter[tuple[str, ...]] = Counter()
    if len(tokens) < order:
        return counter
    for index in range(len(tokens) - order + 1):
        counter[tuple(tokens[index : index + order])] += 1
    return counter


def modified_precision(candidate_tokens: list[str], reference_tokens_list: list[list[str]], order: int) -> tuple[int, int]:
    candidate_counts = count_ngrams(candidate_tokens, order)
    if not candidate_counts:
        return 0, 0

    max_ref_counts: Counter[tuple[str, ...]] = Counter()
    for reference_tokens in reference_tokens_list:
        ref_counts = count_ngrams(reference_tokens, order)
        for ngram, count in ref_counts.items():
            max_ref_counts[ngram] = max(max_ref_counts[ngram], count)

    clipped = sum(min(count, max_ref_counts[ngram]) for ngram, count in candidate_counts.items())
    total = sum(candidate_counts.values())
    return clipped, total


def best_reference_length(candidate_length: int, reference_lengths: Iterable[int]) -> int:
    return min(reference_lengths, key=lambda ref_len: (abs(ref_len - candidate_length), ref_len))


def corpus_bleu(candidate_texts: list[str], reference_text_sets: list[list[str]], max_order: int = 4) -> float:
    clipped_totals = [0] * max_order
    total_totals = [0] * max_order
    candidate_length_total = 0
    reference_length_total = 0

    for candidate_text, reference_texts in zip(candidate_texts, reference_text_sets):
        candidate_tokens = whitespace_tokens(candidate_text)
        reference_tokens_list = [whitespace_tokens(reference) for reference in reference_texts if reference]
        if not reference_tokens_list:
            continue

        candidate_length_total += len(candidate_tokens)
        reference_length_total += best_reference_length(
            len(candidate_tokens), [len(tokens) for tokens in reference_tokens_list]
        )

        for order in range(1, max_order + 1):
            clipped, total = modified_precision(candidate_tokens, reference_tokens_list, order)
            clipped_totals[order - 1] += clipped
            total_totals[order - 1] += total

    precisions: list[float] = []
    for clipped, total in zip(clipped_totals, total_totals):
        if total == 0:
            precisions.append(0.0)
        else:
            precisions.append((clipped + 1.0) / (total + 1.0))

    if not candidate_length_total:
        return 0.0
    if any(precision == 0.0 for precision in precisions):
        return 0.0

    brevity_penalty = 1.0
    if candidate_length_total < reference_length_total:
        brevity_penalty = math.exp(1 - (reference_length_total / candidate_length_total))

    score = brevity_penalty * math.exp(sum(math.log(p) for p in precisions) / max_order)
    return 100.0 * score


def sentence_bleu(candidate_text: str, reference_texts: list[str], max_order: int = 4) -> float:
    return corpus_bleu([candidate_text], [reference_texts], max_order=max_order)


def char_ngrams(text: str, order: int) -> Counter[str]:
    counter: Counter[str] = Counter()
    if len(text) < order:
        return counter
    for index in range(len(text) - order + 1):
        counter[text[index : index + order]] += 1
    return counter


def chrf_score(candidate_text: str, reference_texts: list[str], max_order: int = 6, beta: float = 2.0) -> float:
    candidate_text = "".join(candidate_text.split())
    references = ["".join(reference.split()) for reference in reference_texts if reference]
    if not references:
        return 0.0

    beta_sq = beta * beta
    best_score = 0.0
    for reference in references:
        order_scores: list[float] = []
        for order in range(1, max_order + 1):
            candidate_counts = char_ngrams(candidate_text, order)
            reference_counts = char_ngrams(reference, order)

            if not candidate_counts and not reference_counts:
                order_scores.append(1.0)
                continue
            if not candidate_counts or not reference_counts:
                order_scores.append(0.0)
                continue

            overlap = sum(
                min(candidate_counts[ngram], reference_counts[ngram])
                for ngram in candidate_counts
            )
            precision = overlap / max(sum(candidate_counts.values()), 1)
            recall = overlap / max(sum(reference_counts.values()), 1)
            if precision == 0.0 and recall == 0.0:
                order_scores.append(0.0)
            else:
                order_scores.append(
                    (1 + beta_sq) * precision * recall / ((beta_sq * precision) + recall)
                )

        best_score = max(best_score, sum(order_scores) / max_order)

    return 100.0 * best_score


def normalized_exact_match(prediction: str, references: list[str]) -> bool:
    normalized_prediction = normalize_text(prediction)
    return any(normalized_prediction == normalize_text(reference) for reference in references if reference)


def longest_common_substring_length(text_a: str, text_b: str) -> int:
    if not text_a or not text_b:
        return 0
    previous = [0] * (len(text_b) + 1)
    best = 0
    for char_a in text_a:
        current = [0]
        for index, char_b in enumerate(text_b, start=1):
            if char_a == char_b:
                value = previous[index - 1] + 1
                current.append(value)
                best = max(best, value)
            else:
                current.append(0)
        previous = current
    return best
