You are working in the root of this repository.

This is an evaluation-and-analysis task for an English-to-Korean MT project. Do not invent results, do not train new models, and do not claim anything about the official hidden SemEval test set. Work only from files present in the repo and from reproducible computations you can run locally.

First, PLAN before making changes:
1. Inspect the repository structure and identify the relevant files for:
   - the manuscript or manuscript source
   - data/processed and data/human_eval
   - src/evaluation and src/analysis
   - outputs/metrics and outputs/figures
   - any scripts that define automatic metrics
2. Write a short plan in `docs/codex_issue_log.md` before running analyses.

Primary goal:
Produce the missing analysis artifacts and manuscript-support artifacts needed to strengthen the current paper, without rewriting the full report.

Important constraints:
- no new model training
- no fabricated values
- no notebook-only hidden logic if avoidable
- prefer reproducible scripts and CSV outputs
- if an analysis is impossible, state exactly why, including the missing file/column/blocker
- if the manuscript source is not editable, do not try to edit the PDF; instead create `docs/paper_support.md` with exact definitions, issue notes, and ready-to-paste replacement text

Your tasks:

A. REPO + DATA AUDIT
- Find the merged Korean dataset and summarize:
  - number of examples
  - key columns
  - system outputs available
  - human-annotation files available
- Verify whether human annotations include:
  - acceptable / borderline / unacceptable
  - rendering strategy
  - preferred model
  - “automatic metrics likely miss this” or equivalent
  - overlap / agreement annotations
- Save findings in `docs/codex_issue_log.md`.

B. METRIC DEFINITIONS
Find the exact code used for:
- mention match
- metric-human disagreement (`Disagr.` or equivalent)
- any binarization of human labels
- any normalization or exact-match logic

Then write precise definitions in `docs/paper_support.md`:
- one subsection for `mention match`
- one subsection for `Disagr.`
Use the exact implemented logic from code, not a guessed description.

C. HUMAN-ANNOTATION ANALYSES
Using existing annotations, compute and save:
1. `outputs/metrics/human_acceptability_summary.csv`
   - counts and proportions for Acceptable / Borderline / Unacceptable by model
2. `outputs/metrics/preferred_model_summary.csv`
   - if preferred-model labels exist
3. `outputs/metrics/metric_miss_summary.csv`
   - if “automatic metrics likely miss this” labels exist
4. `outputs/metrics/strategy_breakdown.csv`
   - counts by target rendering strategy
   - acceptability by strategy and by model if possible
5. `outputs/metrics/mention_match_confusion.csv`
   - confusion table between mention match and human acceptability
   - do this per model if possible
6. `outputs/metrics/overlap_agreement_summary.csv`
   - summarize the overlap annotation / inter-annotator agreement files if present

D. FIGURES
Create clear summary figures in `outputs/figures/`:
- acceptability by model
- rendering-strategy distribution
- mention-match vs human-acceptability disagreement
- strategy-specific acceptability if possible

Keep figures simple and publication-friendly.

E. OPTIONAL STATISTICS
If the annotations support it, compute one or more of:
- 95% confidence intervals for acceptability proportions
- McNemar’s test for paired acceptability comparison between GPT-4o and GPT-4o-mini
- sign test or equivalent for preferred-model judgments

If possible, save outputs in:
- `outputs/metrics/stat_tests.csv`
- and summarize them in `docs/paper_support.md`

If not possible, explain why.

F. COMET / M-ETA FEASIBILITY AND LOCAL RUN
Check whether COMET and/or M-ETA can be run on the repo’s local validation-derived split using available references.
- If yes:
  - implement or wire up reproducible scripts
  - run them locally
  - save results to `outputs/metrics/comet_meta_results.csv`
  - document exactly what was run, on what split, and with what inputs
- If no:
  - document the precise blocker in `docs/codex_issue_log.md`
  - do not hand-wave

G. MANUSCRIPT SUPPORT ONLY (NOT FULL REPORT WRITING)
Create `docs/paper_support.md` containing:
1. a concise issue list tied to the current paper:
   - abstract seems to imply human evaluation for all four systems; verify exact scope
   - title/claim language may be broader than evaluated metrics
   - `mention match` is underdefined
   - `Disagr.` is underdefined
   - the IAA interpretation should be cautious
   - §5.2.2 appears repetitive / duplicated
   - the conclusion should be localized to the actual setup
2. exact replacement-ready wording for:
   - abstract scope sentence
   - metric-definition paragraph
   - disagreement-definition sentence
   - a cautious IAA interpretation sentence
   - a revised §5.2.2 paragraph
   - a more precise conclusion sentence

Do not rewrite the whole paper. Only provide short, high-value replacement text blocks grounded in actual results.

H. OUTPUT SUMMARY
At the end, return:
1. what files you created or modified
2. what analyses were successfully computed
3. which manuscript issues are now supported by computed evidence
4. which remaining issues require human judgment or missing data
5. whether COMET/M-ETA was successfully run locally

Quality bar:
- be precise
- be reproducible
- do not guess
- do not overclaim