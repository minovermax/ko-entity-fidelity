# Codex Issue Log

## 2026-05-01 Plan Before Analysis

Relevant files identified from the repository inventory:

- Manuscript/support sources:
  - `docs/final_report_draft.md`
  - `docs/notes/final_report_todo.md`
  - `docs/notes/results_memo.md`
  - `docs/notes/representative_examples.md`
  - `README.md`
- Processed data and human evaluation:
  - `data/processed/validation_ko_merged.jsonl`
  - `data/processed/validation_ko_with_baselines.jsonl`
  - `data/processed/local_dev_ko_with_baselines.jsonl`
  - `data/processed/local_test_ko_with_baselines.jsonl`
  - `data/human_eval/human_eval_sheet_merged.csv`
  - `data/human_eval/annotator_exports/*.csv`
  - `data/human_eval/overlap/annotator_exports/*.csv`
- Evaluation and analysis scripts:
  - `src/evaluation/run_general_metrics.py`
  - `src/evaluation/run_entity_metrics.py`
  - `src/evaluation/metrics_utils.py`
  - `src/analysis/compare_metrics_vs_human.py`
  - `src/analysis/compute_inter_annotator_agreement.py`
  - `src/analysis/build_final_report_artifacts.py`
- Existing outputs:
  - `outputs/metrics/*.csv`
  - `outputs/figures/*.svg`

Planned steps:

1. Audit processed datasets and human annotation files, recording row counts, columns, available model-output fields, and annotation fields.
2. Read metric/evaluation code and document exact implemented definitions for mention match, disagreement, normalization, and human-label binarization.
3. Add a reproducible analysis script that writes the requested CSV summaries and simple SVG figures from existing files only.
4. Run the script locally and verify that generated outputs are internally consistent with existing annotation and metric files.
5. Check local feasibility for COMET and M-ETA from installed packages/scripts and document precise blockers if they are not runnable.
6. Create `docs/paper_support.md` with exact definitions, issue notes, computed evidence, and ready-to-paste manuscript wording.

Constraints for this run:

- Do not train new models.
- Do not invent results.
- Do not claim official hidden SemEval test performance.
- Prefer reproducible scripts and CSV/SVG artifacts over notebook-only logic.

## 2026-05-01 Audit Findings

Manuscript/support source:

- Editable draft source found: `docs/final_report_draft.md`
- No `.tex`, manuscript PDF, or paper-specific source file was found inside the repository.
- Because there is no separate editable manuscript source in the repo, manuscript edits are provided in `docs/paper_support.md` as replacement-ready text rather than direct PDF edits.

Processed Korean data:

- `data/processed/validation_ko_merged.jsonl`
  - rows: 745
  - key columns: `id`, `split`, `source`, `source_locale`, `target_locale`, `wikidata_id`, `entity_types`, `targets`, `reference_translation`, `reference_mention`, `reference_translations`, `reference_mentions`, `gpt4o_prediction`, `gpt4o_mini_prediction`
  - system outputs available: `gpt4o_prediction`, `gpt4o_mini_prediction`
- `data/processed/validation_ko_with_baselines.jsonl`
  - rows: 745
  - system outputs available: `gpt4o_prediction`, `gpt4o_mini_prediction`, `vanilla_mt_prediction`, `entity_aware_mt_prediction`
- `data/processed/local_dev_ko_with_baselines.jsonl`
  - rows: 595
  - same four system outputs as above
  - includes `local_eval_split`
- `data/processed/local_test_ko_with_baselines.jsonl`
  - rows: 150
  - same four system outputs as above
  - includes `local_eval_split`

Human annotation files:

- `data/human_eval/human_eval_sheet.csv`
  - rows: 200
  - includes main merged annotation fields
- `data/human_eval/human_eval_sheet_merged.csv`
  - rows: 200
  - same schema as `human_eval_sheet.csv`
- `data/human_eval/annotator_exports/minseo_annotations.csv`
  - rows: 100
- `data/human_eval/annotator_exports/siwan_annotations.csv`
  - rows: 100
- `data/human_eval/overlap/annotator_exports/minseo_annotations.csv`
  - rows: 30
- `data/human_eval/overlap/annotator_exports/siwan_annotations.csv`
  - rows: 30

Annotation fields verified:

- Acceptable / borderline / unacceptable is not a raw column; it is derived in `src/analysis/compare_metrics_vs_human.py` from `*_entity_correct` and `*_quality_label`.
- Rendering strategy fields exist:
  - `target_rendering_strategy`
  - `gpt4o_rendering_strategy`
  - `gpt4o_mini_rendering_strategy`
- Preferred-model field exists:
  - `preferred_model`
- Automatic-metric-likely-miss fields exist:
  - `gpt4o_metric_likely_miss`
  - `gpt4o_mini_metric_likely_miss`
- Overlap / agreement annotations exist and have already been summarized in:
  - `outputs/metrics/inter_annotator_agreement.csv`
  - `docs/notes/inter_annotator_agreement.md`

Metric implementation files:

- Mention match and entity metrics:
  - `src/evaluation/run_entity_metrics.py`
  - `src/evaluation/metrics_utils.py`
- Metric-human disagreement and human-label binarization:
  - `src/analysis/compare_metrics_vs_human.py`
- Inter-annotator agreement:
  - `src/analysis/compute_inter_annotator_agreement.py`

## 2026-05-01 New Support Artifacts

Added reproducible script:

- `src/analysis/build_paper_support_artifacts.py`

Generated or refreshed:

- `outputs/metrics/human_acceptability_summary.csv`
- `outputs/metrics/preferred_model_summary.csv`
- `outputs/metrics/metric_miss_summary.csv`
- `outputs/metrics/strategy_breakdown.csv`
- `outputs/metrics/mention_match_confusion.csv`
- `outputs/metrics/overlap_agreement_summary.csv`
- `outputs/metrics/stat_tests.csv`
- `outputs/figures/acceptability_by_model.svg`
- `outputs/figures/rendering_strategy_distribution.svg`
- `outputs/figures/mention_match_confusion.svg`
- `outputs/figures/strategy_acceptability_by_model.svg`

## 2026-05-01 COMET / M-ETA Feasibility

Local references are available for the validation-derived local dev/test splits, so the data itself is not the blocker.

Initial blockers found locally:

- No repository dependency manifest was found (`requirements.txt`, `pyproject.toml`, `environment.yml`, or `setup.py`).
- COMET packages are not installed in the current environment:
  - `comet`: missing
  - `unbabel_comet`: missing
- Before checking external sources, no M-ETA implementation or official evaluation script was present in this repository.
- A repository search found only textual mentions of COMET/M-ETA, not runnable local code.

External source check:

- `https://github.com/SapienzaNLP/ea-mt-eval` provides notebooks for COMET and M-ETA plus `requirements.txt`.
- The M-ETA notebook defines entity accuracy as casefolded substring matching: a prediction is correct if at least one manually annotated reference mention appears in the prediction after `casefold()`.
- The COMET notebook uses `unbabel-comet`, duplicates each prediction across all references, scores each prediction-reference pair, takes the maximum COMET score per example, and averages across examples.

Action taken:

- Added `src/evaluation/run_comet_meta_eval.py`.
- Ran official-style M-ETA locally on `data/processed/local_test_ko_with_baselines.jsonl`.
- Saved `outputs/metrics/comet_meta_results.csv`.

Local test M-ETA results:

- `gpt4o`: 72 / 150 = 48.0
- `gpt4o_mini`: 54 / 150 = 36.0
- `entity_aware_mt`: 47 / 150 = 31.3333
- `vanilla_mt`: 11 / 150 = 7.3333

COMET status:

- Installed `unbabel-comet==2.2.4` locally with `python3 -m pip install --user unbabel-comet==2.2.4`.
- Downloaded and ran `Unbabel/wmt22-comet-da` through `src/evaluation/run_comet_meta_eval.py`.
- The first COMET attempt failed with a Torch/COMET DataLoader issue:
  - `multiprocessing_context can only be used with multi-process loading (num_workers > 0), but got num_workers=0`
- Updated `src/evaluation/run_comet_meta_eval.py` to expose `--num-workers`, defaulting to `1`.
- Re-ran successfully on CPU:

```bash
python3 src/evaluation/run_comet_meta_eval.py --run-comet --gpus 0 --batch-size 8 --num-workers 1
```

- Saved COMET, M-ETA, and harmonic mean results to `outputs/metrics/comet_meta_results.csv`.

Local test COMET / M-ETA / harmonic mean results:

| model | COMET | M-ETA | harmonic mean |
| --- | ---: | ---: | ---: |
| `gpt4o` | 92.7050 | 48.0000 | 63.2506 |
| `gpt4o_mini` | 91.6067 | 36.0000 | 51.6876 |
| `entity_aware_mt` | 89.4729 | 31.3333 | 46.4129 |
| `vanilla_mt` | 84.7982 | 7.3333 | 13.4992 |

Important scope note:

- These are local validation-derived test scores, not official hidden SemEval test scores.
