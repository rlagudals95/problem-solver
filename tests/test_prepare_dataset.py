from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES_DIR, read_json, run_script


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
            excluded_records = [record for record in manifest["records"] if not record["included"]]
            reasons = sorted(record["exclusion_reason"] for record in excluded_records)
            self.assertEqual(reasons, ["duplicate_of:rec_1ddae68e5f48", "empty_content"])
            self.assertTrue(all(record["chunk_file"] == "" for record in excluded_records))
            self.assertTrue(all(record["chunk_index"] is None for record in excluded_records))
            audit = (output_dir / "audit-report.md").read_text(encoding="utf-8")
            self.assertIn("Source rows: 5", audit)
            self.assertIn("Included rows: 3", audit)
            self.assertIn("Excluded rows: 2", audit)


if __name__ == "__main__":
    unittest.main()
