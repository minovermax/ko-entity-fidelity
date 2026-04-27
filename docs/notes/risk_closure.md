# Risk Closure Notes

This note addresses the five main weaknesses identified before final report writing.

## 1. No Official SemEval Hidden-Test Result

Status: addressed as a limitation.

The official Korean hidden test in our downloaded data has no targets, and the original CodaBench phases are closed. We should not claim official SemEval hidden-test performance.

What we did instead:

- created a deterministic local dev/test split from Korean validation references
- kept the local test held out for final automatic metric reporting
- documented the wording in `docs/notes/local_evaluation.md`

Report wording:

> Because the official Korean hidden test targets are unavailable in our local data and the original CodaBench evaluation phases are closed, we report automatic metrics on a deterministic local dev/test split from the Korean validation set. These are local held-out results, not official SemEval leaderboard results.

## 2. No Inter-Annotator Agreement

Status: setup added; requires a tiny extra annotation pass if we want an agreement number.

Existing Minseo and Siwan annotations are non-overlapping, so agreement cannot be computed from the current main sheet.

What we added:

- `src/analysis/build_overlap_annotation_sheet.py`
- `src/analysis/compute_inter_annotator_agreement.py`
- `overlap_annotation_app/server.py`
- `overlap_annotation_app/README.md`
- annotation app support for `ANNOTATION_ASSIGNMENT_MODE=all`

Run:

```bash
python3 overlap_annotation_app/server.py
```

Then open `http://127.0.0.1:8766`.

After both people annotate the 30 overlap examples:

```bash
python3 src/analysis/compute_inter_annotator_agreement.py
```

## 3. No Explicit Trained Model

Status: optional trained diagnostic model added.

The main project does not need MT model training. But if the professor expects an explicit learned component, we now have a tiny supervised classifier:

- `src/analysis/train_acceptability_classifier.py`
- input: `outputs/metrics/metric_human_comparison_by_example.csv`
- task: predict whether a model output is human-acceptable using automatic metric features, model identity, and entity type

This is not the main contribution. It should be presented as a diagnostic extension only.

Current result:

- majority baseline accuracy: `0.6875`
- metric-rule baseline accuracy: `0.5125`
- logistic regression accuracy: `0.775`
- logistic regression F1: `0.8302`

## 4. Final Report Not Yet Polished

Status: report story scaffold added.

Use:

- `docs/notes/final_report_story.md`
- `docs/notes/results_memo.md`
- `docs/notes/baselines.md`
- `docs/notes/local_evaluation.md`

The report should argue that Korean entity fidelity requires strategy-aware evaluation, not just sentence-level overlap or exact entity mention matching.

## 5. Need Concrete Qualitative Examples

Status: example selector added.

Use:

- `src/analysis/select_representative_examples.py`
- `outputs/metrics/representative_examples.csv`
- `docs/notes/representative_examples.md`

These examples should anchor the qualitative analysis section.

Current selected example count: 8.

## 6. Proposal Feedback: Error Propagation From Off-The-Shelf Models

Status: mostly avoided by design, with one remaining baseline limitation.

The proposal originally mentioned applying off-the-shelf NER to identify entities. The feedback warned that this could introduce error propagation: if NER identifies the wrong span or entity, later entity-fidelity analysis could become unreliable.

Current project state:

- We do not use off-the-shelf NER for the core evaluation labels.
- The SemEval EA-MT data already provides entity metadata, including `wikidata_id`, `entity_types`, target references, and reference mentions.
- Human annotation is performed against the provided source, reference, model predictions, and Korean entity mention.
- Entity metrics compare model outputs against gold/reference mentions, not NER-extracted mentions.

Therefore, the original NER error-propagation risk is mostly unnecessary for the final project.

Remaining related limitation:

- The optional `entity_aware_mt` baseline uses Wikidata labels/aliases and string replacement.
- Wikidata labels can be incomplete or non-ideal, and string replacement may fail when the source wording does not exactly match the label.
- This affects only the baseline system, not the gold data or human evaluation.

Report wording:

> We avoid a major source of error propagation by not relying on off-the-shelf NER to construct the evaluation labels. Instead, we use the entity metadata and reference mentions supplied by the EA-MT benchmark. The only remaining external-resource dependency is the Wikidata label lookup used by our entity-aware baseline, which we treat as a baseline limitation rather than as ground truth.
