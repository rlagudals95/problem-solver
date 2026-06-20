from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import LABEL_COLUMNS, missing_columns, normalize_space, parse_bool, read_csv, read_json

RELEVANT_REQUIRED_COLUMNS = [
    "jtbd",
    "primary_pain_point",
    "sentiment",
    "severity",
    "evidence_quote",
    "confidence",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate chunk label CSV files against a source manifest.")
    parser.add_argument("manifest", help="Path to source_manifest.json.")
    parser.add_argument("labels", nargs="+", help="One or more label CSV files.")
    return parser.parse_args()


def validate(manifest_path: Path, label_paths: list[Path]) -> list[str]:
    manifest = read_json(manifest_path)
    included_ids = {record["record_id"] for record in manifest["records"] if record["included"]}
    excluded_without_reason = [
        record["record_id"]
        for record in manifest["records"]
        if not record["included"] and not normalize_space(record.get("exclusion_reason", ""))
    ]
    errors: list[str] = []
    seen: dict[str, str] = {}

    if excluded_without_reason:
        errors.append("excluded rows without reasons: " + ", ".join(sorted(excluded_without_reason)))

    for label_path in label_paths:
        header, rows = read_csv(label_path)
        missing = missing_columns(header, LABEL_COLUMNS)
        if missing:
            errors.append(f"{label_path}: missing required columns: {', '.join(missing)}")
            continue

        for row_number, row in enumerate(rows, start=2):
            record_id = normalize_space(row.get("record_id", ""))
            location = f"{label_path}:{row_number}"
            if not record_id:
                errors.append(f"{location}: record_id is empty")
                continue
            if record_id not in included_ids:
                errors.append(f"{location}: unexpected record_id {record_id}")
                continue
            if record_id in seen:
                errors.append(f"{location}: duplicate record_id {record_id}; first seen at {seen[record_id]}")
                continue
            seen[record_id] = location

            is_relevant = parse_bool(row.get("is_relevant", ""))
            if is_relevant is None:
                errors.append(f"{location}: is_relevant must be true or false")
                continue
            if is_relevant:
                for column in RELEVANT_REQUIRED_COLUMNS:
                    if not normalize_space(row.get(column, "")):
                        errors.append(f"{location}: {column} is required for relevant rows")
            elif not normalize_space(row.get("irrelevant_reason", "")):
                errors.append(f"{location}: irrelevant_reason is required for irrelevant rows")

    missing_ids = sorted(included_ids - set(seen))
    if missing_ids:
        errors.append("missing label rows: " + ", ".join(missing_ids))

    return errors


def append_audit(manifest_path: Path, passed: bool, errors: list[str]) -> None:
    audit_path = manifest_path.parent / "audit-report.md"
    existing = audit_path.read_text(encoding="utf-8") if audit_path.exists() else "# Audit Report\n"
    lines = [existing.rstrip(), "", "## Label Validation", ""]
    if passed:
        lines.append("- Result: coverage passed")
    else:
        lines.append("- Result: coverage failed")
        for error in errors:
            lines.append(f"- {error}")
    audit_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    label_paths = [Path(path) for path in args.labels]
    errors = validate(manifest_path, label_paths)
    append_audit(manifest_path, not errors, errors)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("coverage passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
