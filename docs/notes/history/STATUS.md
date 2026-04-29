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
- final report artifact script implemented and run
- lecture-aligned MT baselines implemented and run
- local dev/test evaluation split implemented and run
- optional overlap-agreement workflow implemented
- optional tiny supervised acceptability classifier implemented and run
- representative qualitative examples selected for report writing
- proposal-feedback risk about off-the-shelf NER error propagation documented

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
- local dev examples: 595
- local test examples: 150
- optional overlap sheet size: 30 examples
- representative examples selected: 8

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

### Final report artifacts

Implemented in [build_final_report_artifacts.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/build_final_report_artifacts.py).

Generated artifacts:

- `outputs/metrics/preferred_model_summary.csv`
- `outputs/metrics/rendering_strategy_summary.csv`
- `outputs/metrics/human_quality_by_model.csv`
- `outputs/metrics/disagreement_by_entity_type.csv`
- `outputs/figures/preferred_model_summary.svg`
- `outputs/figures/rendering_strategy_distribution.svg`
- `outputs/figures/human_quality_by_model.svg`
- `docs/notes/results_memo.md`

These artifacts are intended to be the bridge from raw analysis outputs to:

- paper/report tables
- slides
- short presentation talking points
- representative-example selection

### Added baselines

Implemented in:

- [run_vanilla_mt.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/baselines/run_vanilla_mt.py)
- [run_entity_aware_baseline.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/baselines/run_entity_aware_baseline.py)
- [baseline_utils.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/baselines/baseline_utils.py)

Generated artifacts:

- `outputs/translations/validation_ko_vanilla_mt_predictions.jsonl`
- `outputs/translations/validation_ko_vanilla_mt_predictions.csv`
- `outputs/translations/validation_ko_entity_aware_mt_predictions.jsonl`
- `outputs/translations/validation_ko_entity_aware_mt_predictions.csv`
- `data/processed/validation_ko_with_baselines.jsonl`
- `data/processed/wikidata_entity_labels.json`
- `outputs/metrics/all_models_general_metrics_overall.csv`
- `outputs/metrics/all_models_general_metrics_by_example.csv`
- `outputs/metrics/all_models_general_metrics_by_entity_type.csv`
- `outputs/metrics/all_models_entity_metrics_overall.csv`
- `outputs/metrics/all_models_entity_metrics_by_example.csv`
- `outputs/metrics/all_models_entity_metrics_by_entity_type.csv`
- `docs/notes/baselines.md`

Baseline design:

- `vanilla_mt`:
  - plain pretrained multilingual MT
  - default model: `facebook/m2m100_418M`
- `entity_aware_mt`:
  - uses Wikidata English/Korean labels
  - rewrites the English source with a Korean entity label before MT
  - then translates with the same multilingual model

Top-line baseline results on Korean validation:

- general metrics:
  - `gpt4o`: BLEU `25.8746`, avg chrF `54.6224`
  - `gpt4o-mini`: BLEU `20.7067`, avg chrF `52.3392`
  - `entity_aware_mt`: BLEU `20.5896`, avg chrF `45.1523`
  - `vanilla_mt`: BLEU `11.0663`, avg chrF `32.8703`
- entity metrics:
  - `gpt4o`: any-reference normalized mention match `0.5007`
  - `gpt4o-mini`: any-reference normalized mention match `0.3678`
  - `entity_aware_mt`: any-reference normalized mention match `0.4483`
  - `vanilla_mt`: any-reference normalized mention match `0.0966`

Takeaway:

- the plain pretrained MT baseline is much weaker than the GPT systems
- the entity-aware baseline strongly improves entity fidelity over plain MT
- simple entity-aware conditioning matters, even without fine-tuning

### Local dev/test evaluation

Implemented in:

- [build_local_eval_splits.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/build_local_eval_splits.py)
- [build_local_eval_summary.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/build_local_eval_summary.py)

Generated artifacts:

- `data/processed/local_dev_ko_with_baselines.jsonl`
- `data/processed/local_test_ko_with_baselines.jsonl`
- `data/processed/local_eval_split_summary.json`
- `outputs/metrics/local_eval_split_counts.csv`
- `outputs/metrics/local_dev_all_models_general_metrics_overall.csv`
- `outputs/metrics/local_dev_all_models_entity_metrics_overall.csv`
- `outputs/metrics/local_test_all_models_general_metrics_overall.csv`
- `outputs/metrics/local_test_all_models_entity_metrics_overall.csv`
- `outputs/metrics/local_eval_model_summary.csv`
- `docs/notes/local_evaluation.md`

Reason:

- the official Korean hidden test file has no targets in the downloaded data
- the original CodaBench phases are closed
- therefore the project now reports local dev/test performance using a deterministic held-out split from the Korean validation data

Local split:

- local dev: 595 examples
- local test: 150 examples
- split method: deterministic stratified holdout by primary entity type
- seed: `4650`

Local held-out test results:

- `gpt4o`: BLEU `30.6223`, avg chrF `56.8152`, any-reference normalized mention match `0.4933`
- `gpt4o_mini`: BLEU `25.3421`, avg chrF `55.1993`, any-reference normalized mention match `0.38`
- `entity_aware_mt`: BLEU `20.0075`, avg chrF `44.5816`, any-reference normalized mention match `0.3333`
- `vanilla_mt`: BLEU `11.6502`, avg chrF `32.837`, any-reference normalized mention match `0.0733`

### Risk closure and final report support

Implemented in:

- [build_overlap_annotation_sheet.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/build_overlap_annotation_sheet.py)
- [compute_inter_annotator_agreement.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/compute_inter_annotator_agreement.py)
- [train_acceptability_classifier.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/train_acceptability_classifier.py)
- [select_representative_examples.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/src/analysis/select_representative_examples.py)
- [server.py](/Users/minlee/Desktop/current-sem/CS4650/final%20project/ko-entity-fidelity/overlap_annotation_app/server.py)

Generated artifacts:

- `data/human_eval/overlap/overlap_annotation_sheet.csv`
- `data/human_eval/overlap/overlap_annotation_summary.json`
- `docs/notes/inter_annotator_agreement.md`
- `outputs/metrics/acceptability_classifier_summary.csv`
- `outputs/metrics/acceptability_classifier_predictions.csv`
- `docs/notes/acceptability_classifier.md`
- `outputs/metrics/representative_examples.csv`
- `docs/notes/representative_examples.md`
- `docs/notes/final_report_story.md`
- `docs/notes/risk_closure.md`
- `overlap_annotation_app/server.py`
- `overlap_annotation_app/README.md`

Inter-annotator agreement:

- current main annotations have no overlap
- a 30-example overlap sheet now exists
- a separate overlap annotation web app now exists at `overlap_annotation_app/`
- agreement can be computed after both annotators complete the overlap sheet

Tiny trained diagnostic classifier:

- task: predict human acceptability from automatic metric features, model identity, and entity type
- train rows: 320
- test rows: 80
- majority baseline accuracy: `0.6875`
- metric-rule baseline accuracy: `0.5125`
- logistic regression accuracy: `0.775`
- logistic regression F1: `0.8302`

Qualitative examples:

- 8 representative examples selected from `disagreement_cases.csv`
- examples cover acceptable aliases, overly harsh metrics, wrong Korean rendering strategy, adaptation, preserve-English cases, and metrics missing human rejection

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
- implemented `src/analysis/build_final_report_artifacts.py`
- generated report-ready summary tables, figures, and a results memo
- implemented pretrained MT and entity-aware lecture-aligned baselines
- ran both baselines on Korean validation
- expanded the metric scripts so they can score any `*_prediction` fields from an input JSONL
- generated automatic metric comparisons across GPT + baseline models
- checked the feasibility of official CodaBench hidden-test scoring and found the phases are closed
- implemented local dev/test splits as the replacement evaluation setup
- ran local dev/test general and entity metrics for GPT + baseline models
- created `docs/notes/local_evaluation.md`
- implemented optional overlap annotation workflow for inter-annotator agreement
- added a separate overlap annotation web app so both annotators can label the same 30 examples
- implemented and ran optional supervised acceptability classifier
- selected 8 representative examples for final qualitative analysis
- created report-story and risk-closure notes
- checked the proposal against current project state and documented that the NER error-propagation warning is mostly avoided because benchmark-provided entity metadata is used instead of off-the-shelf NER

## What Is Partial vs Missing

### Partial

1. Results interpretation / write-up
   - the analysis artifacts now exist
   - the project now also has report-ready summaries and figures
   - the baseline comparison layer now also exists
   - the local dev/test reporting layer now also exists
   - but the final paper/report prose still needs to be written

2. Optional methodology strengthening
   - the full annotation pass is complete
   - an optional 30-example overlap subset now exists
   - but Minseo and Siwan still need to annotate it before there is an inter-annotator agreement score

3. Optional explicit training component
   - the project now includes pretrained MT and entity-aware baselines
   - the project now also includes an optional tiny supervised acceptability classifier

## 2026-04-28 Update: Overlap Agreement Merged

What changed:

- fetched remote branches and found two agreement exports:
  - `origin/annotate-minseo`
  - `origin/overlap-siwan`
- merged both into `main`
- added:
  - `data/human_eval/overlap/annotator_exports/minseo_annotations.csv`
  - `data/human_eval/overlap/annotator_exports/siwan_annotations.csv`
- ran `python3 src/analysis/compute_inter_annotator_agreement.py`
- generated:
  - `outputs/metrics/inter_annotator_agreement.csv`
  - `docs/notes/inter_annotator_agreement.md`
- updated the final report draft with the agreement interpretation

Agreement highlights:

- overlap examples scored: 30
- `gpt4o_entity_correct`: 83.3% agreement, kappa 0.635
- `gpt4o_mini_entity_correct`: 73.3% agreement, kappa 0.5556
- `gpt4o_metric_likely_miss`: 83.3% agreement, kappa 0.625
- `gpt4o_mini_metric_likely_miss`: 73.3% agreement, kappa 0.5349
- `preferred_model`: 66.7% agreement, kappa 0.5253
- `target_rendering_strategy`: 40.0% agreement, kappa 0.194

Interpretation:

- agreement is stronger on concrete model-output correctness judgments
- agreement is weaker on abstract Korean rendering-strategy judgments
- this supports the final story that English-to-Korean entity fidelity is strategy-dependent and partly interpretive, not reducible to exact mention matching

### Missing

- final analysis narrative connecting:
  - Korean rendering strategy
  - metric failures
  - entity-type-specific patterns
- final representative example set for the report body / appendix
- final integration of agreement numbers into the polished report and slides

## Recommended Next Steps

These should be the next implementation steps, in order.

1. Review `outputs/metrics/disagreement_cases.csv`
   - identify the strongest example cases for the report
   - pull examples for:
     - general metric misses
     - entity metric misses
     - Korean strategy mismatches
     - acceptable alias cases

2. Turn `docs/notes/results_memo.md` and `docs/notes/baselines.md` into the final results section
   - summarize top-line human outcomes
   - summarize where metrics are too harsh vs too lenient
   - summarize which entity types are hardest in Korean
   - summarize how the pretrained MT baseline compares against the entity-aware baseline and GPT systems
   - explain why the project reports local held-out test results instead of official hidden-test results

3. Produce final report-ready tables / figures
   - preferred model counts
   - quality-label distribution by model
   - disagreement breakdown by model
   - disagreement breakdown by entity type
   - reuse the new SVGs and summary CSVs where possible

4. Integrate overlap agreement into the final write-up
   - use the concrete model-output agreement numbers as reliability evidence
   - use lower strategy-label agreement as evidence that Korean rendering decisions are interpretive
   - frame the 30-example overlap set as a consistency check, not a definitive reliability study

## Best Immediate Next Task

The single best next task is:

**Turn the comparison outputs into report-ready evidence.**

Reason:

- the annotation stage is complete
- the metric-vs-human evidence now exists
- the report-artifact layer now exists
- the lecture-aligned baseline layer now exists
- the local dev/test metric layer now exists
- the remaining work is mainly interpretation, example selection, final presentation, and only optional extra ML

## Suggested Task After That

Immediately after the first pass through the disagreement outputs:

**Draft the results section structure and select 6 to 10 representative examples from `disagreement_cases.csv`.**

That will turn the exported analysis artifacts into the clearest material for the final write-up.

## Notes For Future Runs

- Do not redo dataset download or Korean filtering.
- Treat the repo as an evaluation pipeline, not a model-training repo.
- Prefer deterministic scripts and CSV / JSONL outputs.
- Use the local held-out split for dev/test course reporting.
- Do not call the local test split an official SemEval hidden test result.
- Do not claim the project relies on off-the-shelf NER; the final pipeline uses benchmark-provided entity metadata and reference mentions.
- The human annotation stage is complete for the main 200-example subset.
- The overlap agreement round is complete. Report it as a 30-example consistency check.
- No additional model training is required for the core project.
- If a professor asks for explicit training, the clean add-on is a tiny classifier, not MT fine-tuning.
- Keep updating this file with:
  - what changed
  - what was verified
  - what is still blocked
  - what the next highest-priority task is
