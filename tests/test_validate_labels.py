from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES_DIR, read_json, run_script


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
