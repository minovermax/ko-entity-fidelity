# Korean Data Prep

Run the repo-local prep script to extract the Korean SemEval files and build the first-pass analysis tables:

```bash
python3 src/analysis/prepare_ko_data.py
```

What it produces:

- `data/raw/sample/ko_KR.jsonl`
- `data/raw/validation/ko_KR.jsonl`
- `data/raw/test/ko_KR.jsonl`
- `data/raw/predictions/gpt-4o-2024-08-06/validation/ko_KR.jsonl`
- `data/raw/predictions/gpt-4o-mini-2024-07-18/validation/ko_KR.jsonl`
- `data/processed/sample_ko.jsonl`
- `data/processed/validation_ko.jsonl`
- `data/processed/test_ko.jsonl`
- `data/processed/validation_ko_merged.jsonl`
- `data/processed/ko_analysis_table.jsonl`
- `outputs/metrics/validation_ko_merged.csv`
- `outputs/metrics/ko_analysis_table.csv`
- `data/human_eval/ko_validation_analysis_subset_250.csv`
- `data/human_eval/ko_annotation_template.csv`

The merged validation table is the main baseline-comparison asset. It keeps the gold Korean reference fields together with the two provided prediction files:

- `reference_translation`
- `reference_mention`
- `gpt4o_prediction`
- `gpt4o_mini_prediction`

The combined analysis table includes both Korean `sample` and Korean `validation` rows, with a `split` column so later scripts can slice them cleanly.
