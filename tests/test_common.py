from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "community-painpoint-analysis"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS_DIR))

from common import read_csv, stable_key  # noqa: E402


class CommonHelperTests(unittest.TestCase):
    def test_read_csv_rejects_extra_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "bad.csv"
            csv_path.write_text("site,post_id\nclien,1,extra\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                f"{csv_path}: malformed CSV row at line 2",
            ):
                read_csv(csv_path)

    def test_stable_key_fallback_includes_source_path(self) -> None:
        row: dict[str, str] = {}

        first = stable_key(row, Path("first") / "posts.csv", 7)
        second = stable_key(row, Path("second") / "posts.csv", 7)

        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
