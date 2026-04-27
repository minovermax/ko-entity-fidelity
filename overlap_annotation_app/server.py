#!/usr/bin/env python3
"""Separate runner for the 30-example overlap agreement annotation page."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
OVERLAP_SHEET = ROOT / "data" / "human_eval" / "overlap" / "overlap_annotation_sheet.csv"

sys.path.insert(0, str(ROOT))

if not OVERLAP_SHEET.exists():
    from src.analysis.build_overlap_annotation_sheet import main as build_overlap_sheet

    build_overlap_sheet()

os.environ.setdefault("ANNOTATION_BASE_SHEET", str(OVERLAP_SHEET))
os.environ.setdefault(
    "ANNOTATION_EXPORT_DIR",
    str(ROOT / "data" / "human_eval" / "overlap" / "annotator_exports"),
)
os.environ.setdefault(
    "ANNOTATION_ASSIGNMENTS_PATH",
    str(APP_DIR / "data" / "overlap_annotator_assignments.json"),
)
os.environ.setdefault("ANNOTATION_ASSIGNMENT_MODE", "all")
os.environ.setdefault("ANNOTATION_PORT", "8766")
os.environ.setdefault("ANNOTATION_APP_EYEBROW", "EntityLens Overlap Annotation")
os.environ.setdefault("ANNOTATION_APP_TITLE", "Annotate the same 30 examples for agreement.")
os.environ.setdefault(
    "ANNOTATION_APP_SUBCOPY",
    "Both Minseo and Siwan should complete every example on this page. "
    "Your answers are saved separately so we can compute inter-annotator agreement.",
)
os.environ.setdefault("ANNOTATION_QUEUE_TITLE", "Overlap Examples")
os.environ.setdefault("ANNOTATION_ASSIGNED_LABEL", "overlap examples")

from annotation_app.server import main


if __name__ == "__main__":
    main()
