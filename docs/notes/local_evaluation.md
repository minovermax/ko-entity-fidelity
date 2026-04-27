# Local Evaluation Plan

The original EA-MT Korean hidden test file does not include target references, and the CodaBench phases are no longer active. For the course report, we therefore use a local held-out split from the Korean validation data, which does include references.

## Split Setup

- Source file: `data/processed/validation_ko_with_baselines.jsonl`
- Local dev: `data/processed/local_dev_ko_with_baselines.jsonl`
- Local test: `data/processed/local_test_ko_with_baselines.jsonl`
- Split script: `src/analysis/build_local_eval_splits.py`
- Method: deterministic stratified holdout by primary entity type
- Seed: `4650`
- Local dev size: 595 examples
- Local test size: 150 examples

The original hidden test file remains useful only for submission-format prediction generation. It cannot be scored locally because `data/processed/test_ko.jsonl` has no target translations.

## Generated Outputs

- `data/processed/local_eval_split_summary.json`
- `outputs/metrics/local_eval_split_counts.csv`
- `outputs/metrics/local_dev_all_models_general_metrics_overall.csv`
- `outputs/metrics/local_dev_all_models_entity_metrics_overall.csv`
- `outputs/metrics/local_test_all_models_general_metrics_overall.csv`
- `outputs/metrics/local_test_all_models_entity_metrics_overall.csv`
- `outputs/metrics/local_eval_model_summary.csv`

## Current Local Test Results

| model | BLEU | avg chrF | any-reference mention match |
| --- | ---: | ---: | ---: |
| `gpt4o` | 30.6223 | 56.8152 | 0.4933 |
| `gpt4o_mini` | 25.3421 | 55.1993 | 0.3800 |
| `entity_aware_mt` | 20.0075 | 44.5816 | 0.3333 |
| `vanilla_mt` | 11.6502 | 32.8370 | 0.0733 |

Main takeaway:

- `gpt4o` is strongest overall on local held-out automatic metrics.
- `gpt4o_mini` remains second overall.
- `entity_aware_mt` is weaker than GPT systems, but much stronger than `vanilla_mt` on entity mention fidelity.
- `vanilla_mt` is the weakest baseline, especially for Korean entity mentions.

## Rerun Commands

From the repo root:

```bash
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

## Report Language

Use wording like this:

> The official Korean hidden test set contains no released targets in our downloaded data, and the original CodaBench evaluation phases are closed. We therefore report automatic metrics on a deterministic local dev/test split constructed from the Korean validation set, stratified by primary entity type. The local test split is held out from analysis and used only for final automatic metric reporting.

Do not call this the official SemEval hidden test result.
