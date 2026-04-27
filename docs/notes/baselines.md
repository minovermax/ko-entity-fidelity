# Baseline Notes

## What Was Added

Two lightweight lecture-aligned baselines are now implemented under `src/baselines/`:

1. `run_vanilla_mt.py`
   - plain pretrained multilingual MT baseline
   - default model: `facebook/m2m100_418M`

2. `run_entity_aware_baseline.py`
   - entity-aware baseline using Wikidata English/Korean labels
   - rewrites the English source by replacing the detected English entity label with a Korean Wikidata label before MT
   - then translates the rewritten source with the same multilingual model

This second baseline is not a paid-API prompt baseline.
It plays the same conceptual role as an entity-aware translation baseline, but stays local, reproducible, and easy to rerun.

## Why This Is Reasonable For The Project

- It uses pretrained neural MT, which connects clearly to lecture material.
- It adds an entity-aware mechanism without requiring full fine-tuning.
- It stays aligned with the project scope: evaluation and analysis, not heavy training.

## Main Files

- `src/baselines/baseline_utils.py`
- `src/baselines/run_vanilla_mt.py`
- `src/baselines/run_entity_aware_baseline.py`
- `data/processed/validation_ko_with_baselines.jsonl`

## Outputs

Translations:

- `outputs/translations/validation_ko_vanilla_mt_predictions.jsonl`
- `outputs/translations/validation_ko_vanilla_mt_predictions.csv`
- `outputs/translations/validation_ko_entity_aware_mt_predictions.jsonl`
- `outputs/translations/validation_ko_entity_aware_mt_predictions.csv`

Automatic metrics across GPT + baseline models:

- `outputs/metrics/all_models_general_metrics_overall.csv`
- `outputs/metrics/all_models_general_metrics_by_example.csv`
- `outputs/metrics/all_models_general_metrics_by_entity_type.csv`
- `outputs/metrics/all_models_entity_metrics_overall.csv`
- `outputs/metrics/all_models_entity_metrics_by_example.csv`
- `outputs/metrics/all_models_entity_metrics_by_entity_type.csv`

Local dev/test evaluation outputs:

- `data/processed/local_dev_ko_with_baselines.jsonl`
- `data/processed/local_test_ko_with_baselines.jsonl`
- `outputs/metrics/local_eval_model_summary.csv`

## Rerun Commands

From repo root:

```bash
python3 src/baselines/run_vanilla_mt.py --batch-size 64
python3 src/baselines/run_entity_aware_baseline.py --batch-size 64
python3 src/evaluation/run_general_metrics.py \
  --input-path data/processed/validation_ko_with_baselines.jsonl \
  --output-prefix all_models
python3 src/evaluation/run_entity_metrics.py \
  --input-path data/processed/validation_ko_with_baselines.jsonl \
  --output-prefix all_models

python3 src/analysis/build_local_eval_splits.py
python3 src/evaluation/run_general_metrics.py \
  --input-path data/processed/local_dev_ko_with_baselines.jsonl \
  --output-prefix local_dev_all_models
python3 src/evaluation/run_entity_metrics.py \
  --input-path data/processed/local_dev_ko_with_baselines.jsonl \
  --output-prefix local_dev_all_models
python3 src/evaluation/run_general_metrics.py \
  --input-path data/processed/local_test_ko_with_baselines.jsonl \
  --output-prefix local_test_all_models
python3 src/evaluation/run_entity_metrics.py \
  --input-path data/processed/local_test_ko_with_baselines.jsonl \
  --output-prefix local_test_all_models
python3 src/analysis/build_local_eval_summary.py
```

## Current Top-Line Results

General MT metrics on Korean validation:

- `gpt4o`: BLEU `25.8746`, avg chrF `54.6224`
- `gpt4o_mini`: BLEU `20.7067`, avg chrF `52.3392`
- `entity_aware_mt`: BLEU `20.5896`, avg chrF `45.1523`
- `vanilla_mt`: BLEU `11.0663`, avg chrF `32.8703`

Entity-sensitive metrics on Korean validation:

- `gpt4o`: any-reference normalized mention match `0.5007`
- `gpt4o_mini`: any-reference normalized mention match `0.3678`
- `entity_aware_mt`: any-reference normalized mention match `0.4483`
- `vanilla_mt`: any-reference normalized mention match `0.0966`

Local held-out test metrics:

- `gpt4o`: BLEU `30.6223`, avg chrF `56.8152`, any-reference normalized mention match `0.4933`
- `gpt4o_mini`: BLEU `25.3421`, avg chrF `55.1993`, any-reference normalized mention match `0.38`
- `entity_aware_mt`: BLEU `20.0075`, avg chrF `44.5816`, any-reference normalized mention match `0.3333`
- `vanilla_mt`: BLEU `11.6502`, avg chrF `32.837`, any-reference normalized mention match `0.0733`

## Interpretation

- The plain pretrained MT baseline is much weaker than the GPT systems, especially on entity mention fidelity.
- The entity-aware baseline recovers a large amount of entity performance relative to the plain MT baseline.
- The entity-aware baseline gets close to `gpt4o` on mention-oriented metrics, even though its sentence-level fluency remains weaker.

That is useful for the final story:

- entity awareness clearly matters
- generic MT alone is not enough
- even simple label-aware interventions can strongly improve entity fidelity
- but strong overall translation quality still matters beyond entity injection
