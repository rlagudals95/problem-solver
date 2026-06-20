from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.helpers import FIXTURES_DIR, SCRIPTS_DIR, read_csv_rows, read_json, run_script

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common import MERGED_COLUMNS
from merge_labels import merge


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


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return next(csv.reader(file))


def prepare_labels(output_dir: Path) -> tuple[Path, Path, list[str]]:
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
    if prepare.returncode != 0:
        raise AssertionError(prepare.stderr)
    manifest_path = output_dir / "source_manifest.json"
    manifest = read_json(manifest_path)
    included_ids = [record["record_id"] for record in manifest["records"] if record["included"]]
    labels_path = output_dir / "labels" / "all.csv"
    write_labels(labels_path, list(reversed(included_ids)))
    return manifest_path, labels_path, included_ids


class MergeLabelsTests(unittest.TestCase):
    def test_merge_labels_preserves_manifest_order_and_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            manifest_path, labels_path, included_ids = prepare_labels(output_dir)

            result = run_script(
                "merge_labels.py",
                str(manifest_path),
                str(output_dir / "labeled_posts.csv"),
                str(labels_path),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(read_csv_header(output_dir / "labeled_posts.csv"), MERGED_COLUMNS)
            rows = read_csv_rows(output_dir / "labeled_posts.csv")
            self.assertEqual([row["record_id"] for row in rows], included_ids)
            self.assertEqual(rows[0]["site"], "clien")
            self.assertEqual(rows[0]["url"], "https://example.com/a")

    def test_merge_labels_rejects_output_path_matching_label_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            manifest_path, labels_path, _included_ids = prepare_labels(output_dir)
            original_labels = labels_path.read_text(encoding="utf-8")

            result = run_script(
                "merge_labels.py",
                str(manifest_path),
                str(labels_path),
                str(labels_path),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("output path", result.stderr)
            self.assertEqual(labels_path.read_text(encoding="utf-8"), original_labels)

    def test_merge_labels_rejects_output_path_matching_manifest_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            manifest_path, labels_path, _included_ids = prepare_labels(output_dir)
            original_manifest = manifest_path.read_text(encoding="utf-8")

            result = run_script(
                "merge_labels.py",
                str(manifest_path),
                str(manifest_path),
                str(labels_path),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("output path", result.stderr)
            self.assertEqual(manifest_path.read_text(encoding="utf-8"), original_manifest)

    def test_merge_labels_defensively_rejects_duplicate_labels_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "run"
            manifest_path, labels_path, included_ids = prepare_labels(output_dir)
            write_labels(labels_path, [*included_ids, included_ids[0]])
            output_path = output_dir / "labeled_posts.csv"

            with patch("merge_labels.validate", return_value=[]):
                with self.assertRaisesRegex(ValueError, "duplicate record_id"):
                    merge(manifest_path, output_path, [labels_path])

            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
