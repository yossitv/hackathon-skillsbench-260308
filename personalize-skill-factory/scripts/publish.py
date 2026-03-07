# /// script
# dependencies = []
# ///
"""
Publish — Push a generated skill to Sundial Hub.

Usage:
    uv run publish.py <skill-path> [--visibility public] [--categories coding]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def publish_to_sundial(
    skill_path: Path,
    visibility: str = "public",
    categories: str | None = None,
    changelog: str | None = None,
) -> bool:
    """Push skill to Sundial Hub."""
    if not (skill_path / "SKILL.md").exists():
        print(f"  Error: No SKILL.md found in {skill_path}")
        return False

    cmd = ["npx", "sundial-hub", "push", str(skill_path)]
    cmd.extend(["--visibility", visibility])

    if categories:
        cmd.extend(["--categories", categories])
    if changelog:
        cmd.extend(["--changelog", changelog])

    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  Error publishing: {result.stderr}")
        return False

    print(f"  Published: {result.stdout.strip()}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Publish skill to Sundial")
    parser.add_argument("skill_path", type=Path, help="Path to generated skill")
    parser.add_argument("--visibility", default="public", choices=["public", "private"])
    parser.add_argument("--categories", default=None,
                        help="Comma-separated categories (coding,research,etc)")
    parser.add_argument("--changelog", default=None, help="Changelog message")
    args = parser.parse_args()

    if not args.skill_path.exists():
        print(f"  Error: {args.skill_path} not found")
        sys.exit(1)

    ok = publish_to_sundial(
        args.skill_path,
        visibility=args.visibility,
        categories=args.categories,
        changelog=args.changelog,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
