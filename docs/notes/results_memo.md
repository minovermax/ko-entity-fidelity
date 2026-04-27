# Results Memo

This note summarizes the main findings from the completed 200-example Korean human evaluation subset.

## What We Can Claim

Current automatic evaluation methods do not fully capture entity fidelity in English-to-Korean translation.
The strongest evidence is that many outputs judged acceptable by Korean annotators are still penalized by either general MT metrics or mention-match metrics, especially when Korean requires a rendering-strategy choice rather than a literal surface match.

## Human Annotation Coverage

- Annotated examples: 200
- Model-output judgments: 400
- Annotators: 2 (non-overlapping split)

## Human Preference Snapshot

- Preferred `gpt4o`: 96
- Preferred `gpt4o_mini`: 41
- Ties: 41
- Neither model preferred: 22

## Korean Rendering Strategy Snapshot

- `translate`: 104
- `transliterate`: 66
- `adapt`: 25
- `preserve`: 5

## Model-Level Human Outcomes

- `gpt4o`: acceptable 160, borderline 30, unacceptable 10
- `gpt4o_mini`: acceptable 109, borderline 66, unacceptable 25

## Error Pattern Snapshot

- `gpt4o` `correct`: 118
- `gpt4o` `acceptable_alias`: 42
- `gpt4o` `wrong_rendering_strategy`: 19
- `gpt4o_mini` `correct`: 62
- `gpt4o_mini` `acceptable_alias`: 47
- `gpt4o_mini` `wrong_rendering_strategy`: 46

## Highest-Disagreement Entity Types

### gpt4o

- `Book series`: disagreement rate 0.8333 (5 / 6)
- `Food`: disagreement rate 0.8 (16 / 20)
- `Landmark`: disagreement rate 0.7895 (15 / 19)
- `Movie`: disagreement rate 0.6316 (12 / 19)
- `TV series`: disagreement rate 0.5789 (11 / 19)

### gpt4o_mini

- `Landmark`: disagreement rate 0.8421 (16 / 19)
- `Place of worship`: disagreement rate 0.8421 (16 / 19)
- `Book series`: disagreement rate 0.8333 (5 / 6)
- `Musical work`: disagreement rate 0.7895 (15 / 19)
- `Fictional entity`: disagreement rate 0.75 (15 / 20)

## What We Do Next

1. Pull 6 to 10 representative examples from `outputs/metrics/disagreement_cases.csv`.
2. Build the final report section around three stories:
   - general metrics can be too harsh on acceptable Korean outputs,
   - entity metrics still miss Korean rendering-strategy choices,
   - `gpt4o_mini` fails more often on borderline or strategy-sensitive cases.
3. Use the generated CSVs and SVGs for clean tables and figures in the write-up.

## What We Do Not Need

- No model training is required for the core project.
- No additional large-scale machine learning experiments are required.
- Extra baselines are optional only if there is time and a clear payoff.
