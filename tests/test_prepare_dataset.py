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


if __name__ == "__main__":
    unittest.main()
