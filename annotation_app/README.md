# Annotation App

This is a local web app for the human evaluation phase.

## What it does

- lets each teammate choose `Minseo` or `Siwan`
- gives each annotator a fixed non-overlapping slice of the evaluation sheet
- saves progress locally in that annotator's clone
- keeps the original shared sheet as the base reference

## Run it

From the repo root:

```bash
python3 annotation_app/server.py
```

Then open:

```text
http://127.0.0.1:8765
```

## Optional overlap-agreement mode

Use this only if the project needs an inter-annotator agreement number.

First build the overlap sheet:

```bash
python3 src/analysis/build_overlap_annotation_sheet.py
```

Then run the app so both annotators receive the same 30 examples:

```bash
ANNOTATION_BASE_SHEET=data/human_eval/overlap/overlap_annotation_sheet.csv \
ANNOTATION_EXPORT_DIR=data/human_eval/overlap/annotator_exports \
ANNOTATION_ASSIGNMENTS_PATH=annotation_app/data/overlap_annotator_assignments.json \
ANNOTATION_ASSIGNMENT_MODE=all \
ANNOTATION_PORT=8766 \
python3 annotation_app/server.py
```

Then open:

```text
http://127.0.0.1:8766
```

After both overlap exports exist, compute agreement:

```bash
python3 src/analysis/compute_inter_annotator_agreement.py
```

## Where annotations are saved

Each annotator writes to a separate CSV in their own clone:

- `data/human_eval/annotator_exports/minseo_annotations.csv`
- `data/human_eval/annotator_exports/siwan_annotations.csv`

That keeps Git merges cleaner than having both people edit the same CSV.

## Recommended teammate workflow

Each teammate should work in their own clone or branch.

Recommended Git workflow:

1. clone the repo
2. create a branch for your annotation work

```bash
git checkout -b annotate-your-name
```

3. start the local annotation app

```bash
python3 annotation_app/server.py
```

4. open:

```text
http://127.0.0.1:8765
```

5. choose your assigned name in the app
6. annotate and save as you go
7. commit your annotator export file
8. push your branch to GitHub
9. open a pull request, or send the branch back to the repo owner

Typical Git commands:

```bash
git add data/human_eval/annotator_exports/*.csv
git commit -m "Add annotation progress"
git push -u origin annotate-your-name
```

For Minseo:

1. clone the repo
2. run `git checkout -b annotate-minseo`
3. run `python3 annotation_app/server.py`
4. open `http://127.0.0.1:8765`
5. choose `Minseo` in the app
6. annotate and save
7. commit `data/human_eval/annotator_exports/minseo_annotations.csv`
8. push to GitHub

Example:

```bash
git add data/human_eval/annotator_exports/minseo_annotations.csv
git commit -m "Add Minseo annotations"
git push -u origin annotate-minseo
```

For Siwan:

1. clone the repo
2. run `git checkout -b annotate-siwan`
3. run `python3 annotation_app/server.py`
4. open `http://127.0.0.1:8765`
5. choose `Siwan` in the app
6. annotate and save
7. commit `data/human_eval/annotator_exports/siwan_annotations.csv`
8. push to GitHub

Example:

```bash
git add data/human_eval/annotator_exports/siwan_annotations.csv
git commit -m "Add Siwan annotations"
git push -u origin annotate-siwan
```

## What each annotator actually does in the page

For each assigned example:

1. read the source sentence
2. read the reference translation and entity mention
3. fill the shared decision fields
4. judge `gpt4o`
5. judge `gpt4o-mini`
6. pick `Preferred Model`
7. click `Save` or `Save and Next`

The page writes progress locally to the annotator export CSV, so they can stop and resume later.

## Merge annotations back into the repo sheet

After both annotation export files are in the repo, run:

```bash
python3 src/analysis/merge_annotator_exports.py
```

That writes:

- `data/human_eval/human_eval_sheet_merged.csv`

If you want to overwrite the main sheet in place after checking it:

```bash
python3 src/analysis/merge_annotator_exports.py --in-place
```
