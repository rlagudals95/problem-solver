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
    codex_home_value = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    codex_home = Path(codex_home_value).expanduser()
    return codex_home / "skills"


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def resolve_install_paths(source: Path, destination: Path) -> tuple[Path, Path]:
    resolved_source = source.expanduser().resolve(strict=False)
    resolved_destination = destination.expanduser().resolve(strict=False)
    if resolved_destination == resolved_source or is_relative_to(resolved_destination, resolved_source):
        raise SystemExit(
            "refusing to install into the source skill tree: "
            f"source={resolved_source} destination={resolved_destination}"
        )
    return resolved_source, resolved_destination


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "skills" / "community-painpoint-analysis"
    destination = codex_skills_dir() / "community-painpoint-analysis"
    source, destination = resolve_install_paths(source, destination)
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
