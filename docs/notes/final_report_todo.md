# Final Report Todo

This is the remaining work after the 30-example overlap annotation round.

## Ready Now

- Turn `docs/final_report_draft.md` into a 4-page final report.
- Shorten the intro and methods sections to fit the page limit.
- Choose 3 to 4 qualitative examples from `docs/notes/representative_examples.md`.
- Decide whether to include the optional classifier in the main report or appendix.
- Make sure the report clearly says local held-out test, not official SemEval hidden test.
- Add one paragraph explaining why the project avoids off-the-shelf NER error propagation.
- Prepare slides from the same story:
  - research question
  - data and systems
  - local test table
  - human evaluation table
  - qualitative examples
  - conclusion

## Completed Overlap Annotation

- Merged Minseo overlap export from `origin/annotate-minseo`.
- Merged Siwan overlap export from `origin/overlap-siwan`.
- Confirmed both exports contain 30 annotation rows.
- Ran:

```bash
python3 src/analysis/compute_inter_annotator_agreement.py
```

- Wrote:
  - `outputs/metrics/inter_annotator_agreement.csv`
  - `docs/notes/inter_annotator_agreement.md`
- Added agreement interpretation to `docs/final_report_draft.md`.

## Agreement Numbers To Use

- `gpt4o_entity_correct`: 83.3% agreement, kappa 0.635
- `gpt4o_mini_entity_correct`: 73.3% agreement, kappa 0.5556
- `gpt4o_metric_likely_miss`: 83.3% agreement, kappa 0.625
- `gpt4o_mini_metric_likely_miss`: 73.3% agreement, kappa 0.5349
- `preferred_model`: 66.7% agreement, kappa 0.5253
- `target_rendering_strategy`: 40.0% agreement, kappa 0.194

Use the contrast between concrete model-output agreement and lower strategy-label agreement as evidence that Korean entity rendering is interpretive.

## Final Claim To Preserve

> English-to-Korean entity fidelity requires strategy-aware evaluation. Surface overlap and exact mention matching miss acceptable aliases, transliteration variants, official title choices, and cultural adaptation decisions.

## Do Not Overclaim

- Do not claim official SemEval hidden-test performance.
- Do not claim full official M-ETA/COMET reproduction.
- Do not overstate inter-annotator agreement. The overlap set is 30 examples and should be framed as a consistency check.
- Do not claim the project relies on off-the-shelf NER.
- Do not present the classifier as the main contribution.
