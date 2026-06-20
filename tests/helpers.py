from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "community-painpoint-analysis"
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = ROOT / "tests" / "fixtures"


def run_script(
    script_name: str,
    *args: str,
    cwd: Path | None = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    script_path = SCRIPTS_DIR / script_name
    return subprocess.run(
        [sys.executable, str(script_path), *args],
        cwd=str(cwd or ROOT),
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = []
        for row_number, row in enumerate(csv.DictReader(file), start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}: malformed CSV row at line {row_number}")
            rows.append(row)
        return rows


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
