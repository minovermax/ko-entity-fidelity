#!/usr/bin/env python3
"""Shared helpers for baseline translation experiments."""

from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
BASE_INPUT_PATH = ROOT / "data" / "processed" / "validation_ko_merged.jsonl"
COMBINED_BASELINE_DATASET_PATH = ROOT / "data" / "processed" / "validation_ko_with_baselines.jsonl"
TRANSLATION_OUTPUT_DIR = ROOT / "outputs" / "translations"
WIKIDATA_CACHE_PATH = ROOT / "data" / "processed" / "wikidata_entity_labels.json"

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_BATCH_SIZE = 50


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: stringify(value) for key, value in row.items()})


def chunked(items: list[str], chunk_size: int) -> list[list[str]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def load_transformers():
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing transformers dependencies. Install with: "
            "python3 -m pip install transformers sentencepiece torch"
        ) from exc
    return AutoTokenizer, AutoModelForSeq2SeqLM


def load_translation_model(model_name: str):
    AutoTokenizer, AutoModelForSeq2SeqLM = load_transformers()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model


def resolve_lang_code(tokenizer: Any, lang_code: str) -> str:
    class_name = tokenizer.__class__.__name__.lower()
    if "nllb" in class_name:
        mapping = {"en": "eng_Latn", "ko": "kor_Hang"}
        return mapping.get(lang_code, lang_code)
    return lang_code


def translate_texts(
    texts: list[str],
    model_name: str,
    batch_size: int = 8,
    max_new_tokens: int = 128,
    src_lang: str = "en",
    tgt_lang: str = "ko",
) -> list[str]:
    tokenizer, model = load_translation_model(model_name)
    resolved_src_lang = resolve_lang_code(tokenizer, src_lang)
    resolved_tgt_lang = resolve_lang_code(tokenizer, tgt_lang)

    tokenizer_class = tokenizer.__class__.__name__.lower()
    if hasattr(tokenizer, "src_lang") and ("m2m100" in tokenizer_class or "nllb" in tokenizer_class):
        tokenizer.src_lang = resolved_src_lang

    predictions: list[str] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        encoded = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
        generate_kwargs: dict[str, Any] = {"max_new_tokens": max_new_tokens, "max_length": None}

        if "m2m100" in tokenizer_class:
            generate_kwargs["forced_bos_token_id"] = tokenizer.get_lang_id(resolved_tgt_lang)
        elif "nllb" in tokenizer_class:
            if hasattr(tokenizer, "lang_code_to_id"):
                generate_kwargs["forced_bos_token_id"] = tokenizer.lang_code_to_id[resolved_tgt_lang]
            else:
                generate_kwargs["forced_bos_token_id"] = tokenizer.convert_tokens_to_ids(resolved_tgt_lang)

        generated = model.generate(**encoded, **generate_kwargs)
        predictions.extend(tokenizer.batch_decode(generated, skip_special_tokens=True))
    return predictions


def load_wikidata_cache(cache_path: Path = WIKIDATA_CACHE_PATH) -> dict[str, dict[str, Any]]:
    if not cache_path.exists():
        return {}
    return json.loads(cache_path.read_text(encoding="utf-8"))


def save_wikidata_cache(cache: dict[str, dict[str, Any]], cache_path: Path = WIKIDATA_CACHE_PATH) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def fetch_wikidata_entities(
    wikidata_ids: list[str],
    cache_path: Path = WIKIDATA_CACHE_PATH,
    sleep_seconds: float = 0.1,
) -> dict[str, dict[str, Any]]:
    cache = load_wikidata_cache(cache_path)
    ids_to_fetch = [wikidata_id for wikidata_id in wikidata_ids if wikidata_id and wikidata_id not in cache]

    for batch in chunked(ids_to_fetch, WIKIDATA_BATCH_SIZE):
        params = {
            "action": "wbgetentities",
            "format": "json",
            "ids": "|".join(batch),
            "languages": "en|ko",
            "props": "labels|aliases",
        }
        request = Request(
            f"{WIKIDATA_API}?{urlencode(params)}",
            headers={"User-Agent": "ko-entity-fidelity-baseline/1.0"},
        )
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        for wikidata_id, entity in payload.get("entities", {}).items():
            labels = entity.get("labels", {})
            aliases = entity.get("aliases", {})
            cache[wikidata_id] = {
                "label_en": labels.get("en", {}).get("value", ""),
                "label_ko": labels.get("ko", {}).get("value", ""),
                "aliases_en": [item.get("value", "") for item in aliases.get("en", []) if item.get("value")],
                "aliases_ko": [item.get("value", "") for item in aliases.get("ko", []) if item.get("value")],
            }
        if sleep_seconds:
            time.sleep(sleep_seconds)

    save_wikidata_cache(cache, cache_path)
    return cache


def unique_in_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        stripped = value.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            ordered.append(stripped)
    return ordered


def pick_korean_entity_label(entity_info: dict[str, Any]) -> tuple[str, str]:
    label_ko = str(entity_info.get("label_ko", "")).strip()
    aliases_ko = unique_in_order(str(value) for value in entity_info.get("aliases_ko", []))
    label_en = str(entity_info.get("label_en", "")).strip()

    if label_ko:
        return label_ko, "wikidata_ko_label"
    if aliases_ko:
        return aliases_ko[0], "wikidata_ko_alias"
    if label_en:
        return label_en, "fallback_en_label"
    return "", "missing_entity_label"


def english_entity_candidates(entity_info: dict[str, Any]) -> list[str]:
    label_en = str(entity_info.get("label_en", "")).strip()
    aliases_en = unique_in_order(str(value) for value in entity_info.get("aliases_en", []))
    candidates = unique_in_order([label_en, *aliases_en])
    candidates.sort(key=len, reverse=True)
    return [candidate for candidate in candidates if len(candidate) >= 3]


def replace_case_insensitive(source: str, target: str, replacement: str) -> tuple[str, bool]:
    if not target:
        return source, False
    pattern = re.compile(re.escape(target), flags=re.IGNORECASE)
    updated, count = pattern.subn(replacement, source, count=1)
    return updated, count > 0


def build_entity_aware_source(
    source: str,
    entity_info: dict[str, Any],
) -> dict[str, Any]:
    replacement_text, replacement_origin = pick_korean_entity_label(entity_info)
    label_en = str(entity_info.get("label_en", "")).strip()
    candidates = english_entity_candidates(entity_info)

    if not replacement_text:
        return {
            "rewritten_source": source,
            "rewrite_applied": False,
            "matched_source_entity": "",
            "replacement_text": "",
            "replacement_origin": replacement_origin,
            "entity_label_en": label_en,
            "entity_label_ko": str(entity_info.get("label_ko", "")).strip(),
        }

    for candidate in candidates:
        rewritten_source, replaced = replace_case_insensitive(source, candidate, replacement_text)
        if replaced:
            return {
                "rewritten_source": rewritten_source,
                "rewrite_applied": True,
                "matched_source_entity": candidate,
                "replacement_text": replacement_text,
                "replacement_origin": replacement_origin,
                "entity_label_en": label_en,
                "entity_label_ko": str(entity_info.get("label_ko", "")).strip(),
            }

    return {
        "rewritten_source": source,
        "rewrite_applied": False,
        "matched_source_entity": "",
        "replacement_text": replacement_text,
        "replacement_origin": replacement_origin,
        "entity_label_en": label_en,
        "entity_label_ko": str(entity_info.get("label_ko", "")).strip(),
    }


def write_prediction_artifacts(
    output_stem: str,
    rows: list[dict[str, Any]],
) -> tuple[Path, Path]:
    jsonl_path = TRANSLATION_OUTPUT_DIR / f"{output_stem}.jsonl"
    csv_path = TRANSLATION_OUTPUT_DIR / f"{output_stem}.csv"
    write_jsonl(jsonl_path, rows)
    write_csv(csv_path, rows)
    return jsonl_path, csv_path


def update_combined_baseline_dataset(
    prediction_field: str,
    prediction_rows: list[dict[str, Any]],
    base_input_path: Path = BASE_INPUT_PATH,
    output_path: Path = COMBINED_BASELINE_DATASET_PATH,
) -> Path:
    if output_path.exists():
        records = load_jsonl(output_path)
    else:
        records = load_jsonl(base_input_path)

    prediction_map = {row["id"]: row["prediction"] for row in prediction_rows}
    for record in records:
        record[prediction_field] = prediction_map.get(record["id"], "")

    write_jsonl(output_path, records)
    return output_path
