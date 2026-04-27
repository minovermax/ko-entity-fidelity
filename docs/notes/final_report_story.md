# Final Report Story

## One-Sentence Thesis

Automatic MT metrics under-measure English-to-Korean entity fidelity because Korean named-entity rendering often requires choosing between translation, transliteration, preservation, and cultural/title adaptation.

## Main Claim

This project is an evaluation and error-analysis study, not primarily a model-building study. We show that:

1. strong systems such as `gpt4o` outperform smaller and local baselines overall,
2. generic pretrained MT performs poorly on Korean entity mentions,
3. a simple entity-aware baseline using Wikidata labels improves entity fidelity over vanilla MT,
4. human judgments reveal that surface metrics still miss Korean-specific rendering decisions.

## Evidence To Use

- Local held-out test:
  - `gpt4o`: BLEU `30.6223`, avg chrF `56.8152`, mention match `0.4933`
  - `gpt4o_mini`: BLEU `25.3421`, avg chrF `55.1993`, mention match `0.38`
  - `entity_aware_mt`: BLEU `20.0075`, avg chrF `44.5816`, mention match `0.3333`
  - `vanilla_mt`: BLEU `11.6502`, avg chrF `32.837`, mention match `0.0733`
- Human evaluation:
  - 200 examples
  - 400 model-output judgments
  - `gpt4o`: 160 acceptable, 30 borderline, 10 unacceptable
  - `gpt4o_mini`: 109 acceptable, 66 borderline, 25 unacceptable
- Metric-human disagreement:
  - `gpt4o`: disagreement rate `0.59`
  - `gpt4o_mini`: disagreement rate `0.73`
- Korean rendering strategy distribution:
  - translate: 104
  - transliterate: 66
  - adapt: 25
  - preserve: 5

## Report Structure

1. Introduction
   - Named entities are hard in MT.
   - Korean is especially interesting because many names/titles have conventional Korean renderings.
   - Research question: do automatic metrics capture this?

2. Related Work / Task Context
   - SemEval-2025 Task 2: Entity-Aware Machine Translation.
   - XC-Translate and M-ETA motivate entity-aware evaluation.
   - Team ACK motivates Korean-specific adaptation/transcreation.

3. Data
   - Korean EA-MT sample/validation/test.
   - Korean hidden test has no targets locally; CodaBench phase is closed.
   - We report a deterministic local dev/test split from the Korean validation set.

4. Systems Compared
   - `gpt4o`
   - `gpt4o_mini`
   - vanilla pretrained MT
   - entity-aware MT with Wikidata label injection

5. Metrics and Human Evaluation
   - BLEU/chrF-style general metrics
   - entity mention match metrics
   - 200-example human annotation subset
   - Korean rendering categories

6. Results
   - GPT systems win overall.
   - Entity-aware baseline improves mention fidelity over vanilla MT.
   - Human judgments show metrics are often too harsh on acceptable aliases or too coarse for rendering strategy.

7. Qualitative Analysis
   - Use `docs/notes/representative_examples.md`.
   - Focus on acceptable aliases, wrong rendering strategy, adaptation, and metrics missing human rejection.

8. Limitations
   - Local test, not official hidden test.
   - Main annotations are non-overlapping; optional overlap workflow exists if time allows.
   - Metrics are lightweight, not a full official M-ETA/COMET reproduction.
   - We avoid NER error propagation by using benchmark-provided entity metadata, but the Wikidata-based baseline can still inherit label/alias or string-replacement errors.
   - Tiny classifier is optional and diagnostic, not the main contribution.

9. Conclusion
   - Korean entity fidelity needs strategy-aware evaluation.
   - Exact mention matching alone is insufficient.
   - Simple entity-aware interventions help, but evaluation still needs human-informed categories.
