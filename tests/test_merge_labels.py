from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES_DIR, read_csv_rows, read_json, run_script


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
