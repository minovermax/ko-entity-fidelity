# Korean Entity Fidelity in Machine Translation

This repository studies evaluation gaps in English-to-Korean entity-aware machine translation. The core question is whether automatic MT metrics capture the entity decisions that Korean readers actually care about: translation, transliteration, preservation, and cultural or title adaptation.

The project uses the Korean portion of the SemEval-2025 Entity-Aware Machine Translation data, compares several translation systems, and aligns automatic scores with Korean human judgments.

## Research Question

> Do current automatic evaluation methods adequately capture entity fidelity in English-to-Korean translation, especially when Korean requires a choice between translation, transliteration, preservation, or culturally adapted rendering?

## What This Repository Contains

- Korean-only EA-MT data preparation and validation checks
- GPT-4o and GPT-4o-mini prediction alignment
- A vanilla pretrained MT baseline
- A Wikidata-label entity-aware MT baseline
- General MT metrics and entity-sensitive mention metrics
- A 200-example Korean human evaluation set
- A separate 30-example overlap annotation workflow for inter-annotator agreement
- Report-ready summary tables, figures, and qualitative examples
- A draft report and notes for final analysis

## Project Shape

This is an evaluation and analysis project, not a full MT system training project. The main contribution is an empirical analysis of where automatic evaluation succeeds or fails for Korean entity rendering.

We avoid relying on off-the-shelf NER for the core evaluation labels. Instead, the EA-MT benchmark provides the entity metadata and reference mentions used for evaluation. The only external entity lookup is in the optional entity-aware baseline, which uses Wikidata labels and aliases as a simple intervention.

## Repository Layout

```text
data/
  raw/                      downloaded source data, ignored by git
  processed/                Korean processed JSONL files and local eval splits
  human_eval/               human annotation sheets and exports

src/
  analysis/                 data prep, subset construction, reporting, agreement
  baselines/                vanilla MT and entity-aware MT baselines
  evaluation/               general and entity-sensitive metric scripts

outputs/
  translations/             baseline prediction artifacts
  metrics/                  metric tables and analysis outputs
  figures/                  report-ready SVG figures

annotation_app/             main non-overlap annotation web app
overlap_annotation_app/     separate overlap annotation app for agreement
docs/
  notes/                    running research notes and report scaffolding
```

## Current Data Setup

The Korean EA-MT data used here contains:

- 73 Korean sample examples
- 745 Korean validation/reference examples
- 5,082 Korean hidden test examples without targets

The original hidden test set cannot be scored locally because target references are not available in the downloaded test file, and the original CodaBench phase is closed. For local reporting, we use a deterministic dev/test split from the Korean validation set:

- local dev: 595 examples
- local test: 150 examples

These are local held-out results, not official SemEval leaderboard results.

## Systems Compared

| system | description |
| --- | --- |
| `gpt4o` | released GPT-4o prediction data |
| `gpt4o_mini` | released GPT-4o-mini prediction data |
| `vanilla_mt` | pretrained multilingual MT without entity intervention |
| `entity_aware_mt` | Wikidata-label source rewriting followed by the same MT model |

## Main Results Snapshot

Local held-out test:

| system | BLEU | avg chrF | mention match |
| --- | ---: | ---: | ---: |
| `gpt4o` | 30.6223 | 56.8152 | 0.4933 |
| `gpt4o_mini` | 25.3421 | 55.1993 | 0.3800 |
| `entity_aware_mt` | 20.0075 | 44.5816 | 0.3333 |
| `vanilla_mt` | 11.6502 | 32.8370 | 0.0733 |

Human evaluation on 200 examples:

| model | acceptable | borderline | unacceptable | metric-human disagreement |
| --- | ---: | ---: | ---: | ---: |
| `gpt4o` | 160 | 30 | 10 | 0.59 |
| `gpt4o_mini` | 109 | 66 | 25 | 0.73 |

Key finding: entity-aware conditioning improves mention fidelity over vanilla MT, but human judgments show that surface metrics still miss Korean-specific alias, transliteration, official-title, and adaptation decisions.

## Reproducing The Pipeline

Run commands from the repository root.

Prepare Korean data from downloaded EA-MT archives:

```bash
python3 src/analysis/prepare_ko_data.py
python3 src/analysis/inspect_dataset.py
```

Build the human-analysis subset:

```bash
python3 src/analysis/build_subset.py
python3 src/analysis/build_human_eval_sheet.py
```

Run automatic metrics for released GPT predictions:

```bash
python3 src/evaluation/run_general_metrics.py
python3 src/evaluation/run_entity_metrics.py
```

Run local baselines:

```bash
python3 src/baselines/run_vanilla_mt.py --batch-size 64
python3 src/baselines/run_entity_aware_baseline.py --batch-size 64
```

Evaluate all systems on the local dev/test split:

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

Compare metrics against human judgments:

```bash
python3 src/analysis/compare_metrics_vs_human.py
python3 src/analysis/build_final_report_artifacts.py
python3 src/analysis/select_representative_examples.py
```

Optional diagnostic classifier:

```bash
python3 src/analysis/train_acceptability_classifier.py
```

## Human Annotation

The main annotation app assigns non-overlapping examples:

```bash
python3 annotation_app/server.py
```

Open:

```text
http://127.0.0.1:8765
```

The overlap annotation app assigns the same 30 fresh examples to both annotators for agreement:

```bash
python3 overlap_annotation_app/server.py
```

Open:

```text
http://127.0.0.1:8766
```

After both overlap exports are merged:

```bash
python3 src/analysis/compute_inter_annotator_agreement.py
```

This writes:

```text
outputs/metrics/inter_annotator_agreement.csv
docs/notes/inter_annotator_agreement.md
```

The current overlap round has been completed on 30 examples. The strongest agreement is on concrete model-output labels such as entity correctness; the more interpretive Korean rendering-strategy labels have lower agreement.

## Important Caveats

- Do not interpret local test results as official SemEval hidden-test results.
- The metric scripts are lightweight and reproducible, but they do not reproduce the full official COMET/M-ETA setup.
- The entity-aware baseline depends on Wikidata labels and string replacement, so it may inherit label or matching errors.
- Inter-annotator agreement is based on a 30-example overlap set, so treat it as a consistency check rather than a definitive reliability study.

## Primary Artifacts

- `docs/final_report_draft.md`
- `docs/notes/results_memo.md`
- `docs/notes/baselines.md`
- `docs/notes/local_evaluation.md`
- `docs/notes/representative_examples.md`
- `outputs/metrics/local_eval_model_summary.csv`
- `outputs/metrics/metric_human_summary.csv`
- `outputs/metrics/disagreement_cases.csv`
