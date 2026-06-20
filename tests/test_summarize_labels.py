from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tests.helpers import read_json, run_script


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
