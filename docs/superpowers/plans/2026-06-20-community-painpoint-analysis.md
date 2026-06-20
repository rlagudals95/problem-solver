# Community Painpoint Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a versioned Codex skill that converts large `community-analyzer` CSV exports into complete row-level labels, audit files, aggregate summaries, and evidence-backed problem-definition guidance.

**Architecture:** Keep the skill source in this repository under `skills/community-painpoint-analysis`, then install it into `${CODEX_HOME:-$HOME/.codex}/skills` with a small installer. Python scripts perform deterministic CSV, manifest, validation, merge, and summary work; `SKILL.md` instructs Codex to do codebook calibration, chunk labeling, taxonomy reconciliation, and final synthesis only after coverage gates pass.

**Tech Stack:** Python 3 standard library, `unittest`, CSV/JSON/Markdown files, Codex Skill markdown.

---

## File Structure

- Create: `skills/community-painpoint-analysis/SKILL.md`
- Create: `skills/community-painpoint-analysis/scripts/common.py`
- Create: `skills/community-painpoint-analysis/scripts/prepare_dataset.py`
- Create: `skills/community-painpoint-analysis/scripts/validate_labels.py`
- Create: `skills/community-painpoint-analysis/scripts/merge_labels.py`
- Create: `skills/community-painpoint-analysis/scripts/summarize_labels.py`
- Create: `skills/community-painpoint-analysis/references/labeling-codebook-guide.md`
- Create: `skills/community-painpoint-analysis/references/problem-definition-template.md`
- Create: `scripts/install_skill.py`
- Create: `tests/fixtures/community_posts.csv`
- Create: `tests/fixtures/community_posts_extra.csv`
- Create: `tests/helpers.py`
- Create: `tests/test_prepare_dataset.py`
- Create: `tests/test_validate_labels.py`
- Create: `tests/test_merge_labels.py`
- Create: `tests/test_summarize_labels.py`

Source-of-truth lives in this repo so changes can be reviewed and committed. The install script copies `skills/community-painpoint-analysis` into the local Codex skill directory.

## Task 1: Test Harness And Fixtures

**Files:**
- Create: `tests/fixtures/community_posts.csv`
- Create: `tests/fixtures/community_posts_extra.csv`
- Create: `tests/helpers.py`

- [ ] **Step 1: Create fixture CSV with representative source rows**

Create `tests/fixtures/community_posts.csv` with this exact content:

```csv
site,post_id,board_code,board_name,category_name,title,author,posted_at,url,view_count,like_count,dislike_count,comment_count,matched_queries,matched_search_urls,search_pages,search_excerpt,body_text,comments_text,comments_json,crawl_status,crawl_error
clien,1001,board-a,생활,,정수기 렌탈 가격이 너무 헷갈립니다,user-a,2026-06-01,https://example.com/a,120,3,0,2,정수기 렌탈,https://search.example/a,1,월 요금이 다 다르게 보여요,월 요금과 사은품 조건이 업체마다 달라서 비교가 어렵습니다.,저도 위약금 때문에 고민입니다.,"[]",ok,
clien,1002,board-a,생활,,설치 공간 때문에 렌탈이 망설여져요,user-b,2026-06-02,https://example.com/b,98,1,0,1,정수기 렌탈,https://search.example/a,1,싱크대 공간이 부족해요,집 구조상 설치가 가능한지 모르겠고 상담마다 말이 다릅니다.,설치 전에 확인해야 합니다.,"[]",ok,
fmkorea,2001,home,자유,,렌탈 광고 링크 모음,user-c,2026-06-03,https://example.com/c,500,0,0,0,정수기 렌탈,https://search.example/b,1,특가 링크,제휴 링크 모음입니다.,,"[]",ok,
fmkorea,2002,home,자유,,본문 없는 실패 글,user-d,2026-06-04,https://example.com/d,0,0,0,0,정수기 렌탈,https://search.example/b,1,,,,[],detail_failed,blocked
clien,1001,board-a,생활,,정수기 렌탈 가격이 너무 헷갈립니다,user-a,2026-06-01,https://example.com/a,120,3,0,2,정수기 렌탈,https://search.example/a,1,월 요금이 다 다르게 보여요,월 요금과 사은품 조건이 업체마다 달라서 비교가 어렵습니다.,저도 위약금 때문에 고민입니다.,"[]",ok,
```

- [ ] **Step 2: Create second fixture CSV for multi-file merge behavior**

Create `tests/fixtures/community_posts_extra.csv` with this exact content:

```csv
site,post_id,board_code,board_name,category_name,title,author,posted_at,url,view_count,like_count,dislike_count,comment_count,matched_queries,matched_search_urls,search_pages,search_excerpt,body_text,comments_text,comments_json,crawl_status,crawl_error
arca,3001,breaking,종합 속보,,관리 방문이 불편합니다,user-e,2026-06-05,https://example.com/e,80,4,0,3,정수기 렌탈,https://search.example/c,1,관리 기사 일정 맞추기가 어렵습니다,방문 관리 일정이 매번 애매해서 연차를 써야 할 때가 있습니다.,예약 시간 폭이 너무 넓어요.,"[]",ok,
```

- [ ] **Step 3: Create subprocess helper utilities**

Create `tests/helpers.py`:

```python
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "community-painpoint-analysis"
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = ROOT / "tests" / "fixtures"


def run_script(script_name: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    script_path = SCRIPTS_DIR / script_name
    return subprocess.run(
        [sys.executable, str(script_path), *args],
        cwd=str(cwd or ROOT),
        check=False,
        text=True,
        capture_output=True,
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Run the empty test suite**

Run: `python3 -m unittest discover -s tests -v`

Expected: `Ran 0 tests` or no failing tests.

- [ ] **Step 5: Commit fixtures and helpers**

```bash
git add tests/fixtures/community_posts.csv tests/fixtures/community_posts_extra.csv tests/helpers.py
git commit -m "test: add community analysis fixtures"
```

## Task 2: Shared Script Utilities

**Files:**
- Create: `skills/community-painpoint-analysis/scripts/common.py`
- Create: `tests/test_prepare_dataset.py`

- [ ] **Step 1: Write failing tests for stable IDs and source schema validation**

Create `tests/test_prepare_dataset.py` with these initial tests:

```python
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES_DIR, read_json, run_script


class PrepareDatasetTests(unittest.TestCase):
    def test_prepare_dataset_creates_manifest_with_stable_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            result = run_script(
                "prepare_dataset.py",
                "--topic",
                "rental",
                "--output-dir",
                str(output_dir),
                "--chunk-size",
                "2",
                str(FIXTURES_DIR / "community_posts.csv"),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = read_json(output_dir / "source_manifest.json")
            self.assertEqual(manifest["topic"], "rental")
            self.assertEqual(manifest["summary"]["source_rows"], 5)
            self.assertEqual(manifest["summary"]["included_rows"], 3)
            self.assertEqual(manifest["summary"]["excluded_rows"], 2)
            self.assertEqual(manifest["summary"]["chunks"], 2)

    def test_prepare_dataset_fails_when_required_columns_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_csv = Path(temp_dir) / "bad.csv"
            bad_csv.write_text("site,post_id,title\nclien,1,hello\n", encoding="utf-8")
            output_dir = Path(temp_dir) / "run"
            result = run_script(
                "prepare_dataset.py",
                "--topic",
                "bad",
                "--output-dir",
                str(output_dir),
                str(bad_csv),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required columns", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify the script is missing**

Run: `python3 -m unittest tests.test_prepare_dataset -v`

Expected: FAIL because `prepare_dataset.py` does not exist.

- [ ] **Step 3: Create shared constants and helpers**

Create `skills/community-painpoint-analysis/scripts/common.py`:

```python
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

SOURCE_COLUMNS = [
    "site",
    "post_id",
    "board_code",
    "board_name",
    "category_name",
    "title",
    "author",
    "posted_at",
    "url",
    "view_count",
    "like_count",
    "dislike_count",
    "comment_count",
    "matched_queries",
    "matched_search_urls",
    "search_pages",
    "search_excerpt",
    "body_text",
    "comments_text",
    "comments_json",
    "crawl_status",
    "crawl_error",
]

CHUNK_COLUMNS = [
    "record_id",
    "source_file",
    "source_row_number",
    *SOURCE_COLUMNS,
]

LABEL_COLUMNS = [
    "record_id",
    "is_relevant",
    "irrelevant_reason",
    "user_context",
    "journey_stage",
    "jtbd",
    "primary_pain_point",
    "secondary_pain_point",
    "sentiment",
    "severity",
    "segment_candidate",
    "evidence_quote",
    "confidence",
    "needs_review",
]

MERGED_COLUMNS = [
    "record_id",
    "source_file",
    "source_row_number",
    "site",
    "post_id",
    "title",
    "posted_at",
    "url",
    "matched_queries",
    *[column for column in LABEL_COLUMNS if column != "record_id"],
]

TEXT_COLUMNS = ["title", "search_excerpt", "body_text", "comments_text"]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = [{key: value or "" for key, value in row.items()} for row in reader]
        return list(reader.fieldnames or []), rows


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def has_meaningful_text(row: dict[str, str]) -> bool:
    return any(normalize_space(row.get(column, "")) for column in TEXT_COLUMNS)


def content_fingerprint(row: dict[str, str]) -> str:
    text = normalize_space(" ".join(row.get(column, "") for column in TEXT_COLUMNS)).lower()
    if not text:
        return ""
    return hashlib.sha1(text[:1000].encode("utf-8")).hexdigest()[:12]


def stable_key(row: dict[str, str], source_file: Path, source_row_number: int) -> str:
    site = normalize_space(row.get("site", ""))
    post_id = normalize_space(row.get("post_id", ""))
    url = normalize_space(row.get("url", ""))
    if site and post_id:
        return f"{site}:{post_id}"
    if url:
        return f"url:{url}"
    return f"source:{source_file.name}:{source_row_number}"


def stable_record_id(key: str) -> str:
    return "rec_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def missing_columns(header: list[str], required: list[str]) -> list[str]:
    present = set(header)
    return [column for column in required if column not in present]


def parse_bool(value: str) -> bool | None:
    normalized = normalize_space(value).lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    return None
```

- [ ] **Step 4: Run tests again to confirm only `prepare_dataset.py` remains missing**

Run: `python3 -m unittest tests.test_prepare_dataset -v`

Expected: FAIL because `prepare_dataset.py` does not exist.

- [ ] **Step 5: Commit shared utilities**

```bash
git add skills/community-painpoint-analysis/scripts/common.py tests/test_prepare_dataset.py
git commit -m "test: specify dataset preparation behavior"
```

## Task 3: Dataset Preparation Script

**Files:**
- Create: `skills/community-painpoint-analysis/scripts/prepare_dataset.py`
- Modify: `tests/test_prepare_dataset.py`

- [ ] **Step 1: Add tests for chunk files and explicit exclusions**

Append these tests inside `PrepareDatasetTests` before the `if __name__ == "__main__"` block:

```python
    def test_prepare_dataset_writes_chunks_with_record_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            result = run_script(
                "prepare_dataset.py",
                "--topic",
                "rental",
                "--output-dir",
                str(output_dir),
                "--chunk-size",
                "2",
                str(FIXTURES_DIR / "community_posts.csv"),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            chunks = sorted((output_dir / "chunks").glob("chunk-*.csv"))
            self.assertEqual([chunk.name for chunk in chunks], ["chunk-001.csv", "chunk-002.csv"])
            first_chunk = chunks[0].read_text(encoding="utf-8")
            self.assertIn("record_id", first_chunk)
            self.assertIn("정수기 렌탈 가격이 너무 헷갈립니다", first_chunk)

    def test_prepare_dataset_tracks_excluded_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            result = run_script(
                "prepare_dataset.py",
                "--topic",
                "rental",
                "--output-dir",
                str(output_dir),
                str(FIXTURES_DIR / "community_posts.csv"),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = read_json(output_dir / "source_manifest.json")
            reasons = sorted(record["exclusion_reason"] for record in manifest["records"] if not record["included"])
            self.assertEqual(reasons, ["duplicate_of:rec_1ddae68e5f48", "empty_content"])
            audit = (output_dir / "audit-report.md").read_text(encoding="utf-8")
            self.assertIn("Source rows: 5", audit)
            self.assertIn("Included rows: 3", audit)
            self.assertIn("Excluded rows: 2", audit)
```

- [ ] **Step 2: Run tests to verify failures**

Run: `python3 -m unittest tests.test_prepare_dataset -v`

Expected: FAIL because `prepare_dataset.py` does not exist.

- [ ] **Step 3: Implement dataset preparation**

Create `skills/community-painpoint-analysis/scripts/prepare_dataset.py`:

```python
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from common import (
    CHUNK_COLUMNS,
    SOURCE_COLUMNS,
    has_meaningful_text,
    missing_columns,
    normalize_space,
    read_csv,
    stable_key,
    stable_record_id,
    content_fingerprint,
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
            elif not has_meaningful_text(row):
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
            if record["record_id"] in ids_in_chunk:
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
```

- [ ] **Step 4: Run preparation tests**

Run: `python3 -m unittest tests.test_prepare_dataset -v`

Expected: PASS for all `PrepareDatasetTests`.

- [ ] **Step 5: Commit preparation script**

```bash
git add skills/community-painpoint-analysis/scripts/prepare_dataset.py tests/test_prepare_dataset.py
git commit -m "feat: prepare community analysis datasets"
```

## Task 4: Label Validation Script

**Files:**
- Create: `skills/community-painpoint-analysis/scripts/validate_labels.py`
- Create: `tests/test_validate_labels.py`

- [ ] **Step 1: Write failing validation tests**

Create `tests/test_validate_labels.py`:

```python
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES_DIR, read_json, run_script


def write_label_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "record_id",
        "is_relevant",
        "irrelevant_reason",
        "user_context",
        "journey_stage",
        "jtbd",
        "primary_pain_point",
        "secondary_pain_point",
        "sentiment",
        "severity",
        "segment_candidate",
        "evidence_quote",
        "confidence",
        "needs_review",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class ValidateLabelsTests(unittest.TestCase):
    def test_validate_labels_passes_complete_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            prepare = run_script(
                "prepare_dataset.py",
                "--topic",
                "rental",
                "--output-dir",
                str(output_dir),
                str(FIXTURES_DIR / "community_posts.csv"),
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            manifest = read_json(output_dir / "source_manifest.json")
            included_ids = [record["record_id"] for record in manifest["records"] if record["included"]]
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            write_label_csv(
                labels,
                [
                    {
                        "record_id": record_id,
                        "is_relevant": "true",
                        "irrelevant_reason": "",
                        "user_context": "렌탈 검토 중",
                        "journey_stage": "탐색/비교",
                        "jtbd": "When comparing rental options, I want clear conditions, so I can choose without regret.",
                        "primary_pain_point": "가격/혜택 구조 불투명",
                        "secondary_pain_point": "",
                        "sentiment": "부정",
                        "severity": "중간",
                        "segment_candidate": "비교 피로형",
                        "evidence_quote": "월 요금과 사은품 조건이 업체마다 달라서 비교가 어렵습니다.",
                        "confidence": "높음",
                        "needs_review": "false",
                    }
                    for record_id in included_ids
                ],
            )

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("coverage passed", result.stdout)

    def test_validate_labels_fails_when_included_record_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            prepare = run_script(
                "prepare_dataset.py",
                "--topic",
                "rental",
                "--output-dir",
                str(output_dir),
                str(FIXTURES_DIR / "community_posts.csv"),
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            write_label_csv(labels, [])

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing label rows", result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run validation tests to verify failure**

Run: `python3 -m unittest tests.test_validate_labels -v`

Expected: FAIL because `validate_labels.py` does not exist.

- [ ] **Step 3: Implement label validation**

Create `skills/community-painpoint-analysis/scripts/validate_labels.py`:

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import LABEL_COLUMNS, missing_columns, parse_bool, read_csv, read_json, normalize_space

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
```

- [ ] **Step 4: Run validation tests**

Run: `python3 -m unittest tests.test_validate_labels -v`

Expected: PASS for all `ValidateLabelsTests`.

- [ ] **Step 5: Commit validation script**

```bash
git add skills/community-painpoint-analysis/scripts/validate_labels.py tests/test_validate_labels.py
git commit -m "feat: validate labeled community chunks"
```

## Task 5: Label Merge Script

**Files:**
- Create: `skills/community-painpoint-analysis/scripts/merge_labels.py`
- Create: `tests/test_merge_labels.py`

- [ ] **Step 1: Write failing merge tests**

Create `tests/test_merge_labels.py`:

```python
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES_DIR, read_csv_rows, read_json, run_script


def write_labels(path: Path, record_ids: list[str]) -> None:
    fieldnames = [
        "record_id",
        "is_relevant",
        "irrelevant_reason",
        "user_context",
        "journey_stage",
        "jtbd",
        "primary_pain_point",
        "secondary_pain_point",
        "sentiment",
        "severity",
        "segment_candidate",
        "evidence_quote",
        "confidence",
        "needs_review",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for index, record_id in enumerate(record_ids, start=1):
            writer.writerow(
                {
                    "record_id": record_id,
                    "is_relevant": "true",
                    "irrelevant_reason": "",
                    "user_context": "렌탈 검토 중",
                    "journey_stage": "탐색/비교",
                    "jtbd": f"When comparing option {index}, I want clarity, so I can decide.",
                    "primary_pain_point": "가격/혜택 구조 불투명",
                    "secondary_pain_point": "",
                    "sentiment": "부정",
                    "severity": "중간",
                    "segment_candidate": "비교 피로형",
                    "evidence_quote": "비교가 어렵습니다.",
                    "confidence": "높음",
                    "needs_review": "false",
                }
            )


class MergeLabelsTests(unittest.TestCase):
    def test_merge_labels_preserves_manifest_order_and_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            prepare = run_script(
                "prepare_dataset.py",
                "--topic",
                "rental",
                "--output-dir",
                str(output_dir),
                "--chunk-size",
                "2",
                str(FIXTURES_DIR / "community_posts.csv"),
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            manifest = read_json(output_dir / "source_manifest.json")
            included_ids = [record["record_id"] for record in manifest["records"] if record["included"]]
            labels = output_dir / "labels" / "all.csv"
            write_labels(labels, list(reversed(included_ids)))

            result = run_script(
                "merge_labels.py",
                str(output_dir / "source_manifest.json"),
                str(output_dir / "labeled_posts.csv"),
                str(labels),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            rows = read_csv_rows(output_dir / "labeled_posts.csv")
            self.assertEqual([row["record_id"] for row in rows], included_ids)
            self.assertEqual(rows[0]["site"], "clien")
            self.assertEqual(rows[0]["url"], "https://example.com/a")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run merge tests to verify failure**

Run: `python3 -m unittest tests.test_merge_labels -v`

Expected: FAIL because `merge_labels.py` does not exist.

- [ ] **Step 3: Implement label merge**

Create `skills/community-painpoint-analysis/scripts/merge_labels.py`:

```python
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
```

- [ ] **Step 4: Run merge tests**

Run: `python3 -m unittest tests.test_merge_labels -v`

Expected: PASS for all `MergeLabelsTests`.

- [ ] **Step 5: Commit merge script**

```bash
git add skills/community-painpoint-analysis/scripts/merge_labels.py tests/test_merge_labels.py
git commit -m "feat: merge validated community labels"
```

## Task 6: Label Summary Script

**Files:**
- Create: `skills/community-painpoint-analysis/scripts/summarize_labels.py`
- Create: `tests/test_summarize_labels.py`

- [ ] **Step 1: Write failing summary tests**

Create `tests/test_summarize_labels.py`:

```python
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from helpers import read_json, run_script


class SummarizeLabelsTests(unittest.TestCase):
    def test_summarize_labels_counts_relevant_pain_points_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            fieldnames = [
                "record_id",
                "source_file",
                "source_row_number",
                "site",
                "post_id",
                "title",
                "posted_at",
                "url",
                "matched_queries",
                "is_relevant",
                "irrelevant_reason",
                "user_context",
                "journey_stage",
                "jtbd",
                "primary_pain_point",
                "secondary_pain_point",
                "sentiment",
                "severity",
                "segment_candidate",
                "evidence_quote",
                "confidence",
                "needs_review",
            ]
            rows = [
                {
                    "record_id": "rec_a",
                    "source_file": "source.csv",
                    "source_row_number": "2",
                    "site": "clien",
                    "post_id": "1",
                    "title": "가격 혼란",
                    "posted_at": "2026-06-01",
                    "url": "https://example.com/a",
                    "matched_queries": "정수기 렌탈",
                    "is_relevant": "true",
                    "irrelevant_reason": "",
                    "user_context": "렌탈 검토 중",
                    "journey_stage": "탐색/비교",
                    "jtbd": "When comparing rental plans, I want clear total cost, so I can choose safely.",
                    "primary_pain_point": "가격/혜택 구조 불투명",
                    "secondary_pain_point": "",
                    "sentiment": "부정",
                    "severity": "높음",
                    "segment_candidate": "비교 피로형",
                    "evidence_quote": "조건이 달라서 비교가 어렵습니다.",
                    "confidence": "높음",
                    "needs_review": "false",
                },
                {
                    "record_id": "rec_b",
                    "source_file": "source.csv",
                    "source_row_number": "3",
                    "site": "clien",
                    "post_id": "2",
                    "title": "광고",
                    "posted_at": "2026-06-02",
                    "url": "https://example.com/b",
                    "matched_queries": "정수기 렌탈",
                    "is_relevant": "false",
                    "irrelevant_reason": "promotional_or_deal",
                    "user_context": "",
                    "journey_stage": "",
                    "jtbd": "",
                    "primary_pain_point": "",
                    "secondary_pain_point": "",
                    "sentiment": "중립",
                    "severity": "낮음",
                    "segment_candidate": "",
                    "evidence_quote": "",
                    "confidence": "높음",
                    "needs_review": "false",
                },
            ]
            with labeled.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = read_json(run_dir / "label_summary.json")
            self.assertEqual(summary["total_rows"], 2)
            self.assertEqual(summary["relevant_rows"], 1)
            self.assertEqual(summary["irrelevant_rows"], 1)
            self.assertEqual(summary["pain_points"][0]["name"], "가격/혜택 구조 불투명")
            self.assertEqual(summary["pain_points"][0]["evidence_record_ids"], ["rec_a"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run summary tests to verify failure**

Run: `python3 -m unittest tests.test_summarize_labels -v`

Expected: FAIL because `summarize_labels.py` does not exist.

- [ ] **Step 3: Implement summary script**

Create `skills/community-painpoint-analysis/scripts/summarize_labels.py`:

```python
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

from common import parse_bool, read_csv, write_json

SEVERITY_SCORE = {"낮음": 1, "중간": 2, "높음": 3}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize merged community pain point labels.")
    parser.add_argument("labeled_posts", help="Path to labeled_posts.csv.")
    parser.add_argument("output", help="Path to write label_summary.json.")
    return parser.parse_args()


def top_counter(counter: Counter[str]) -> list[dict[str, int | str]]:
    return [{"name": name, "count": count} for name, count in counter.most_common() if name]


def summarize(labeled_posts: Path) -> dict:
    _, rows = read_csv(labeled_posts)
    relevant_rows = [row for row in rows if parse_bool(row.get("is_relevant", "")) is True]
    irrelevant_rows = [row for row in rows if parse_bool(row.get("is_relevant", "")) is False]

    pain_counter: Counter[str] = Counter(row.get("primary_pain_point", "") for row in relevant_rows)
    segment_counter: Counter[str] = Counter(row.get("segment_candidate", "") for row in relevant_rows)
    journey_counter: Counter[str] = Counter(row.get("journey_stage", "") for row in relevant_rows)
    sentiment_counter: Counter[str] = Counter(row.get("sentiment", "") for row in relevant_rows)
    severity_counter: Counter[str] = Counter(row.get("severity", "") for row in relevant_rows)
    irrelevant_counter: Counter[str] = Counter(row.get("irrelevant_reason", "") for row in irrelevant_rows)

    evidence_by_pain: dict[str, list[dict[str, str]]] = defaultdict(list)
    severity_by_pain: dict[str, list[int]] = defaultdict(list)
    for row in relevant_rows:
        pain = row.get("primary_pain_point", "")
        if not pain:
            continue
        severity_by_pain[pain].append(SEVERITY_SCORE.get(row.get("severity", ""), 0))
        if len(evidence_by_pain[pain]) < 5:
            evidence_by_pain[pain].append(
                {
                    "record_id": row.get("record_id", ""),
                    "quote": row.get("evidence_quote", ""),
                    "url": row.get("url", ""),
                    "title": row.get("title", ""),
                }
            )

    pain_points = []
    for pain, count in pain_counter.most_common():
        if not pain:
            continue
        scores = severity_by_pain[pain]
        average_severity = round(sum(scores) / len(scores), 2) if scores else 0
        pain_points.append(
            {
                "name": pain,
                "count": count,
                "share": round(count / len(relevant_rows), 4) if relevant_rows else 0,
                "average_severity": average_severity,
                "evidence_record_ids": [item["record_id"] for item in evidence_by_pain[pain]],
                "top_evidence": evidence_by_pain[pain],
            }
        )

    return {
        "total_rows": len(rows),
        "relevant_rows": len(relevant_rows),
        "irrelevant_rows": len(irrelevant_rows),
        "pain_points": pain_points,
        "segments": top_counter(segment_counter),
        "journey_stages": top_counter(journey_counter),
        "sentiment": top_counter(sentiment_counter),
        "severity": top_counter(severity_counter),
        "irrelevant_reasons": top_counter(irrelevant_counter),
        "needs_review_record_ids": [
            row.get("record_id", "")
            for row in rows
            if parse_bool(row.get("needs_review", "")) is True
        ],
    }


def main() -> int:
    args = parse_args()
    try:
        summary = summarize(Path(args.labeled_posts))
        write_json(Path(args.output), summary)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"summary written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run summary tests**

Run: `python3 -m unittest tests.test_summarize_labels -v`

Expected: PASS for all `SummarizeLabelsTests`.

- [ ] **Step 5: Commit summary script**

```bash
git add skills/community-painpoint-analysis/scripts/summarize_labels.py tests/test_summarize_labels.py
git commit -m "feat: summarize community painpoint labels"
```

## Task 7: Skill Instructions And References

**Files:**
- Create: `skills/community-painpoint-analysis/SKILL.md`
- Create: `skills/community-painpoint-analysis/references/labeling-codebook-guide.md`
- Create: `skills/community-painpoint-analysis/references/problem-definition-template.md`

- [ ] **Step 1: Create the skill trigger and workflow**

Create `skills/community-painpoint-analysis/SKILL.md`:

```markdown
---
name: community-painpoint-analysis
description: Use when analyzing large community-analyzer CSV exports to identify user pain points, label posts, prevent row omissions, synthesize JTBD problem definitions, and produce evidence-backed research outputs.
---

# Community Painpoint Analysis

Use this skill to convert one or more `community-analyzer` CSV exports into a traceable problem-definition package.

## Core Rule

Do not write the final `problem-definition.md` until script validation proves every source row is either labeled exactly once or explicitly excluded in `source_manifest.json`.

## Required Inputs

- One or more source CSV files from `community-analyzer`.
- A short topic name for the run.
- A workspace output directory.

## Workflow

1. Run dataset preparation:

```bash
python3 skills/community-painpoint-analysis/scripts/prepare_dataset.py \
  --topic "<topic>" \
  --output-dir "analysis-runs/YYYY-MM-DD-topic" \
  --chunk-size 100 \
  path/to/source.csv
```

2. Read `source_manifest.json` and inspect `audit-report.md`.

3. Calibrate `codebook.md` from a representative sample of 30-50 rows. Read `references/labeling-codebook-guide.md` before writing the codebook.

4. Label every chunk in `chunks/`. Save one label CSV per chunk in `labels/` using exactly these columns:

```text
record_id,is_relevant,irrelevant_reason,user_context,journey_stage,jtbd,primary_pain_point,secondary_pain_point,sentiment,severity,segment_candidate,evidence_quote,confidence,needs_review
```

5. Validate labels:

```bash
python3 skills/community-painpoint-analysis/scripts/validate_labels.py \
  analysis-runs/YYYY-MM-DD-topic/source_manifest.json \
  analysis-runs/YYYY-MM-DD-topic/labels/*.csv
```

6. If validation fails, fix the specific missing, duplicate, invalid, or empty rows. Do not synthesize yet.

7. Merge labels:

```bash
python3 skills/community-painpoint-analysis/scripts/merge_labels.py \
  analysis-runs/YYYY-MM-DD-topic/source_manifest.json \
  analysis-runs/YYYY-MM-DD-topic/labeled_posts.csv \
  analysis-runs/YYYY-MM-DD-topic/labels/*.csv
```

8. Summarize labels:

```bash
python3 skills/community-painpoint-analysis/scripts/summarize_labels.py \
  analysis-runs/YYYY-MM-DD-topic/labeled_posts.csv \
  analysis-runs/YYYY-MM-DD-topic/label_summary.json
```

9. Reconcile taxonomy drift using the merged labels. Preserve raw labels in `labeled_posts.csv`; document normalized clusters in the final Markdown.

10. Read `references/problem-definition-template.md` and write `problem-definition.md` from `labeled_posts.csv`, `label_summary.json`, `source_manifest.json`, `codebook.md`, and `audit-report.md`.

## Quality Gates

- `source_manifest.json` exists.
- `codebook.md` exists.
- Validation passes with no missing included rows.
- Excluded rows have explicit `exclusion_reason`.
- `labeled_posts.csv` exists and contains one row per included `record_id`.
- `label_summary.json` exists.
- Every major claim in `problem-definition.md` cites representative `record_id` values.
- Risks and counter-evidence are included.

## Judgment Rules

- Treat chunks as processing units, not conclusion units.
- Make final claims only from merged row-level labels.
- Prefer direct user evidence over elegant categories.
- Use `needs_review=true` for ambiguous rows.
- Do not infer market size, revenue, or willingness to pay without evidence.
- Avoid jumping from pain point to feature before stating the problem clearly.
```

- [ ] **Step 2: Create the codebook guide**

Create `skills/community-painpoint-analysis/references/labeling-codebook-guide.md`:

```markdown
# Labeling Codebook Guide

Use this reference before writing `codebook.md` for an analysis run.

## Required Columns

- `record_id`: Stable ID from chunk CSV.
- `is_relevant`: `true` when the row contains meaningful user evidence for the topic, otherwise `false`.
- `irrelevant_reason`: Required when `is_relevant=false`.
- `user_context`: The concrete situation the user is in.
- `journey_stage`: Exploration, comparison, purchase decision, installation, active use, problem occurrence, cancellation, replacement, review, or a topic-specific equivalent.
- `jtbd`: Use `When ..., I want ..., so I can ...`.
- `primary_pain_point`: Main pain evidenced by the row.
- `secondary_pain_point`: Optional second pain.
- `sentiment`: `부정`, `중립`, `긍정`, or `혼합`.
- `severity`: `낮음`, `중간`, or `높음`.
- `segment_candidate`: Repeated user type suggested by the evidence.
- `evidence_quote`: Short quote or paraphrase grounded in title, body, or comments.
- `confidence`: `낮음`, `중간`, or `높음`.
- `needs_review`: `true` for ambiguous or conflicting rows.

## Irrelevant Reasons

- `promotional_or_deal`: Ad, affiliate link, coupon, or pure deal post.
- `news_or_investor`: News, stock, investor, or market commentary without user pain.
- `generic_chatter`: Casual mention without actionable user need.
- `non_consumer_context`: Vendor, operator, or non-user context.
- `insufficient_signal`: Too little content to interpret safely.

## Severity

- `높음`: Money loss, time loss, repeated stress, contract/cancellation risk, strong distrust, or intense negative emotion.
- `중간`: Meaningful friction that slows a decision or creates uncertainty.
- `낮음`: Mild preference, curiosity, or low-stakes inconvenience.

## Confidence

- `높음`: Direct first-person experience or multiple text fields support the same interpretation.
- `중간`: Evidence is plausible but partially inferred.
- `낮음`: Sparse, ambiguous, or mostly comment-derived evidence.

## Calibration Process

1. Sample 30-50 records across source files and query terms.
2. Draft the initial taxonomy from actual user language.
3. Define inclusion and exclusion rules.
4. Add examples for each major pain point.
5. Freeze the codebook before full chunk labeling unless the user approves recalibration.
```

- [ ] **Step 3: Create the problem-definition template**

Create `skills/community-painpoint-analysis/references/problem-definition-template.md`:

```markdown
# Problem Definition Template

Use this structure for `problem-definition.md`.

## 1. Executive Summary

State the strongest problem, target segment, and why it matters. Keep this concise and cite representative `record_id` values.

## 2. Dataset Coverage

Include source row count, included row count, excluded row count, chunk count, validation result, and notable audit warnings.

## 3. Top Pain Points

For each top pain point include count, share of relevant rows, severity signal, representative quotes, and `record_id` references.

## 4. Target Segments

Name repeated user types and explain what evidence separates them.

## 5. JTBD Problem Statements

Write problem statements in `When ..., I want ..., so I can ...` format.

## 6. Opportunity Prioritization

Prioritize problems using evidence strength, pain severity, frequency, business relevance, and feasibility to investigate.

## 7. Recommended Problem Definition

Choose the first problem to investigate. Explain why this problem is stronger than the alternatives.

## 8. Risks And Counter-Evidence

List weak evidence, conflicting signals, overrepresentation risks, and rows marked `needs_review=true`.

## 9. Next Validation Questions

List interview questions, landing-page tests, manual concierge tests, or MVP experiments that would validate the problem before solution design.
```

- [ ] **Step 4: Validate skill file exists and has required frontmatter**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
skill = Path("skills/community-painpoint-analysis/SKILL.md").read_text(encoding="utf-8")
assert skill.startswith("---\n")
assert "name: community-painpoint-analysis" in skill
assert "description: Use when" in skill
print("skill frontmatter ok")
PY
```

Expected: `skill frontmatter ok`

- [ ] **Step 5: Commit skill instructions**

```bash
git add skills/community-painpoint-analysis/SKILL.md skills/community-painpoint-analysis/references/labeling-codebook-guide.md skills/community-painpoint-analysis/references/problem-definition-template.md
git commit -m "feat: add community painpoint analysis skill"
```

## Task 8: Installer And End-To-End Smoke Test

**Files:**
- Create: `scripts/install_skill.py`

- [ ] **Step 1: Create installer**

Create `scripts/install_skill.py`:

```python
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the community-painpoint-analysis Codex skill.")
    parser.add_argument("--dry-run", action="store_true", help="Print paths without copying files.")
    return parser.parse_args()


def codex_skills_dir() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills"


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "skills" / "community-painpoint-analysis"
    destination = codex_skills_dir() / "community-painpoint-analysis"
    if not source.exists():
        raise SystemExit(f"source skill not found: {source}")
    if args.dry_run:
        print(f"source={source}")
        print(f"destination={destination}")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    print(f"installed {source} -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run full unit test suite**

Run: `python3 -m unittest discover -s tests -v`

Expected: PASS for prepare, validate, merge, and summarize tests.

- [ ] **Step 3: Run end-to-end smoke commands on fixtures**

Run:

```bash
rm -rf /tmp/community-painpoint-smoke
python3 skills/community-painpoint-analysis/scripts/prepare_dataset.py \
  --topic rental \
  --output-dir /tmp/community-painpoint-smoke \
  --chunk-size 2 \
  tests/fixtures/community_posts.csv \
  tests/fixtures/community_posts_extra.csv
```

Expected: exit 0 and files under `/tmp/community-painpoint-smoke/chunks`.

- [ ] **Step 4: Create smoke label file from manifest**

Run:

```bash
python3 - <<'PY'
import csv, json
from pathlib import Path
run = Path("/tmp/community-painpoint-smoke")
manifest = json.loads((run / "source_manifest.json").read_text(encoding="utf-8"))
ids = [record["record_id"] for record in manifest["records"] if record["included"]]
labels = run / "labels" / "smoke-labels.csv"
labels.parent.mkdir(parents=True, exist_ok=True)
fieldnames = ["record_id","is_relevant","irrelevant_reason","user_context","journey_stage","jtbd","primary_pain_point","secondary_pain_point","sentiment","severity","segment_candidate","evidence_quote","confidence","needs_review"]
with labels.open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for record_id in ids:
        writer.writerow({
            "record_id": record_id,
            "is_relevant": "true",
            "irrelevant_reason": "",
            "user_context": "렌탈 검토 중",
            "journey_stage": "탐색/비교",
            "jtbd": "When comparing rental options, I want clear conditions, so I can decide without regret.",
            "primary_pain_point": "가격/혜택 구조 불투명",
            "secondary_pain_point": "",
            "sentiment": "부정",
            "severity": "중간",
            "segment_candidate": "비교 피로형",
            "evidence_quote": "비교가 어렵습니다.",
            "confidence": "높음",
            "needs_review": "false",
        })
print(labels)
PY
```

Expected: prints `/tmp/community-painpoint-smoke/labels/smoke-labels.csv`.

- [ ] **Step 5: Validate, merge, and summarize smoke labels**

Run:

```bash
python3 skills/community-painpoint-analysis/scripts/validate_labels.py \
  /tmp/community-painpoint-smoke/source_manifest.json \
  /tmp/community-painpoint-smoke/labels/smoke-labels.csv
python3 skills/community-painpoint-analysis/scripts/merge_labels.py \
  /tmp/community-painpoint-smoke/source_manifest.json \
  /tmp/community-painpoint-smoke/labeled_posts.csv \
  /tmp/community-painpoint-smoke/labels/smoke-labels.csv
python3 skills/community-painpoint-analysis/scripts/summarize_labels.py \
  /tmp/community-painpoint-smoke/labeled_posts.csv \
  /tmp/community-painpoint-smoke/label_summary.json
```

Expected: `coverage passed`, `merged labels written`, and `summary written`.

- [ ] **Step 6: Test installer dry run**

Run: `python3 scripts/install_skill.py --dry-run`

Expected: prints source and destination paths.

- [ ] **Step 7: Commit installer and smoke-ready state**

```bash
git add scripts/install_skill.py
git commit -m "chore: add community skill installer"
```

## Task 9: Final Verification And Skill Installation

**Files:**
- Modify: installed copy under `${CODEX_HOME:-$HOME/.codex}/skills/community-painpoint-analysis`

- [ ] **Step 1: Run all tests**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 2: Install the skill locally**

Run: `python3 scripts/install_skill.py`

Expected: prints `installed /path/to/problem-solver/skills/community-painpoint-analysis -> /path/to/codex/skills/community-painpoint-analysis`.

- [ ] **Step 3: Verify installed files**

Run:

```bash
test -f "${CODEX_HOME:-$HOME/.codex}/skills/community-painpoint-analysis/SKILL.md"
test -f "${CODEX_HOME:-$HOME/.codex}/skills/community-painpoint-analysis/scripts/prepare_dataset.py"
test -f "${CODEX_HOME:-$HOME/.codex}/skills/community-painpoint-analysis/references/problem-definition-template.md"
```

Expected: all commands exit 0.

- [ ] **Step 4: Check git status**

Run: `git status --short`

Expected: no uncommitted tracked changes. Test output directories under `/tmp` do not affect the repo.

- [ ] **Step 5: Record final commit**

Run: `git log --oneline -5`

Expected: shows commits for fixtures, scripts, skill docs, installer, and any plan commit.

## Self-Review Checklist

- Spec coverage: Tasks implement CSV input, manifest-first processing, stable IDs, chunking, validation, merging, summary JSON, skill workflow, codebook guide, problem definition template, installer, and tests.
- No final synthesis shortcut: `SKILL.md` blocks `problem-definition.md` until validation passes.
- No row omission gap: validation requires every included `record_id` to appear exactly once, and preparation requires every excluded row to have `exclusion_reason`.
- Type consistency: label columns are centralized in `common.py` and reused by validation and merge.
- Scope control: crawler and dashboard work remain out of scope.
