# Human Evaluation Instructions

## Files

Use:

- `data/human_eval/human_eval_sheet.csv`
- `docs/annotation_guidelines.md`

## Unit of Annotation

Each row is one source example. For each row, annotate both model outputs:

- `gpt4o_prediction`
- `gpt4o_mini_prediction`

## Workflow

1. Read the source sentence.
2. Read the reference translation and reference mention fields.
3. Decide the target rendering strategy that Korean should ideally use.
4. Judge `gpt4o`.
5. Judge `gpt4o-mini`.
6. Record which model is preferred, if either.
7. Add notes only when the case is nontrivial or debatable.

## Plain-Language Rule

Annotate like this:

- imagine you are a normal Korean reader
- do not worry about research terms
- ask what title or name would feel most natural, correct, and familiar in Korean
- if something feels awkward, misleading, too English-heavy, or like the wrong title, mark that

You are not grading literary style. You are mostly judging whether the entity name or title feels right in Korean.

## Required Columns To Fill

Shared columns:

- `target_rendering_strategy`
- `official_korean_title_preferred`
- `preserve_english_preferred`
- `adaptation_needed`

What these mean in plain language:

- `target_rendering_strategy`: what is the best overall way to write this entity in Korean?
- `official_korean_title_preferred`: is there a standard Korean title or name that should be used?
- `preserve_english_preferred`: would Korean readers naturally prefer the English form here?
- `adaptation_needed`: would a direct wording feel unnatural enough that Korean needs a more adjusted form?

Per-model columns:

- `*_entity_correct`
- `*_rendering_strategy`
- `*_quality_label`
- `*_metric_likely_miss`
- `*_notes`

What these mean in plain language:

- `*_entity_correct`: is this basically the right entity in Korean?
- `*_rendering_strategy`: what did the model actually do?
- `*_quality_label`: what kind of success or mistake is this?
- `*_metric_likely_miss`: would a simple automatic score probably fail to notice the problem?
- `*_notes`: short explanation if needed

Optional comparison columns:

- `preferred_model`
- `overall_comments`

## Recommended Label Values

For `*_entity_correct`:

- `yes`
- `partly`
- `no`

For `*_metric_likely_miss`:

- `yes`
- `no`
- `maybe`

Use the exact rendering and quality labels from `docs/annotation_guidelines.md`.

## Recommended Annotation Load

For this repo's current formal subset:

- total rows: 200 examples
- total model judgments: 400 output-level judgments

Recommended minimum for a solid class-project analysis:

- 100 to 150 examples
- which means 200 to 300 model judgments

Recommended full pass:

- all 200 examples
- which means 400 model judgments

## Time Estimate

Approximate single-annotator time:

- 100 examples: about 2 to 3 hours
- 150 examples: about 3 to 5 hours
- 200 examples: about 4 to 6 hours

If possible, a second annotator on a 30 to 50 example overlap set is useful for checking consistency, but it is not strictly required for a course project.
