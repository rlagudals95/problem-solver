from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import LABEL_COLUMNS, MERGED_COLUMNS, missing_columns, read_csv, read_json, write_csv
from validate_labels import validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge validated chunk label CSV files.")
    parser.add_argument("manifest", help="Path to source_manifest.json.")
    parser.add_argument("output", help="Path to write labeled_posts.csv.")
    parser.add_argument("labels", nargs="+", help="One or more label CSV files.")
    return parser.parse_args()


def ensure_output_does_not_clobber_inputs(
    manifest_path: Path,
    output_path: Path,
    label_paths: list[Path],
) -> None:
    resolved_output = output_path.resolve()
    if resolved_output == manifest_path.resolve():
        raise ValueError("output path must not match the manifest path")
    for label_path in label_paths:
        if resolved_output == label_path.resolve():
            raise ValueError(f"output path must not match a label input path: {label_path}")


def merge(manifest_path: Path, output_path: Path, label_paths: list[Path]) -> None:
    ensure_output_does_not_clobber_inputs(manifest_path, output_path, label_paths)

    errors = validate(manifest_path, label_paths)
    if errors:
        raise ValueError("\n".join(errors))

    manifest = read_json(manifest_path)
    included_records = [record for record in manifest["records"] if record["included"]]
    included_record_ids = [record["record_id"] for record in included_records]
    included_record_id_set = set(included_record_ids)
    labels_by_id: dict[str, dict[str, str]] = {}

    for label_path in label_paths:
        header, rows = read_csv(label_path)
        missing = missing_columns(header, LABEL_COLUMNS)
        if missing:
            raise ValueError(f"{label_path}: missing required columns: {', '.join(missing)}")
        for row in rows:
            record_id = row.get("record_id", "")
            if record_id in labels_by_id:
                raise ValueError(f"{label_path}: duplicate record_id {record_id}")
            labels_by_id[record_id] = row

    label_id_set = set(labels_by_id)
    missing_label_ids = sorted(included_record_id_set - label_id_set)
    unexpected_label_ids = sorted(label_id_set - included_record_id_set)
    id_errors = []
    if missing_label_ids:
        id_errors.append("missing label rows: " + ", ".join(missing_label_ids))
    if unexpected_label_ids:
        id_errors.append("unexpected label rows: " + ", ".join(unexpected_label_ids))
    if id_errors:
        raise ValueError("\n".join(id_errors))

    merged_rows: list[dict[str, str]] = []
    for record in included_records:
        record_id = record["record_id"]
        label = labels_by_id[record_id]
        merged_rows.append(
            {
                "record_id": record_id,
                "source_file": record.get("source_file", ""),
                "source_row_number": str(record.get("source_row_number", "")),
                "site": record.get("site", ""),
                "post_id": record.get("post_id", ""),
                "title": record.get("title", ""),
                "posted_at": record.get("posted_at", ""),
                "url": record.get("url", ""),
                "matched_queries": record.get("matched_queries", ""),
                **{column: label.get(column, "") for column in LABEL_COLUMNS if column != "record_id"},
            }
        )

    write_csv(output_path, MERGED_COLUMNS, merged_rows)


def main() -> int:
    args = parse_args()
    try:
        merge(Path(args.manifest), Path(args.output), [Path(path) for path in args.labels])
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"merged labels written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
