from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the community-painpoint-analysis Codex skill.")
    parser.add_argument("--dry-run", action="store_true", help="Print paths without copying files.")
    return parser.parse_args()


def codex_skills_dir() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills"


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "skills" / "community-painpoint-analysis"
    destination = codex_skills_dir() / "community-painpoint-analysis"
    if not source.exists():
        raise SystemExit(f"source skill not found: {source}")
    if args.dry_run:
        print(f"source={source}")
        print(f"destination={destination}")
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    print(f"installed {source} -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
