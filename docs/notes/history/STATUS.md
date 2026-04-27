# Project Status

Last updated: 2026-04-27

## Current Project State

This repo is already positioned as an evaluation-and-analysis project for English-to-Korean entity fidelity, which matches the scope in `docs/notes/instructions.md`.

The Korean data prep stage is done:

- SemEval archives downloaded
- Korean sample / validation / test files extracted
- Korean processed JSONL files created
- merged validation table with gold + `gpt-4o` + `gpt-4o-mini` created
- dataset inspection script implemented and run
- formal 200-example analysis subset created
- annotation guidelines written
- human evaluation sheet generated
- local annotation web app created for clone-local teammate use
- general metric script implemented and run
- entity metric script implemented and run
- both teammate annotation branches merged
- full human annotation merged back into the shared sheet
- metric-vs-human comparison script implemented and run

Current known counts:

- sample: 73 Korean examples
- validation: 745 Korean examples
- test: 5,082 Korean examples
- prediction alignment:
  - `gpt-4o`: 745 / 745
  - `gpt-4o-mini`: 745 / 745
- validation rows with multiple references: 610 / 745
- validation rows missing reference mention: 0 / 745
- formal analysis subset: 200 examples
- human evaluation load for full subset: 400 model-output judgments
- completed human annotation rows: 200 / 200
- completed model-output judgments: 400 / 400

## What Has Been Done So Far

### Data preparation

Implemented in [prepare_ko_data.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/prepare_ko_data.py).

Generated artifacts:

- `data/raw/sample/ko_KR.jsonl`
- `data/raw/validation/ko_KR.jsonl`
- `data/raw/test/ko_KR.jsonl`
- `data/raw/predictions/gpt-4o-2024-08-06/validation/ko_KR.jsonl`
- `data/raw/predictions/gpt-4o-mini-2024-07-18/validation/ko_KR.jsonl`
- `data/processed/sample_ko.jsonl`
- `data/processed/validation_ko.jsonl`
- `data/processed/test_ko.jsonl`
- `data/processed/validation_ko_merged.jsonl`
- `data/processed/ko_analysis_table.jsonl`
- `outputs/metrics/validation_ko_merged.csv`
- `outputs/metrics/ko_analysis_table.csv`
- `data/human_eval/ko_validation_analysis_subset_250.csv`
- `data/human_eval/ko_annotation_template.csv`
- `data/processed/ko_dataset_summary.json`

### Dataset inspection

Implemented in [inspect_dataset.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/inspect_dataset.py).

Generated artifacts:

- `outputs/metrics/validation_ko_inspection_summary.json`
- `outputs/metrics/validation_ko_inspection_summary.csv`
- `outputs/metrics/validation_ko_entity_type_counts.csv`
- `outputs/metrics/validation_ko_inspection_examples.jsonl`

Key findings:

- merged Korean validation rows: 745
- total columns in merged file: 14
- rows with multiple references: 610
- rows missing reference mention: 0
- validation / merged / prediction IDs all match exactly
- merged predictions exactly match raw prediction files
- top primary entity types:
  - `Artwork`: 168
  - `TV series`: 120
  - `Movie`: 78
  - `Person`: 77
  - `Musical work`: 75

### Subset construction

Implemented in [build_subset.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/build_subset.py).

Generated artifacts:

- `data/processed/ko_analysis_subset.jsonl`
- `data/processed/ko_analysis_subset.csv`
- `data/processed/ko_analysis_subset_summary.json`

Key findings:

- final formal subset size: 200
- stage mix:
  - `seed`: 66
  - `hard_case`: 54
  - `easy_case`: 40
  - `random_fill`: 40
- primary entity type coverage is balanced across the available Korean validation types

### Human evaluation setup

Generated artifacts:

- `docs/annotation_guidelines.md`
- `docs/human_eval_instructions.md`
- `data/human_eval/human_eval_sheet.csv`
- `data/human_eval/annotation_template.csv`
- `data/human_eval/ko_annotation_template.csv`
- `annotation_app/server.py`
- `annotation_app/static/index.html`
- `annotation_app/static/styles.css`
- `annotation_app/static/app.js`
- `annotation_app/README.md`
- `annotation_app/data/annotator_assignments.json`
- `src/analysis/merge_annotator_exports.py`

Human annotation planning:

- current formal sheet size: 200 examples
- two model judgments per row:
  - `gpt4o`
  - `gpt4o-mini`
- full pass annotation load: 400 output-level judgments
- recommended minimum: 100 to 150 examples

Clone-local annotation workflow:

- Minseo and Siwan each get a fixed non-overlapping 100-example split
- each annotator runs the local app in their own clone
- each annotator writes only to their own export file:
  - `data/human_eval/annotator_exports/minseo_annotations.csv`
  - `data/human_eval/annotator_exports/siwan_annotations.csv`
- a merge script can fold those exports back into the repo sheet

### Completed human evaluation

Completed artifacts:

- `data/human_eval/annotator_exports/minseo_annotations.csv`
- `data/human_eval/annotator_exports/siwan_annotations.csv`
- `data/human_eval/human_eval_sheet_merged.csv`
- updated `data/human_eval/human_eval_sheet.csv`

Annotation completion:

- Minseo completed 100 / 100 assigned examples
- Siwan completed 100 / 100 assigned examples
- total completed subset rows: 200 / 200
- total judged model outputs: 400

Human judgment distribution highlights:

- target rendering strategy:
  - `translate`: 104
  - `transliterate`: 66
  - `adapt`: 25
  - `preserve`: 5
- `official_korean_title_preferred`:
  - `yes`: 135
  - `no`: 65
- `adaptation_needed`:
  - `yes`: 34
  - `no`: 166
- `preferred_model`:
  - `gpt4o`: 96
  - `gpt4o_mini`: 41
  - `tie`: 41
  - `neither`: 22

### Automatic metrics

Implemented in:

- [run_general_metrics.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/evaluation/run_general_metrics.py)
- [run_entity_metrics.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/evaluation/run_entity_metrics.py)

Generated artifacts:

- `outputs/metrics/general_metrics_by_example.csv`
- `outputs/metrics/general_metrics_overall.csv`
- `outputs/metrics/general_metrics_by_entity_type.csv`
- `outputs/metrics/entity_metrics_by_example.csv`
- `outputs/metrics/entity_metrics_overall.csv`
- `outputs/metrics/entity_metrics_by_entity_type.csv`

Current top-line results on Korean validation:

- general metrics:
  - `gpt4o` corpus BLEU: `25.8746`
  - `gpt4o-mini` corpus BLEU: `20.7067`
  - `gpt4o` average sentence chrF: `54.6224`
  - `gpt4o-mini` average sentence chrF: `52.3392`
- entity metrics:
  - `gpt4o` any-reference normalized mention match rate: `0.5007`
  - `gpt4o-mini` any-reference normalized mention match rate: `0.3678`

### Metric-vs-human comparison

Implemented in [compare_metrics_vs_human.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/compare_metrics_vs_human.py).

Generated artifacts:

- `outputs/metrics/metric_human_comparison_by_example.csv`
- `outputs/metrics/metric_human_summary.csv`
- `outputs/metrics/disagreement_summary.csv`
- `outputs/metrics/disagreement_cases.csv`
- `outputs/metrics/metric_human_summary_by_entity_type.csv`
- `outputs/figures/metric_human_disagreement.svg`

Current top-line results on the annotated 200-example subset:

- `gpt4o`
  - human acceptable: `160 / 200`
  - human borderline: `30 / 200`
  - human unacceptable: `10 / 200`
  - general chrF pass rate: `0.625`
  - entity metric pass rate: `0.59`
  - strategy match rate: `0.79`
  - metric-human disagreement rate: `0.59`
- `gpt4o_mini`
  - human acceptable: `109 / 200`
  - human borderline: `66 / 200`
  - human unacceptable: `25 / 200`
  - general chrF pass rate: `0.52`
  - entity metric pass rate: `0.235`
  - strategy match rate: `0.685`
  - metric-human disagreement rate: `0.73`

Most important disagreement patterns:

- for `gpt4o`, the most common failures are:
  - `general_metric_too_harsh_on_acceptable_output`: 32
  - `entity_metric_too_harsh_on_acceptable_output`: 31
  - `both_metrics_too_harsh_on_acceptable_output`: 21
- for `gpt4o_mini`, the dominant issue is that many outputs are borderline or strategy-wrong even when surface overlap is decent:
  - `borderline_human_and_metrics_fail`: 34
  - `entity_metric_too_harsh_on_acceptable_output`: 32
  - `both_metrics_too_harsh_on_acceptable_output`: 31
  - `borderline_human_general_pass_entity_fail`: 31

Entity types with especially high disagreement:

- `gpt4o`
  - `Book series`: `0.8333`
  - `Food`: `0.8`
  - `Landmark`: `0.7895`
- `gpt4o_mini`
  - `Landmark`: `0.8421`
  - `Place of worship`: `0.8421`
  - `Book series`: `0.8333`
  - `Musical work`: `0.7895`
  - `Fictional entity`: `0.75`

### Most recent run

- reviewed `docs/notes/instructions.md`
- mapped the instruction list against what is already present in the repo
- identified which tasks are complete, partial, and still missing
- created this running status file for future runs
- implemented `src/analysis/inspect_dataset.py`
- ran the inspection script and exported diagnostics
- confirmed that the merged Korean validation table is structurally sound
- implemented `src/analysis/build_subset.py`
- implemented `docs/annotation_guidelines.md`
- implemented `docs/human_eval_instructions.md`
- generated the formal human evaluation sheet
- implemented a local annotation website for teammate use
- implemented a merge script for per-annotator export files
- fixed the annotation app layout so the annotation panel stays visible on narrower windows
- added plain-language guidance and per-field help text for non-research annotators
- moved the final model-comparison decision below the two model outputs in the annotation UI
- implemented both metric runner scripts
- ran the current baseline metrics on Korean validation
- fetched `annotate-minseo` and `annotate-siwan` from GitHub
- merged both annotation branches into local `main`
- merged per-annotator export files back into the shared human evaluation sheet
- implemented `src/analysis/compare_metrics_vs_human.py`
- ran metric-vs-human comparison and exported summaries, disagreement cases, and a figure

## What Is Partial vs Missing

### Partial

1. Results interpretation / write-up
   - the analysis artifacts now exist
   - but the paper-ready narrative, tables, and claim framing still need to be written

2. Optional methodology strengthening
   - the full annotation pass is complete
   - but there is no overlap subset, so there is no inter-annotator agreement score

### Missing

- concise report-ready result tables / figures in the exact format needed for the final write-up
- final analysis narrative connecting:
  - Korean rendering strategy
  - metric failures
  - entity-type-specific patterns

## Recommended Next Steps

These should be the next implementation steps, in order.

1. Review `outputs/metrics/disagreement_cases.csv`
   - identify the strongest example cases for the report
   - pull examples for:
     - general metric misses
     - entity metric misses
     - Korean strategy mismatches
     - acceptable alias cases

2. Write a short results memo or notebook
   - summarize top-line human outcomes
   - summarize where metrics are too harsh vs too lenient
   - summarize which entity types are hardest in Korean

3. Produce final report-ready tables / figures
   - preferred model counts
   - quality-label distribution by model
   - disagreement breakdown by model
   - disagreement breakdown by entity type

4. Optionally add a small overlap set later
   - 20 to 30 examples annotated by both people
   - only if an inter-annotator agreement section becomes necessary

## Best Immediate Next Task

The single best next task is:

**Turn the comparison outputs into report-ready evidence.**

Reason:

- the annotation stage is complete
- the metric-vs-human evidence now exists
- the remaining work is mainly interpretation, example selection, and final presentation

## Suggested Task After That

Immediately after the first pass through the disagreement outputs:

**Draft the results section structure and select 6 to 10 representative examples from `disagreement_cases.csv`.**

That will turn the exported analysis artifacts into the clearest material for the final write-up.

## Notes For Future Runs

- Do not redo dataset download or Korean filtering.
- Treat the repo as an evaluation pipeline, not a model-training repo.
- Prefer deterministic scripts and CSV / JSONL outputs.
- The human annotation stage is complete for the main 200-example subset.
- There is currently no overlap subset, so do not claim inter-annotator agreement.
- Keep updating this file with:
  - what changed
  - what was verified
  - what is still blocked
  - what the next highest-priority task is
