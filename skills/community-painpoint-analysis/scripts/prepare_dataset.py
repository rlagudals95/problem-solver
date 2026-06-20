from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from common import (
    CHUNK_COLUMNS,
    SOURCE_COLUMNS,
    content_fingerprint,
    has_meaningful_text,
    missing_columns,
    normalize_space,
    read_csv,
    stable_key,
    stable_record_id,
    write_csv,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare community CSV files for chunked pain point analysis.")
    parser.add_argument("sources", nargs="+", help="Source CSV files from community-analyzer.")
    parser.add_argument("--topic", required=True, help="Short topic name for this analysis run.")
    parser.add_argument("--output-dir", required=True, help="Analysis run output directory.")
    parser.add_argument("--chunk-size", type=int, default=100, help="Included rows per chunk.")
    return parser.parse_args()


def audit_markdown(manifest: dict) -> str:
    summary = manifest["summary"]
    return "\n".join(
        [
            "# Audit Report",
            "",
            "## Dataset Preparation",
            "",
            f"- Topic: {manifest['topic']}",
            f"- Source rows: {summary['source_rows']}",
            f"- Included rows: {summary['included_rows']}",
            f"- Excluded rows: {summary['excluded_rows']}",
            f"- Chunks: {summary['chunks']}",
            "",
        ]
    )


def has_analyzable_content(row: dict[str, str]) -> bool:
    content_row = {**row, "title": ""}
    return has_meaningful_text(content_row)


def prepare_dataset(topic: str, source_paths: list[Path], output_dir: Path, chunk_size: int) -> dict:
    if chunk_size < 1:
        raise ValueError("--chunk-size must be at least 1")

    output_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    included_rows: list[dict[str, str]] = []
    seen_keys: dict[str, str] = {}
    seen_fingerprints: dict[str, str] = {}
    source_summary: list[dict] = []

    for source_path in source_paths:
        header, rows = read_csv(source_path)
        missing = missing_columns(header, SOURCE_COLUMNS)
        if missing:
            raise ValueError(f"{source_path}: missing required columns: {', '.join(missing)}")

        source_summary.append({"path": str(source_path), "rows": len(rows)})

        for zero_index, row in enumerate(rows):
            source_row_number = zero_index + 2
            key = stable_key(row, source_path, source_row_number)
            record_id = stable_record_id(key)
            fingerprint = content_fingerprint(row)
            duplicate_of = seen_keys.get(key, "")
            near_duplicate_of = seen_fingerprints.get(fingerprint, "") if fingerprint else ""
            included = True
            exclusion_reason = ""

            if duplicate_of:
                included = False
                exclusion_reason = f"duplicate_of:{duplicate_of}"
            elif not has_analyzable_content(row):
                included = False
                exclusion_reason = "empty_content"
            else:
                seen_keys[key] = record_id
                if fingerprint and not near_duplicate_of:
                    seen_fingerprints[fingerprint] = record_id

            record = {
                "record_id": record_id,
                "source_file": str(source_path),
                "source_row_number": source_row_number,
                "stable_key": key,
                "included": included,
                "exclusion_reason": exclusion_reason,
                "duplicate_of": duplicate_of,
                "near_duplicate_of": near_duplicate_of if not duplicate_of else "",
                "chunk_file": "",
                "chunk_index": None,
                "site": row.get("site", ""),
                "post_id": row.get("post_id", ""),
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "posted_at": row.get("posted_at", ""),
                "matched_queries": row.get("matched_queries", ""),
            }

            if included:
                chunk_row = {
                    "record_id": record_id,
                    "source_file": str(source_path),
                    "source_row_number": str(source_row_number),
                    **{column: normalize_space(row.get(column, "")) for column in SOURCE_COLUMNS},
                }
                included_rows.append(chunk_row)

            records.append(record)

    for chunk_offset in range(0, len(included_rows), chunk_size):
        chunk_number = chunk_offset // chunk_size + 1
        chunk_rows = included_rows[chunk_offset : chunk_offset + chunk_size]
        chunk_name = f"chunk-{chunk_number:03d}.csv"
        chunk_path = chunks_dir / chunk_name
        write_csv(chunk_path, CHUNK_COLUMNS, chunk_rows)
        ids_in_chunk = {row["record_id"] for row in chunk_rows}
        for record in records:
            if record["included"] and record["record_id"] in ids_in_chunk:
                record["chunk_file"] = f"chunks/{chunk_name}"
                record["chunk_index"] = chunk_number

    manifest = {
        "topic": topic,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_files": source_summary,
        "summary": {
            "source_rows": len(records),
            "included_rows": sum(1 for record in records if record["included"]),
            "excluded_rows": sum(1 for record in records if not record["included"]),
            "chunks": (len(included_rows) + chunk_size - 1) // chunk_size if included_rows else 0,
        },
        "records": records,
    }

    write_json(output_dir / "source_manifest.json", manifest)
    (output_dir / "audit-report.md").write_text(audit_markdown(manifest), encoding="utf-8")
    return manifest


def main() -> int:
    args = parse_args()
    try:
        prepare_dataset(
            topic=args.topic,
            source_paths=[Path(source) for source in args.sources],
            output_dir=Path(args.output_dir),
            chunk_size=args.chunk_size,
        )
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
