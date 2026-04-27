# Overlap Annotation App

This is the separate page for the 30-example inter-annotator agreement round.

Both Minseo and Siwan should annotate all 30 examples. The app saves their answers into separate overlap export files, so we can calculate agreement afterward.

This is different from the first annotation round. In the first round, each person had separate examples. In this overlap round, both people annotate the exact same examples.

The 30 overlap examples are fresh examples selected from the validation data outside the first 200-example annotation sheet. You should not be re-annotating your own earlier examples.

## Start From The Latest Repo

From your local clone:

```bash
git checkout main
git pull origin main
```

If you do not have the repo yet:

```bash
git clone https://github.com/minovermax/ko-entity-fidelity.git
cd ko-entity-fidelity
```

## Run

From the repo root:

```bash
python3 overlap_annotation_app/server.py
```

Open:

```text
http://127.0.0.1:8766
```

Leave the terminal running while you annotate. When you are done, press `Ctrl-C` in the terminal to stop the server.

## What Each Person Does

1. Choose your own name.
2. Annotate all 30 overlap examples.
3. Save as you go.
4. Commit only your overlap export file.

Minseo export:

```text
data/human_eval/overlap/annotator_exports/minseo_annotations.csv
```

Siwan export:

```text
data/human_eval/overlap/annotator_exports/siwan_annotations.csv
```

## Git Commands

For Minseo:

```bash
git checkout main
git pull origin main
git checkout -b overlap-minseo
python3 overlap_annotation_app/server.py
git add data/human_eval/overlap/annotator_exports/minseo_annotations.csv
git commit -m "Add Minseo overlap annotations"
git push -u origin overlap-minseo
```

For Siwan:

```bash
git checkout main
git pull origin main
git checkout -b overlap-siwan
python3 overlap_annotation_app/server.py
git add data/human_eval/overlap/annotator_exports/siwan_annotations.csv
git commit -m "Add Siwan overlap annotations"
git push -u origin overlap-siwan
```

After pushing, open a pull request on GitHub or tell Min that the branch is ready.

## Do Not Commit These

Do not commit the main annotation sheet again for this overlap round:

```text
data/human_eval/human_eval_sheet.csv
```

Do not commit the other person's export file.

## Compute Agreement

After both overlap export files are merged into `main`, run:

```bash
git checkout main
git pull origin main
python3 src/analysis/compute_inter_annotator_agreement.py
```

That writes:

```text
outputs/metrics/inter_annotator_agreement.csv
docs/notes/inter_annotator_agreement.md
```

Those two files can then be used in the final report.
