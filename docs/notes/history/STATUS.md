# Project Status

Last updated: 2026-04-19

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

## What Is Partial vs Missing

### Partial

1. Human evaluation
   - the sheet and guidelines now exist
   - but the actual human annotation has not been done yet

2. Disagreement analysis
   - automatic metrics now exist
   - but metric-vs-human comparison cannot be run until annotations are filled in

### Missing

- `src/analysis/compare_metrics_vs_human.py`
- disagreement outputs and figures

## Recommended Next Steps

These should be the next implementation steps, in order.

1. Run human annotation on the formal subset
   - preferred full pass: all 200 examples
   - minimum pass: 100 to 150 examples
   - use the local annotation app
   - commit per-annotator export files from each clone

2. Build `src/analysis/compare_metrics_vs_human.py`
   - merge filled human annotations with metric outputs
   - identify disagreement categories
   - export disagreement cases

3. Produce summary figures
   - metric scores by model
   - metric scores by entity type
   - human error categories by model
   - automatic vs human disagreement breakdown

## Best Immediate Next Task

The single best next task is:

**Start human annotation on `data/human_eval/human_eval_sheet.csv`.**

Reason:

- the analysis subset is now formalized
- the annotation schema and instructions are ready
- automatic metrics are already available
- the project's next major contribution depends on human judgments

## Suggested Task After That

Immediately after the first human annotation pass:

**Implement `src/analysis/compare_metrics_vs_human.py` and export disagreement cases.**

That will turn the completed annotation work into the core evidence for the final analysis.

## Notes For Future Runs

- Do not redo dataset download or Korean filtering.
- Treat the repo as an evaluation pipeline, not a model-training repo.
- Prefer deterministic scripts and CSV / JSONL outputs.
- Keep updating this file with:
  - what changed
  - what was verified
  - what is still blocked
  - what the next highest-priority task is
