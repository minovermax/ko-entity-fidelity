#!/usr/bin/env python3
"""Local annotation server for the Korean entity-fidelity human evaluation sheet."""

from __future__ import annotations

import csv
import json
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"
BASE_SHEET_PATH = ROOT / "data" / "human_eval" / "human_eval_sheet.csv"
EXPORT_DIR = ROOT / "data" / "human_eval" / "annotator_exports"
ASSIGNMENTS_PATH = APP_DIR / "data" / "annotator_assignments.json"

ANNOTATORS = [
    {
        "slug": "minseo",
        "name": "Minseo",
        "avatar": "/assets/minseo-avatar.png",
        "accent": "#d0624a",
    },
    {
        "slug": "siwan",
        "name": "Siwan",
        "avatar": "/assets/siwan-avatar.png",
        "accent": "#5b7f4a",
    },
]
ANNOTATOR_BY_SLUG = {annotator["slug"]: annotator for annotator in ANNOTATORS}

READ_ONLY_FIELDS = [
    "id",
    "split",
    "primary_entity_type",
    "entity_types",
    "wikidata_id",
    "source",
    "reference_translation",
    "reference_translations",
    "reference_mention",
    "reference_mentions",
    "gpt4o_prediction",
    "gpt4o_mini_prediction",
    "selection_score",
    "selection_reasons",
]
EDITABLE_FIELDS = [
    "target_rendering_strategy",
    "official_korean_title_preferred",
    "preserve_english_preferred",
    "adaptation_needed",
    "gpt4o_entity_correct",
    "gpt4o_rendering_strategy",
    "gpt4o_quality_label",
    "gpt4o_metric_likely_miss",
    "gpt4o_notes",
    "gpt4o_mini_entity_correct",
    "gpt4o_mini_rendering_strategy",
    "gpt4o_mini_quality_label",
    "gpt4o_mini_metric_likely_miss",
    "gpt4o_mini_notes",
    "preferred_model",
    "overall_comments",
]
REQUIRED_FIELDS = [
    "target_rendering_strategy",
    "official_korean_title_preferred",
    "preserve_english_preferred",
    "adaptation_needed",
    "gpt4o_entity_correct",
    "gpt4o_rendering_strategy",
    "gpt4o_quality_label",
    "gpt4o_metric_likely_miss",
    "gpt4o_mini_entity_correct",
    "gpt4o_mini_rendering_strategy",
    "gpt4o_mini_quality_label",
    "gpt4o_mini_metric_likely_miss",
]
EXPORT_FIELDNAMES = READ_ONLY_FIELDS + EDITABLE_FIELDS + [
    "annotator_slug",
    "annotator_name",
    "assignment_index",
    "annotation_completed",
    "last_updated",
]

WRITE_LOCK = threading.Lock()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def assignment_payload_matches_current_rows(payload: dict, base_rows: list[dict[str, str]]) -> bool:
    if "annotators" not in payload:
        return False
    assigned_ids: list[str] = []
    for annotator in ANNOTATORS:
        assigned_ids.extend(payload["annotators"].get(annotator["slug"], []))
    current_ids = [row["id"] for row in base_rows]
    return assigned_ids == current_ids


def build_assignments(base_rows: list[dict[str, str]]) -> dict:
    assignments = {annotator["slug"]: [] for annotator in ANNOTATORS}
    for index, row in enumerate(base_rows):
        annotator = ANNOTATORS[index % len(ANNOTATORS)]
        assignments[annotator["slug"]].append(row["id"])
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_sheet": str(BASE_SHEET_PATH.relative_to(ROOT)),
        "annotators": assignments,
    }
    ASSIGNMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ASSIGNMENTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def load_assignments(base_rows: list[dict[str, str]]) -> dict:
    if ASSIGNMENTS_PATH.exists():
        payload = json.loads(ASSIGNMENTS_PATH.read_text(encoding="utf-8"))
        if assignment_payload_matches_current_rows(payload, base_rows):
            return payload
    return build_assignments(base_rows)


def export_path_for(annotator_slug: str) -> Path:
    return EXPORT_DIR / f"{annotator_slug}_annotations.csv"


def load_export_map(annotator_slug: str) -> dict[str, dict[str, str]]:
    path = export_path_for(annotator_slug)
    if not path.exists():
        return {}
    rows = read_csv_rows(path)
    return {row["id"]: row for row in rows}


def compute_completion(row: dict[str, str]) -> bool:
    return all((row.get(field) or "").strip() for field in REQUIRED_FIELDS)


def build_annotator_rows(
    annotator_slug: str,
    base_rows: list[dict[str, str]],
    assignments: dict,
) -> list[dict[str, str]]:
    assigned_ids = assignments["annotators"][annotator_slug]
    base_by_id = {row["id"]: row for row in base_rows}
    export_map = load_export_map(annotator_slug)
    annotator = ANNOTATOR_BY_SLUG[annotator_slug]

    rows: list[dict[str, str]] = []
    for index, row_id in enumerate(assigned_ids, start=1):
        merged = dict(base_by_id[row_id])
        export_row = export_map.get(row_id, {})
        for field in EDITABLE_FIELDS:
            merged[field] = export_row.get(field, merged.get(field, ""))
        merged["annotator_slug"] = annotator_slug
        merged["annotator_name"] = annotator["name"]
        merged["assignment_index"] = str(index)
        merged["annotation_completed"] = "yes" if compute_completion(merged) else "no"
        merged["last_updated"] = export_row.get("last_updated", "")
        rows.append(merged)
    return rows


def save_annotator_row(
    annotator_slug: str,
    row_id: str,
    payload: dict[str, str],
    base_rows: list[dict[str, str]],
    assignments: dict,
) -> dict[str, str]:
    assigned_ids = assignments["annotators"][annotator_slug]
    if row_id not in assigned_ids:
        raise ValueError(f"Row {row_id} is not assigned to {annotator_slug}")

    base_by_id = {row["id"]: row for row in base_rows}
    base_row = dict(base_by_id[row_id])
    export_rows = build_annotator_rows(annotator_slug, base_rows, assignments)
    export_by_id = {row["id"]: row for row in export_rows}
    merged_row = export_by_id[row_id]

    for field in EDITABLE_FIELDS:
        if field in payload:
            merged_row[field] = str(payload[field])
        else:
            merged_row[field] = merged_row.get(field, "")

    annotator = ANNOTATOR_BY_SLUG[annotator_slug]
    merged_row["annotator_slug"] = annotator_slug
    merged_row["annotator_name"] = annotator["name"]
    merged_row["annotation_completed"] = "yes" if compute_completion(merged_row) else "no"
    merged_row["last_updated"] = datetime.now(timezone.utc).isoformat()

    ordered_rows: list[dict[str, str]] = []
    for index, assigned_id in enumerate(assigned_ids, start=1):
        if assigned_id == row_id:
            row = merged_row
        else:
            row = export_by_id[assigned_id]
        row["assignment_index"] = str(index)
        ordered_rows.append({field: row.get(field, "") for field in EXPORT_FIELDNAMES})

    write_csv_rows(export_path_for(annotator_slug), EXPORT_FIELDNAMES, ordered_rows)
    output_row = dict(base_row)
    for field in EDITABLE_FIELDS:
        output_row[field] = merged_row.get(field, "")
    output_row["annotator_slug"] = annotator_slug
    output_row["annotator_name"] = annotator["name"]
    output_row["assignment_index"] = merged_row["assignment_index"]
    output_row["annotation_completed"] = merged_row["annotation_completed"]
    output_row["last_updated"] = merged_row["last_updated"]
    return output_row


def progress_summary(rows: list[dict[str, str]]) -> dict[str, int | float]:
    completed = sum(1 for row in rows if row.get("annotation_completed") == "yes")
    total = len(rows)
    return {
        "completed": completed,
        "total": total,
        "remaining": total - completed,
        "percent": round((completed / total) * 100, 2) if total else 0.0,
    }


def session_payload(annotator_slug: str) -> dict:
    base_rows = read_csv_rows(BASE_SHEET_PATH)
    assignments = load_assignments(base_rows)
    rows = build_annotator_rows(annotator_slug, base_rows, assignments)
    progress = progress_summary(rows)
    return {
        "annotator": ANNOTATOR_BY_SLUG[annotator_slug],
        "required_fields": REQUIRED_FIELDS,
        "editable_fields": EDITABLE_FIELDS,
        "export_path": str(export_path_for(annotator_slug).relative_to(ROOT)),
        "progress": progress,
        "rows": rows,
    }


class AnnotationHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/bootstrap":
            base_rows = read_csv_rows(BASE_SHEET_PATH)
            assignments = load_assignments(base_rows)
            payload = {
                "annotators": [
                    {
                        **annotator,
                        "assigned_count": len(assignments["annotators"][annotator["slug"]]),
                        "export_path": str(export_path_for(annotator["slug"]).relative_to(ROOT)),
                    }
                    for annotator in ANNOTATORS
                ]
            }
            self.end_json(payload)
            return

        if path.startswith("/api/annotator/") and path.endswith("/session"):
            annotator_slug = path.split("/")[3]
            if annotator_slug not in ANNOTATOR_BY_SLUG:
                self.end_json({"error": "Unknown annotator"}, status=HTTPStatus.NOT_FOUND)
                return
            self.end_json(session_payload(annotator_slug))
            return

        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/annotator/") and path.endswith("/save"):
            annotator_slug = path.split("/")[3]
            if annotator_slug not in ANNOTATOR_BY_SLUG:
                self.end_json({"error": "Unknown annotator"}, status=HTTPStatus.NOT_FOUND)
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length)
                body = json.loads(raw_body.decode("utf-8"))
                row_id = body["id"]
                annotations = body.get("annotations", {})
                with WRITE_LOCK:
                    base_rows = read_csv_rows(BASE_SHEET_PATH)
                    assignments = load_assignments(base_rows)
                    row = save_annotator_row(
                        annotator_slug=annotator_slug,
                        row_id=row_id,
                        payload=annotations,
                        base_rows=base_rows,
                        assignments=assignments,
                    )
                session = session_payload(annotator_slug)
            except Exception as exc:  # noqa: BLE001
                self.end_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return

            self.end_json({"saved_row": row, "session": session})
            return

        self.end_json({"error": "Unsupported endpoint"}, status=HTTPStatus.NOT_FOUND)


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    base_rows = read_csv_rows(BASE_SHEET_PATH)
    load_assignments(base_rows)

    server = ThreadingHTTPServer(("127.0.0.1", 8765), AnnotationHandler)
    print("Annotation app running at http://127.0.0.1:8765")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
