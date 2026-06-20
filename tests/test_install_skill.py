from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

from tests.helpers import ROOT

INSTALLER = ROOT / "scripts" / "install_skill.py"


class InstallSkillTests(unittest.TestCase):
    def run_installer(self, *args: str, codex_home: str | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if codex_home is not None:
            env["CODEX_HOME"] = codex_home
        return subprocess.run(
            [sys.executable, str(INSTALLER), *args],
            cwd=str(ROOT),
            check=False,
            text=True,
            capture_output=True,
            env=env,
            timeout=30,
        )

    def test_dry_run_treats_empty_codex_home_as_unset(self) -> None:
        result = self.run_installer("--dry-run", codex_home="")

        expected_destination = Path.home() / ".codex" / "skills" / "community-painpoint-analysis"
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"destination={expected_destination}", result.stdout)

    def test_dry_run_refuses_destination_equal_to_source(self) -> None:
        result = self.run_installer("--dry-run", codex_home=str(ROOT))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to install", result.stderr)

    def test_dry_run_refuses_destination_inside_source_tree(self) -> None:
        result = self.run_installer(
            "--dry-run",
            codex_home=str(ROOT / "skills" / "community-painpoint-analysis"),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to install", result.stderr)


if __name__ == "__main__":
    unittest.main()
