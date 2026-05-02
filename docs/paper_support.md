# Paper Support Notes

This file provides manuscript-support material only. It does not rewrite the full paper. The repository contains `docs/final_report_draft.md`, but no separate `.tex`, manuscript PDF, or paper-specific source file. If the final manuscript lives outside this repo, copy the replacement text below into that source.

## Data And Scope Facts

- The merged Korean validation dataset with released GPT predictions is `data/processed/validation_ko_merged.jsonl` with 745 examples.
- The local baseline-augmented dataset is `data/processed/validation_ko_with_baselines.jsonl` with 745 examples and four prediction fields: `gpt4o_prediction`, `gpt4o_mini_prediction`, `vanilla_mt_prediction`, and `entity_aware_mt_prediction`.
- The local held-out split is validation-derived, not the official hidden SemEval test:
  - local dev: 595 examples
  - local test: 150 examples
- Human evaluation covers 200 examples and two model outputs per example:
  - `gpt4o`
  - `gpt4o_mini`
- The vanilla MT and entity-aware MT baselines are evaluated automatically, but they are not included in the 200-example human judgment sheet.
- The 30-example overlap annotation round is complete and should be framed as a consistency check.

## Metric Definitions

### Mention Match

The table value called `mention match` is `any_reference_mention_normalized_match_rate`, computed by `src/evaluation/run_entity_metrics.py`.

For each example and model output, the script takes all gold reference mentions in `reference_mentions`. It normalizes both the model prediction and each reference mention using `normalize_text` from `src/evaluation/metrics_utils.py`. This normalization lowercases text and removes whitespace, punctuation, and symbols. The example-level mention-match indicator is true if any normalized gold mention is a substring of the normalized model prediction:

```text
mention_match_i = 1 if any normalize(reference_mention) in normalize(prediction)
                  0 otherwise
```

The reported rate is the average of this boolean indicator over examples:

```text
any_reference_mention_normalized_match_rate
  = mean(mention_match_i)
```

The entity metric script also computes stricter raw substring checks (`primary_mention_exact_match`, `any_reference_mention_exact_match`) and a softer `mention_substring_recall_proxy`, but the main report tables use `any_reference_mention_normalized_match_rate`.

### Disagr.

The `Disagr.` value corresponds to `metric_human_disagreement_rate` from `src/analysis/compare_metrics_vs_human.py`.

Human acceptability is derived from annotation fields, not entered as a single raw label:

```text
acceptable   if quality_label in {correct, acceptable_alias}
borderline   if quality_label == partial_entity_error or entity_correct == partly
unacceptable otherwise
```

The automatic metric side uses two pass/fail signals:

```text
general_pass = sentence_chrf >= 50.0
entity_pass  = any_reference_mention_normalized_match
```

The code computes a BLEU pass field as `sentence_bleu >= 35.0`, but the disagreement category is based on chrF and mention match, not BLEU.

Only two cases are treated as aligned:

```text
acceptable   + general_pass=True  + entity_pass=True
unacceptable + general_pass=False + entity_pass=False
```

All other cases, including every borderline human label, are counted as metric-human disagreement. Therefore:

```text
Disagr. = mean(metric_human_disagreement)
```

This is a conservative disagreement definition. It intentionally treats borderline human judgments as evidence that automatic metrics are not giving a clean accept/reject signal.

## Computed Evidence

### Human Acceptability

From `outputs/metrics/human_acceptability_summary.csv`:

| model | acceptable | borderline | unacceptable |
| --- | ---: | ---: | ---: |
| `gpt4o` | 160 / 200 = 0.800 | 30 / 200 = 0.150 | 10 / 200 = 0.050 |
| `gpt4o_mini` | 109 / 200 = 0.545 | 66 / 200 = 0.330 | 25 / 200 = 0.125 |

### Preferred Model

From `outputs/metrics/preferred_model_summary.csv`:

| preferred model | count | proportion |
| --- | ---: | ---: |
| `gpt4o` | 96 | 0.480 |
| `gpt4o_mini` | 41 | 0.205 |
| tie | 41 | 0.205 |
| neither | 22 | 0.110 |

### Metric Likely Misses

From `outputs/metrics/metric_miss_summary.csv`:

| model | yes | no | maybe |
| --- | ---: | ---: | ---: |
| `gpt4o` | 43 / 200 = 0.215 | 127 / 200 = 0.635 | 30 / 200 = 0.150 |
| `gpt4o_mini` | 81 / 200 = 0.405 | 77 / 200 = 0.385 | 42 / 200 = 0.210 |

### Strategy Distribution

From `outputs/metrics/strategy_breakdown.csv`:

| target rendering strategy | count | proportion |
| --- | ---: | ---: |
| translate | 104 | 0.520 |
| transliterate | 66 | 0.330 |
| adapt | 25 | 0.125 |
| preserve | 5 | 0.025 |

### Mention Match And Human Acceptability

From `outputs/metrics/mention_match_confusion.csv`:

- For `gpt4o`, 52 acceptable outputs did not contain any normalized reference mention.
- For `gpt4o_mini`, 63 acceptable outputs did not contain any normalized reference mention.
- This supports the claim that normalized mention matching can be too harsh for acceptable aliases, paraphrases, or culturally appropriate variants.

### Overlap Agreement

From `outputs/metrics/overlap_agreement_summary.csv`:

- `gpt4o_entity_correct`: 83.3% agreement, kappa 0.635
- `gpt4o_mini_entity_correct`: 73.3% agreement, kappa 0.5556
- `preferred_model`: 66.7% agreement, kappa 0.5253
- `target_rendering_strategy`: 40.0% agreement, kappa 0.194

Interpretation: agreement is stronger on concrete model-output correctness judgments than on abstract target rendering strategy. This should be reported cautiously because the overlap set has only 30 examples.

### Optional Statistics

From `outputs/metrics/stat_tests.csv`:

- Wilson 95% CI for `gpt4o` acceptability: 0.7391 to 0.8495
- Wilson 95% CI for `gpt4o_mini` acceptability: 0.4758 to 0.6125
- Exact McNemar test for paired acceptability:
  - `b=71`, `c=20`, ties/equal cases = 109
  - two-sided exact p-value = `7.24537e-08`
- Exact sign test for preferred model, excluding tie/neither:
  - `gpt4o=96`, `gpt4o_mini=41`
  - two-sided exact p-value = `2.9549e-06`

These tests support the observed advantage of `gpt4o` over `gpt4o_mini` on the annotated subset. They do not make claims about the official hidden SemEval test set.

## COMET / M-ETA Feasibility

Official-style M-ETA and COMET were run locally in this pass using `src/evaluation/run_comet_meta_eval.py`, following the public SapienzaNLP EA-MT evaluation notebook logic.

The local dev/test data has references, so the data is not the blocker.

Run command:

```bash
python3 src/evaluation/run_comet_meta_eval.py --run-comet --gpus 0 --batch-size 8 --num-workers 1
```

The script uses `Unbabel/wmt22-comet-da` by default. For COMET, it duplicates each model output across all available references, takes the maximum COMET score per example, and averages over examples, matching the public EA-MT COMET notebook logic. For M-ETA, it checks whether any reference entity mention appears in the prediction after `casefold()`, matching the public EA-MT M-ETA notebook logic.

From `outputs/metrics/comet_meta_results.csv`, results on the local held-out test split are:

| model | COMET | M-ETA correct / total | M-ETA | harmonic mean |
| --- | ---: | ---: | ---: | ---: |
| `gpt4o` | 92.7050 | 72 / 150 | 48.0000 | 63.2506 |
| `gpt4o_mini` | 91.6067 | 54 / 150 | 36.0000 | 51.6876 |
| `entity_aware_mt` | 89.4729 | 47 / 150 | 31.3333 | 46.4129 |
| `vanilla_mt` | 84.7982 | 11 / 150 | 7.3333 | 13.4992 |

If rerunning from a fresh environment, first install COMET:

```bash
python3 -m pip install unbabel-comet==2.2.4
```

Running COMET requires downloading model weights and may be slow on CPU. These scores are local validation-derived test scores, not official hidden SemEval scores.

## Manuscript Issue List

1. Abstract scope may be too broad if it implies human evaluation for all four systems. Human evaluation covers `gpt4o` and `gpt4o_mini`; `vanilla_mt` and `entity_aware_mt` are automatic-metric baselines only.
2. Title or claim language should avoid implying a general solution for Korean MT evaluation. The evidence is specific to English-to-Korean EA-MT, lightweight BLEU/chrF/mention-match metrics, and one 200-example human subset.
3. `mention match` needs to be defined as normalized any-reference mention substring matching.
4. `Disagr.` needs to be defined as the implemented metric-human disagreement rule using chrF threshold 50 and normalized mention match.
5. IAA interpretation should be cautious: the overlap round is 30 examples and agreement varies substantially by field.
6. If the current manuscript has a repetitive or duplicated Section 5.2.2, it should be replaced by a single focused paragraph connecting mention-match failures to Korean-specific entity rendering.
7. The conclusion should be localized to the actual setup: local validation-derived split, two human-evaluated GPT systems, four automatically scored systems, and lightweight reproducible metrics.

## Replacement-Ready Text

### Abstract Scope Sentence

We automatically evaluate four English-to-Korean MT systems on a validation-derived local split, and we conduct human evaluation on a 200-example subset for the two released GPT prediction systems (`gpt4o` and `gpt4o_mini`).

### Metric-Definition Paragraph

We report BLEU-style and chrF-style sentence similarity scores, plus a lightweight entity mention-match metric. Mention match is computed as `any_reference_mention_normalized_match_rate`: for each example, we normalize the model prediction and all gold reference mentions by lowercasing and removing whitespace, punctuation, and symbols, then mark the example as a match if any normalized reference mention appears as a substring of the normalized prediction. The reported mention-match score is the average of this boolean indicator across examples.

### Disagreement-Definition Sentence

We define `Disagr.` as the proportion of model outputs where the automatic pass/fail signals do not align with human acceptability: chrF must be at least 50 and normalized mention match must be true for an acceptable output to align, while both signals must fail for an unacceptable output to align; all borderline cases are counted as disagreements.

### Cautious IAA Interpretation Sentence

On a 30-example overlap set, annotators agreed more strongly on concrete output-level judgments such as entity correctness (`gpt4o`: 83.3%, kappa 0.635; `gpt4o_mini`: 73.3%, kappa 0.5556) than on the more interpretive target rendering strategy label (40.0%, kappa 0.194), so we treat the overlap results as a consistency check rather than a definitive reliability study.

### Revised Section 5.2.2 Paragraph

Mention matching captures whether a reference entity string appears in the prediction, but it does not fully capture Korean entity fidelity. In the human-evaluated subset, `gpt4o` has 52 acceptable outputs and `gpt4o_mini` has 63 acceptable outputs where normalized mention match is false. These cases are important because Korean often permits or prefers aliases, spacing variants, official localized titles, transliterations, or culturally adapted renderings that do not exactly match the reference mention list. Thus, mention match is useful as a precision-oriented diagnostic, but it should not be interpreted as a complete measure of entity correctness.

### More Precise Conclusion Sentence

Within our English-to-Korean EA-MT setup, local automatic metrics and a 200-example Korean human evaluation show that entity fidelity is strategy-dependent: normalized mention matching and sentence-level overlap identify some errors, but they also miss acceptable Korean aliases, transliteration variants, official title choices, and culturally adapted renderings.
