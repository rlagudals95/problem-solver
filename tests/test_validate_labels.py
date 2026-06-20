from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES_DIR, read_json, run_script


LABEL_FIELDNAMES = [
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


def valid_label_row(record_id: str, **overrides: str) -> dict[str, str]:
    row = {
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
    row.update(overrides)
    return row


def write_label_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    output_fieldnames = fieldnames or LABEL_FIELDNAMES
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=output_fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in output_fieldnames})


def write_malformed_label_csv(path: Path, record_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(LABEL_FIELDNAMES)
        row = valid_label_row(record_id)
        writer.writerow([row[field] for field in LABEL_FIELDNAMES] + ["extra cell"])


class ValidateLabelsTests(unittest.TestCase):
    def prepare_run(self, temp_dir: str) -> tuple[Path, list[str]]:
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
        return output_dir, included_ids

    def test_validate_labels_passes_complete_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            write_label_csv(labels, [valid_label_row(record_id) for record_id in included_ids])

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("coverage passed", result.stdout)

    def test_validate_labels_fails_when_included_record_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, _included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            write_label_csv(labels, [])

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing label rows", result.stderr)

    def test_validate_labels_reports_malformed_csv_in_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            write_malformed_label_csv(labels, included_ids[0])

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("malformed CSV", result.stderr)
            audit = (output_dir / "audit-report.md").read_text(encoding="utf-8")
            self.assertIn("- Result: coverage failed", audit)
            self.assertIn("malformed CSV", audit)

    def test_validate_labels_fails_when_required_label_column_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            fieldnames = [field for field in LABEL_FIELDNAMES if field != "confidence"]
            write_label_csv(labels, [valid_label_row(record_id) for record_id in included_ids], fieldnames=fieldnames)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required columns: confidence", result.stderr)

    def test_validate_labels_fails_when_label_column_is_extra(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            fieldnames = [*LABEL_FIELDNAMES, "extra_label"]
            write_label_csv(labels, [valid_label_row(record_id) for record_id in included_ids], fieldnames=fieldnames)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected label columns: extra_label", result.stderr)

    def test_validate_labels_fails_when_label_column_is_duplicated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            fieldnames = [*LABEL_FIELDNAMES, "confidence"]
            write_label_csv(labels, [valid_label_row(record_id) for record_id in included_ids], fieldnames=fieldnames)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate label columns: confidence", result.stderr)

    def test_validate_labels_rejects_whitespace_padded_record_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows[0]["record_id"] = f" {included_ids[0]} "
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("record_id must not contain surrounding whitespace", result.stderr)

    def test_validate_labels_fails_when_record_id_is_duplicated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows.append(valid_label_row(included_ids[0]))
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate record_id", result.stderr)

    def test_validate_labels_fails_when_record_id_is_unexpected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows.append(valid_label_row("rec_unexpected"))
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected record_id rec_unexpected", result.stderr)

    def test_validate_labels_fails_when_relevant_row_is_missing_required_field(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows[0]["evidence_quote"] = ""
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("evidence_quote is required for relevant rows", result.stderr)

    def test_validate_labels_fails_when_needs_review_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows[0]["needs_review"] = "maybe"
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("needs_review must be true or false", result.stderr)

    def test_validate_labels_fails_when_relevant_sentiment_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows[0]["sentiment"] = "화남"
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown sentiment: 화남", result.stderr)

    def test_validate_labels_fails_when_relevant_severity_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows[0]["severity"] = "심각"
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown severity: 심각", result.stderr)

    def test_validate_labels_fails_when_relevant_confidence_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows[0]["confidence"] = "확실"
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown confidence: 확실", result.stderr)

    def test_validate_labels_fails_when_irrelevant_row_is_missing_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows[0]["is_relevant"] = "false"
            rows[0]["irrelevant_reason"] = ""
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("irrelevant_reason is required for irrelevant rows", result.stderr)

    def test_validate_labels_fails_when_irrelevant_reason_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir, included_ids = self.prepare_run(temp_dir)
            labels = output_dir / "labels" / "chunk-001-labels.csv"
            rows = [valid_label_row(record_id) for record_id in included_ids]
            rows[0]["is_relevant"] = "false"
            rows[0]["irrelevant_reason"] = "기타"
            write_label_csv(labels, rows)

            result = run_script("validate_labels.py", str(output_dir / "source_manifest.json"), str(labels))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown irrelevant_reason: 기타", result.stderr)


if __name__ == "__main__":
    unittest.main()
