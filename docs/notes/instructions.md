# Next Steps for EntityLens

## Project Summary

This project studies **evaluation gaps in English-to-Korean entity-aware machine translation**.
The goal is **not** to build a new state-of-the-art translation model.
Instead, the goal is to analyze whether current automatic evaluation methods adequately capture **entity fidelity** in English-to-Korean translation, especially when Korean requires one of the following:

- translation
- transliteration
- preservation
- cultural adaptation / transcreation

---

## What Is Already Done

The following has already been completed:

- repository created
- project framing decided
- dataset download completed from the EA-MT task page
- English→Korean data filtered / organized
- merged dataset prepared
- baseline-related downloaded prediction data incorporated

Do **not** redo those steps.

---

## Core Research Question

Main question:

> Do current automatic evaluation methods adequately capture entity fidelity in English-to-Korean machine translation?

Secondary questions:

1. Where do general MT metrics fail on entity-sensitive examples?
2. Where do entity-specific metrics still fail for Korean?
3. Which cases require translation vs transliteration vs preservation vs adaptation?
4. Where do automatic metrics disagree with Korean human judgment?

---

## Important Scope Constraints

### What this project is **not**
- not a full shared-task reproduction
- not a new end-to-end entity-aware MT system paper
- not a heavy model training project
- not a leaderboard submission project

### What this project **is**
- an evaluation-and-analysis project
- a Korean-focused study of entity fidelity
- a comparison of automatic metrics and human judgment
- a Korean-specific error taxonomy project with empirical evidence

This is important for originality. The contribution should come from:
- problem framing,
- Korean-specific evaluation design,
- error taxonomy,
- and analysis of metric failure.

---

## High-Level Deliverables

The final outputs should include:

1. **A clean evaluation subset for English→Korean**
2. **Baseline comparison table**
3. **Automatic metric results**
4. **Korean human evaluation results**
5. **A Korean-specific error taxonomy**
6. **A metric-vs-human disagreement analysis**
7. **Figures/tables summarizing results**

---

## Immediate Next Tasks

## 1. Inspect the merged dataset carefully

Create a notebook or script that verifies:

- total number of Korean examples
- available columns
- unique entity types
- whether there are multiple references per item
- whether mentions are always present
- whether the GPT4o / GPT4o-mini predictions align correctly by ID

Output:
- a short dataset summary table
- a few printed example rows

### Required artifact
- `notebooks/01_dataset_inspection.ipynb`
- or `src/analysis/inspect_dataset.py`

---

## 2. Define a **small analysis subset**

Create a manually inspectable subset of about **150–300 examples**.

Selection goals:
- include diverse entity types
- include both easy and difficult cases
- include examples likely to differ on:
  - translation
  - transliteration
  - preservation
  - adaptation

Suggested strategy:
- stratify by entity type where possible
- keep some random examples
- keep some examples where GPT4o and GPT4o-mini differ
- keep some examples where entity mention appears difficult or ambiguous

Output:
- `data/processed/ko_analysis_subset.jsonl`
- `data/processed/ko_analysis_subset.csv`

---

## 3. Build a first-pass Korean error taxonomy

Create an annotation schema for Korean entity handling.

Minimum categories:

### Rendering strategy
- `translate`
- `transliterate`
- `preserve`
- `adapt`

### Outcome quality
- `correct`
- `acceptable_alias`
- `incorrect_entity`
- `wrong_rendering_strategy`
- `partial_entity_error`
- `hallucinated_entity`
- `omitted_entity`

### Notes
Allow a free-text comment field for annotators.

Output:
- `docs/annotation_guidelines.md`
- `data/human_eval/annotation_template.csv`

The annotation guideline should clearly explain:
- when official Korean titles should be preferred
- when transliteration is acceptable
- when preserving English is better
- when adaptation/transcreation is needed

---

## 4. Implement automatic evaluation scripts

Set up scripts for at least two evaluation families:

### A. General MT quality
Use one or more of:
- BLEU
- chrF
- sacreBLEU-compatible metrics

### B. Entity-sensitive evaluation
Implement project-side metrics such as:
- exact mention match
- normalized exact match
- alias-tolerant match if feasible
- mention overlap / span-based proxy if feasible

Even if official EA-MT metrics are available, also implement simpler interpretable metrics so results are explainable.

Outputs:
- `src/evaluation/run_general_metrics.py`
- `src/evaluation/run_entity_metrics.py`
- `outputs/metrics/*.csv`

---

## 5. Run comparisons on available predictions

At minimum, compare:
- gold reference
- GPT4o prediction
- GPT4o-mini prediction

If easy to add later, also compare:
- one vanilla translation baseline
- one simple entity-aware variant

But this is optional. The core project can still succeed without building a new system if the analysis is strong.

Required analyses:
- overall metric comparison
- per-entity-type comparison
- per-rendering-strategy comparison
- disagreement examples

---

## 6. Create human evaluation workflow

For the small subset, create a human evaluation sheet.

Each row should contain:
- ID
- source sentence
- gold translation
- entity mention
- prediction A
- prediction B
- entity type
- Wikidata ID if useful
- annotation slots

Suggested human annotation questions:
1. Is the entity rendered correctly?
2. Is the chosen rendering strategy appropriate for Korean?
3. If wrong, what kind of error is it?
4. Would an automatic metric likely miss this?

Outputs:
- `data/human_eval/human_eval_sheet.csv`
- `docs/human_eval_instructions.md`

---

## 7. Analyze metric-vs-human disagreement

This is one of the most important contributions.

For each evaluated example, compare:
- general metric score
- entity-sensitive metric outcome
- human judgment

Goal:
identify cases where:
- general MT metric looks good but entity handling is wrong
- entity-specific metric still misses Korean-specific issues
- humans reject outputs that metrics treat as acceptable
- humans accept outputs that exact-match metrics penalize too harshly

Create a table of disagreement categories.

Output:
- `outputs/figures/metric_human_disagreement.png`
- `outputs/metrics/disagreement_cases.csv`

---

## 8. Produce descriptive statistics and figures

Create clean summary figures.

Suggested figures:
- entity type distribution
- rendering strategy distribution
- metric scores by model
- metric scores by entity type
- human error categories by model
- automatic-human disagreement breakdown

Output folder:
- `outputs/figures/`

Make plots simple and readable.

---

## Recommended File-Level Task List

### `docs/annotation_guidelines.md`
Must define:
- rendering categories
- correctness categories
- Korean-specific rules
- examples

### `src/analysis/inspect_dataset.py`
Must:
- load merged Korean dataset
- print summary stats
- export quick diagnostics

### `src/analysis/build_subset.py`
Must:
- create the small analysis subset
- support reproducible random seed
- optionally stratify by entity type

### `src/evaluation/run_general_metrics.py`
Must:
- compute BLEU / chrF or equivalent
- save results by model and by example

### `src/evaluation/run_entity_metrics.py`
Must:
- compute exact and normalized entity-level comparisons
- save results by example

### `src/analysis/compare_metrics_vs_human.py`
Must:
- merge metric outputs with human annotations
- quantify disagreement
- export disagreement cases

### `data/human_eval/annotation_template.csv`
Must contain all columns needed for manual annotation.

---

## Suggested Priority Order

1. dataset inspection
2. analysis subset creation
3. annotation guideline
4. automatic metric scripts
5. human eval sheet
6. metric runs on GPT4o / GPT4o-mini
7. small human annotation round
8. disagreement analysis
9. figures

---

## Minimum Acceptable Project

If time becomes tight, the project can still succeed with this minimum version:

- English→Korean subset only
- GPT4o vs GPT4o-mini only
- one small human-evaluated subset
- one general metric + one entity-specific metric
- Korean-specific taxonomy
- metric-vs-human disagreement analysis

---

## Nice-to-Have Extensions (Only If Time Allows)

Do these only after the core pipeline works:

- add one simple vanilla translation baseline
- add one simple entity-aware prompting baseline
- add alias dictionary support
- add entity-type-specific error charts
- test whether some references are themselves debatable
- analyze official-title vs transliteration preference patterns

---

## Coding Expectations

Please keep the implementation:
- modular
- reproducible
- lightweight
- easy to inspect

Avoid:
- large training jobs
- overcomplicated modeling
- premature optimization
- hidden notebook-only logic

Prefer:
- scripts that can be rerun
- CSV / JSONL outputs
- deterministic subset construction
- explicit config variables near the top of each script

---

## Final Goal

By the end, the project should be able to support the following claim:

> Current automatic evaluation methods do not fully capture entity fidelity in English-to-Korean translation, especially in cases where Korean requires nontrivial decisions between translation, transliteration, preservation, and cultural adaptation.

The evidence for this claim should come from:
- dataset examples
- metric comparisons
- human judgments
- Korean-specific error categories

---

## Short Instruction to the Coding Agent

Build the project as an **evaluation and analysis pipeline**, not as a training-heavy MT system.
Prioritize:
1. subset construction,
2. annotation schema,
3. automatic metrics,
4. human evaluation support,
5. disagreement analysis,
6. summary outputs.