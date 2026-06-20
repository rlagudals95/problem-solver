from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import SCRIPTS_DIR, read_json, run_script

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common import MERGED_COLUMNS


def labeled_row(record_id: str, **overrides: str) -> dict[str, str]:
    row = {
        "record_id": record_id,
        "source_file": "source.csv",
        "source_row_number": "2",
        "site": "clien",
        "post_id": record_id,
        "title": "가격 혼란",
        "posted_at": "2026-06-01",
        "url": f"https://example.com/{record_id}",
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
    }
    row.update(overrides)
    return row


def write_labeled_csv(
    path: Path,
    rows: list[dict[str, str]],
    fieldnames: list[str] | None = None,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames or MERGED_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


class SummarizeLabelsTests(unittest.TestCase):
    def test_summarize_labels_counts_relevant_pain_points_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            rows = [
                labeled_row(
                    "rec_a",
                    title="가격 혼란",
                    post_id="1",
                    url="https://example.com/a",
                ),
                labeled_row(
                    "rec_b",
                    title="광고",
                    post_id="2",
                    posted_at="2026-06-02",
                    url="https://example.com/b",
                    is_relevant="false",
                    irrelevant_reason="promotional_or_deal",
                    user_context="",
                    journey_stage="",
                    jtbd="",
                    primary_pain_point="",
                    secondary_pain_point="",
                    sentiment="중립",
                    severity="낮음",
                    segment_candidate="",
                    evidence_quote="",
                    confidence="높음",
                    needs_review="false",
                ),
            ]
            write_labeled_csv(labeled, rows)

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = read_json(run_dir / "label_summary.json")
            self.assertEqual(summary["total_rows"], 2)
            self.assertEqual(summary["relevant_rows"], 1)
            self.assertEqual(summary["irrelevant_rows"], 1)
            self.assertEqual(summary["pain_points"][0]["name"], "가격/혜택 구조 불투명")
            self.assertEqual(summary["pain_points"][0]["evidence_record_ids"], ["rec_a"])
            self.assertEqual(summary["confidence"][0], {"name": "높음", "count": 1})

    def test_summarize_labels_rejects_unexpected_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            fieldnames = [column for column in MERGED_COLUMNS if column != "confidence"]
            write_labeled_csv(labeled, [labeled_row("rec_a")], fieldnames=fieldnames)

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected merged columns", result.stderr)

    def test_summarize_labels_rejects_invalid_is_relevant_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(labeled, [labeled_row("rec_a", is_relevant="maybe")])

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid is_relevant", result.stderr)

    def test_summarize_labels_rejects_invalid_needs_review_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(labeled, [labeled_row("rec_a", needs_review="maybe")])

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid needs_review", result.stderr)

    def test_summarize_labels_rejects_missing_required_relevant_fields(self) -> None:
        for field in ["primary_pain_point", "severity", "evidence_quote", "confidence"]:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temp_dir:
                    run_dir = Path(temp_dir)
                    labeled = run_dir / "labeled_posts.csv"
                    write_labeled_csv(labeled, [labeled_row("rec_a", **{field: ""})])

                    result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f"{field} is required", result.stderr)

    def test_summarize_labels_rejects_unknown_relevant_severity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(labeled, [labeled_row("rec_a", severity="심각")])

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown severity", result.stderr)

    def test_summarize_labels_rejects_unknown_relevant_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(labeled, [labeled_row("rec_a", confidence="불명")])

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown confidence", result.stderr)

    def test_summarize_labels_rejects_irrelevant_row_missing_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(
                labeled,
                [
                    labeled_row(
                        "rec_a",
                        is_relevant="false",
                        irrelevant_reason="",
                        primary_pain_point="",
                        severity="",
                        evidence_quote="",
                        confidence="",
                    ),
                ],
            )

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("irrelevant_reason is required", result.stderr)

    def test_summarize_labels_includes_needs_review_record_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(
                labeled,
                [
                    labeled_row("rec_a", needs_review="true"),
                    labeled_row(
                        "rec_b",
                        is_relevant="false",
                        irrelevant_reason="not_problem_discussion",
                        primary_pain_point="",
                        severity="",
                        evidence_quote="",
                        confidence="",
                        needs_review="true",
                    ),
                ],
            )

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = read_json(run_dir / "label_summary.json")
            self.assertEqual(summary["needs_review_record_ids"], ["rec_a", "rec_b"])

    def test_summarize_labels_rejects_output_matching_input_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(labeled, [labeled_row("rec_a")])
            original_labeled = labeled.read_text(encoding="utf-8")

            result = run_script("summarize_labels.py", str(labeled), str(labeled))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("output path must not match", result.stderr)
            self.assertEqual(labeled.read_text(encoding="utf-8"), original_labeled)

    def test_summarize_labels_orders_top_evidence_by_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(
                labeled,
                [
                    labeled_row("rec_low_high", severity="낮음", confidence="높음"),
                    labeled_row("rec_mid_low", severity="중간", confidence="낮음"),
                    labeled_row("rec_high_low", severity="높음", confidence="낮음"),
                    labeled_row("rec_high_high", severity="높음", confidence="높음"),
                    labeled_row("rec_high_mid", severity="높음", confidence="중간"),
                    labeled_row("rec_mid_high", severity="중간", confidence="높음"),
                ],
            )

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = read_json(run_dir / "label_summary.json")
            self.assertEqual(
                summary["pain_points"][0]["evidence_record_ids"],
                ["rec_high_high", "rec_high_mid", "rec_high_low", "rec_mid_high", "rec_mid_low"],
            )

    def test_summarize_labels_counts_multiple_pain_points_with_share_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            labeled = run_dir / "labeled_posts.csv"
            write_labeled_csv(
                labeled,
                [
                    labeled_row("rec_price_a", primary_pain_point="가격/혜택 구조 불투명"),
                    labeled_row("rec_install", primary_pain_point="설치 가능 여부 불안"),
                    labeled_row("rec_price_b", primary_pain_point="가격/혜택 구조 불투명"),
                ],
            )

            result = run_script("summarize_labels.py", str(labeled), str(run_dir / "label_summary.json"))

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = read_json(run_dir / "label_summary.json")
            self.assertEqual(
                [(item["name"], item["count"], item["share"]) for item in summary["pain_points"]],
                [
                    ("가격/혜택 구조 불투명", 2, 0.6667),
                    ("설치 가능 여부 불안", 1, 0.3333),
                ],
            )


if __name__ == "__main__":
    unittest.main()
