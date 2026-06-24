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

    def test_read_csv_accepts_large_text_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "large.csv"
            large_body = "고양이 병원 후기 " * 25000
            csv_path.write_text(f"site,body_text\ncafe,{large_body}\n", encoding="utf-8")

            _, rows = read_csv(csv_path)

            self.assertEqual(rows[0]["body_text"], large_body)

    def test_stable_key_fallback_includes_source_path(self) -> None:
        row: dict[str, str] = {}

        first = stable_key(row, Path("first") / "posts.csv", 7)
        second = stable_key(row, Path("second") / "posts.csv", 7)

        self.assertNotEqual(first, second)

    def test_stable_key_includes_board_code_and_url(self) -> None:
        row = {
            "site": "clien",
            "post_id": "1001",
            "board_code": "board-a",
            "url": "https://example.com/a",
        }

        key = stable_key(row, Path("posts.csv"), 2)

        self.assertEqual(key, "clien:board-a:1001:url:https://example.com/a")

    def test_stable_key_distinguishes_same_post_id_across_boards_and_urls(self) -> None:
        base_row = {
            "site": "community",
            "post_id": "1001",
            "board_code": "board-a",
            "url": "https://example.com/a",
        }
        other_board = {**base_row, "board_code": "board-b"}
        other_url = {**base_row, "url": "https://example.com/b"}

        self.assertNotEqual(stable_key(base_row, Path("posts.csv"), 2), stable_key(other_board, Path("posts.csv"), 3))
        self.assertNotEqual(stable_key(base_row, Path("posts.csv"), 2), stable_key(other_url, Path("posts.csv"), 4))


if __name__ == "__main__":
    unittest.main()
