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


def merge(manifest_path: Path, output_path: Path, label_paths: list[Path]) -> None:
    errors = validate(manifest_path, label_paths)
    if errors:
        raise ValueError("\n".join(errors))

    manifest = read_json(manifest_path)
    included_records = [record for record in manifest["records"] if record["included"]]
    records_by_id = {record["record_id"]: record for record in included_records}
    labels_by_id: dict[str, dict[str, str]] = {}

    for label_path in label_paths:
        header, rows = read_csv(label_path)
        missing = missing_columns(header, LABEL_COLUMNS)
        if missing:
            raise ValueError(f"{label_path}: missing required columns: {', '.join(missing)}")
        for row in rows:
            labels_by_id[row["record_id"]] = row

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
