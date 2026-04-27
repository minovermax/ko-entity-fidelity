# Final Report Todo

This is the work we can do while waiting for the 30-example overlap annotation round.

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

## Waiting On Overlap Annotation

- Merge Minseo overlap export.
- Merge Siwan overlap export.
- Confirm both exports are from the fresh overlap sheet, not the earlier accidental reused-example sheet.
- Run:

```bash
python3 src/analysis/compute_inter_annotator_agreement.py
```

- Add agreement numbers to:
  - `docs/final_report_draft.md`
  - final report
  - slides, if useful
- Remove the explicit agreement placeholder paragraph from the report draft after numbers are inserted.

## Final Claim To Preserve

> English-to-Korean entity fidelity requires strategy-aware evaluation. Surface overlap and exact mention matching miss acceptable aliases, transliteration variants, official title choices, and cultural adaptation decisions.

## Do Not Overclaim

- Do not claim official SemEval hidden-test performance.
- Do not claim full official M-ETA/COMET reproduction.
- Do not claim the project relies on off-the-shelf NER.
- Do not present the classifier as the main contribution.
