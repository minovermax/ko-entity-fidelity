# Annotation Guidelines

## Scope

These guidelines are for English-to-Korean entity fidelity evaluation in this repo. The goal is to judge whether a model handled the entity correctly for Korean, not whether the whole sentence is stylistically perfect.

## Rendering Strategy Labels

- `translate`: use an established Korean translation or title.
- `transliterate`: render the entity phonetically in Korean.
- `preserve`: keep the English or original-script form.
- `adapt`: use a culturally adapted or transcreated form when literal rendering is not the best Korean choice.

## Outcome Quality Labels

- `correct`: the entity is rendered correctly for the context.
- `acceptable_alias`: not the primary gold form, but still a valid Korean alias or acceptable variant.
- `incorrect_entity`: the output points to the wrong entity.
- `wrong_rendering_strategy`: the entity refers to the right thing, but the strategy is wrong for Korean.
- `partial_entity_error`: the entity is only partly correct, truncated, overextended, or internally inconsistent.
- `hallucinated_entity`: the output introduces an entity that is not supported by the source.
- `omitted_entity`: the entity is missing or effectively dropped.

## Decision Order

For each example:

1. Identify the entity in the source and confirm the Wikidata-linked target.
2. Decide the best Korean rendering strategy for this context.
3. Judge each model output separately.
4. Use `acceptable_alias` when the output is not the main reference form but is still a real and acceptable Korean rendering.
5. Use `wrong_rendering_strategy` when the entity identity is recoverable but the Korean choice is not the best one.

## Korean-Specific Rules

### Prefer an official Korean title when one is established

Use `translate` when a work, film, book, or landmark has a stable Korean title that Korean readers would normally expect.

Examples of signals:

- well-known movie or TV titles
- books with published Korean editions
- landmark names with common Korean exonyms

If the model gives a valid alternate Korean alias, mark `acceptable_alias`, not automatically `incorrect_entity`.

### Transliteration is often right for people and some place names

Use `transliterate` when Korean normally uses a phonetic rendering instead of a translated meaning.

Common cases:

- personal names
- fictional character names
- organizations or places without a standard translated Korean title

Minor spelling variation can still be acceptable if the intended entity is clear.

### Preserve English when that is the most natural Korean usage

Use `preserve` when Korean users commonly keep the English form, brand form, or stylized original title.

This is especially plausible for:

- brands
- franchise names
- mixed-script popular culture references
- titles whose untranslated form is standard in Korean discourse

Do not reward preservation if a stable Korean title clearly exists and should have been used.

### Adapt when literal rendering would sound wrong or miss the intended Korean usage

Use `adapt` only when a direct translation or transliteration is less appropriate than a Korean convention, paraphrase, or culturally established form.

This label should be used sparingly.

## How To Distinguish Similar Error Types

- `acceptable_alias` vs `wrong_rendering_strategy`:
  - if Korean readers would reasonably accept the output as a valid name for the same entity, use `acceptable_alias`
  - if the entity identity is right but the Korean choice is awkward or not preferred, use `wrong_rendering_strategy`

- `incorrect_entity` vs `partial_entity_error`:
  - use `incorrect_entity` when the output refers to a different entity
  - use `partial_entity_error` when only part of the name is wrong but the intended entity is still mostly identifiable

- `omitted_entity` vs `hallucinated_entity`:
  - use `omitted_entity` when the source entity is missing
  - use `hallucinated_entity` when a new unsupported entity is introduced

## Metric-Miss Flag

Mark `metric_likely_miss = yes` when a simple automatic metric could easily score the sentence as acceptable even though the entity handling is not acceptable for Korean.

Typical triggers:

- the sentence is fluent but the entity title choice is wrong
- the output uses the wrong rendering strategy
- the output uses an alias that exact match would punish too harshly

## Notes Field

Use the notes field for:

- evidence about official Korean usage
- why transliteration is preferable
- why preservation is natural or unnatural
- cases where the reference itself seems debatable
