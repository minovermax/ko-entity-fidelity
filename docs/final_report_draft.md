# Are Current MT Metrics Sensitive to Entity Translation Errors?

Soungmin Lee, Siwan Yang, Minseo Kim

## 1. Introduction

Machine translation systems often produce fluent sentences while still mishandling named entities. This is especially important for English-to-Korean translation, where a named entity may need to be translated, transliterated, preserved in English, or adapted to an established Korean title. A sentence can therefore look broadly correct while still using the wrong Korean entity form.

This project studies evaluation gaps in English-to-Korean entity-aware machine translation. Rather than building a new full MT system, we ask whether automatic metrics adequately capture Korean entity fidelity. Our research question is:

> Do current automatic evaluation methods adequately capture entity fidelity in English-to-Korean translation, especially when Korean requires a choice between translation, transliteration, preservation, or culturally adapted rendering?

We use the Korean portion of the SemEval-2025 Entity-Aware Machine Translation benchmark and compare automatic metrics against human judgments from Korean annotators.

## 2. Related Work and Task Context

The SemEval-2025 Entity-Aware Machine Translation task motivates entity-aware evaluation by focusing on English sentences containing difficult named entities. The task introduces XC-Translate and evaluates both general translation quality and entity correctness. This setting is a natural fit for our project because the course guidelines encourage projects that build on existing datasets, compare against baselines, and conduct empirical analysis.

Our project differs from a shared-task submission. We do not try to maximize leaderboard performance. Instead, we use the task setting to study whether automatic metrics reflect Korean-specific judgments about entity rendering. This is especially relevant for Korean because many entities have established Korean names or titles, while others are more naturally preserved or transliterated.

## 3. Data

We use the English-to-Korean portion of the EA-MT data. Korean has sample and evaluation/reference data, but no Korean training split in the released data we used. The processed data contains:

- 73 Korean sample examples
- 745 Korean validation/reference examples
- 5,082 Korean hidden test examples without targets

The original hidden test set cannot be scored locally because it has no target references in our downloaded data, and the original CodaBench evaluation phase is closed. For course reporting, we therefore create a deterministic local dev/test split from the 745 Korean validation examples:

- local dev: 595 examples
- local test: 150 examples

The split is stratified by primary entity type with seed `4650`. We report local held-out test results, not official SemEval hidden-test results.

## 4. Systems Compared

We compare four systems:

1. `gpt4o`
2. `gpt4o_mini`
3. `vanilla_mt`
4. `entity_aware_mt`

The `vanilla_mt` baseline uses a pretrained multilingual MT model (`facebook/m2m100_418M`) without extra entity information. The `entity_aware_mt` baseline uses Wikidata English/Korean labels and aliases to rewrite the English source by injecting a Korean entity label before translation. This gives us a simple entity-aware intervention without full MT fine-tuning.

This setup also addresses a risk from the proposal feedback. The proposal originally mentioned off-the-shelf NER, which could introduce error propagation. In the final pipeline, we avoid using NER to construct evaluation labels. Instead, we rely on benchmark-provided entity metadata, including `wikidata_id`, `entity_types`, reference translations, and reference mentions. The Wikidata lookup affects only the entity-aware baseline, not the gold labels or human evaluation.

## 5. Metrics and Human Evaluation

We evaluate general translation quality with BLEU-style and chrF-style metrics. We evaluate entity fidelity with mention-based metrics:

- primary mention exact match
- any-reference mention exact match
- normalized mention match
- mention substring recall proxy

These metrics are lightweight and reproducible. We do not claim to reproduce the full official SemEval COMET/M-ETA setup.

For human evaluation, two Korean annotators labeled a 200-example subset. Each example includes two model outputs, giving 400 model-output judgments. Annotators marked:

- ideal Korean rendering strategy: translate, transliterate, preserve, or adapt
- whether an official Korean title/name is preferred
- whether English preservation is preferred
- whether cultural adaptation is needed
- entity correctness for each model
- rendering strategy used by each model
- quality label for each model
- whether the automatic metric is likely to miss the issue
- preferred model

The main annotation round is non-overlapping. We are currently collecting a separate 30-example overlap set to compute inter-annotator agreement. The overlap examples are fresh validation examples outside the original 200-example annotation subset.

**Agreement placeholder:** once both overlap exports are complete, run `python3 src/analysis/compute_inter_annotator_agreement.py` and replace this paragraph with the percent agreement / Cohen's kappa results.

## 6. Automatic Metric Results

On the local held-out test set, `gpt4o` performs best overall. `gpt4o_mini` is second, while the local pretrained MT baselines are weaker. However, the entity-aware baseline substantially improves entity mention fidelity over vanilla MT.

| system | BLEU | avg chrF | mention match |
| --- | ---: | ---: | ---: |
| `gpt4o` | 30.6223 | 56.8152 | 0.4933 |
| `gpt4o_mini` | 25.3421 | 55.1993 | 0.3800 |
| `entity_aware_mt` | 20.0075 | 44.5816 | 0.3333 |
| `vanilla_mt` | 11.6502 | 32.8370 | 0.0733 |

The key baseline result is that entity-aware conditioning helps: `entity_aware_mt` improves mention match from 0.0733 to 0.3333 on the local held-out test, even though it still trails GPT systems on overall translation quality.

## 7. Human Evaluation Results

Human judgments show that `gpt4o` is better than `gpt4o_mini`, but they also show that automatic metrics do not fully track Korean acceptability.

| model | acceptable | borderline | unacceptable | metric-human disagreement |
| --- | ---: | ---: | ---: | ---: |
| `gpt4o` | 160 | 30 | 10 | 0.59 |
| `gpt4o_mini` | 109 | 66 | 25 | 0.73 |

Annotators also identified the ideal Korean rendering strategy:

| strategy | count |
| --- | ---: |
| translate | 104 |
| transliterate | 66 |
| adapt | 25 |
| preserve | 5 |

This supports the central claim: Korean entity fidelity is not just exact string matching. Many cases require a strategy choice.

## 8. Qualitative Analysis

Representative examples show several kinds of metric-human mismatch.

First, strict mention metrics can penalize acceptable Korean variants. For example, the reference mention `주스 오티즈` and prediction `주스 오르티즈` differ on the surface, but the annotator judged the prediction acceptable as an alias or variant.

Second, general metrics can be too harsh on fluent acceptable translations. For Uppsala Cathedral, `웁살라 대성당은 일반인에게 공개되어 있나요?` is acceptable, but differs enough from the reference wording that overlap metrics under-score it.

Third, both general and entity metrics can reject a human-acceptable output. For Piano Sonata No. 9, `피아노 소나타 제9번` is a valid Korean rendering, but differs from the reference `피아노 소나타 9번`.

Fourth, some cases are not simply correct or incorrect; they involve Korean rendering strategy. For Village of the Damned, preserving the English title may be understandable but less appropriate when an established Korean title is expected.

These examples suggest that entity-aware evaluation for Korean should account for aliases, official titles, transliteration variants, and adaptation needs.

## 9. Optional Diagnostic Classifier

As an optional trained component, we train a small logistic regression classifier to predict whether a model output is human-acceptable using automatic metric features, model identity, and entity type. This is not the main contribution, but it provides a lightweight supervised diagnostic.

| system | accuracy | precision | recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| majority baseline | 0.6875 | 0.6875 | 1.0000 | 0.8148 |
| metric-rule baseline | 0.5125 | 0.9000 | 0.3273 | 0.4800 |
| logistic regression | 0.7750 | 0.8627 | 0.8000 | 0.8302 |

The classifier result suggests that combining metric features with entity/model information can better predict human acceptability than a simple automatic-metric rule. We treat this as a diagnostic extension rather than a replacement for human evaluation.

## 10. Limitations

This study has several limitations. First, our test set is a local held-out split, not the official SemEval hidden test. Second, our automatic metrics are lightweight approximations and do not reproduce the full official COMET/M-ETA evaluation. Third, the main 200-example annotation round is non-overlapping; inter-annotator agreement will be added after the separate 30-example overlap round is complete. Fourth, the entity-aware baseline depends on Wikidata labels and string replacement, which can introduce errors when labels are missing, non-standard, or not found in the source sentence.

## 11. Conclusion

Our results show that English-to-Korean entity fidelity requires more than sentence-level similarity or exact mention matching. Strong models such as `gpt4o` perform best overall, and simple entity-aware conditioning improves over vanilla MT, but human judgments reveal evaluation gaps around aliases, transliteration variants, official titles, and cultural adaptation. For Korean entity-aware MT, evaluation should be strategy-aware: it should ask not only whether the entity appears, but whether the entity is rendered in the form a Korean reader would expect.

## References

- Papineni et al. 2002. BLEU: a Method for Automatic Evaluation of Machine Translation.
- Rei et al. 2020. COMET: A Neural Framework for MT Evaluation.
- Conia et al. 2025. SemEval-2025 Task 2: Entity-Aware Machine Translation.
- Zhang et al. 2020. BERTScore: Evaluating Text Generation with BERT.
