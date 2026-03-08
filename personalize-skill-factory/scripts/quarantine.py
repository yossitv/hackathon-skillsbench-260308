# /// script
# dependencies = []
# ///
"""
Quarantine — Fetch skill from Sundial and isolate to staging/

Sundial installs to:
  .agents/skills/<name>/     (actual files)
  .claude/skills/<name>      (symlink → .agents/skills/<name>)

This script moves the actual files to staging/ and removes both paths
so Claude Code cannot auto-load the unverified skill.

Usage:
    uv run quarantine.py <skill-query> [--limit 5]
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure sibling scripts are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from event_log import emit as log_event

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FACTORY_ROOT = REPO_ROOT / "personalize-skill-factory"
STAGING_DIR = FACTORY_ROOT / "skills" / "staging"
AGENTS_SKILLS = REPO_ROOT / ".agents" / "skills"
CLAUDE_SKILLS = REPO_ROOT / ".claude" / "skills"


def sundial_find(query: str, limit: int = 5) -> list[dict]:
    """Search Sundial registry, return list of skill metadata."""
    result = subprocess.run(
        ["npx", "sundial-hub", "find", query, "--json", "--limit", str(limit)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  Error searching Sundial: {result.stderr}")
        sys.exit(1)

    data = json.loads(result.stdout)
    return data.get("skills", [])


def sundial_add(skill_name: str) -> str:
    """Install a skill via Sundial CLI. Returns the skill name."""
    result = subprocess.run(
        ["npx", "sundial-hub", "add", skill_name, "--claude", "--yes"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  Error installing skill: {result.stderr}")
        sys.exit(1)

    print(f"  Sundial installed: {skill_name}")
    return skill_name


def quarantine_skill(skill_name: str) -> Path:
    """Move installed skill from .agents/skills/ to staging/ and remove symlink."""
    src = AGENTS_SKILLS / skill_name
    symlink = CLAUDE_SKILLS / skill_name
    dest = STAGING_DIR / skill_name

    if not src.exists() and not symlink.exists():
        print(f"  Error: Skill not found at {src} or {symlink}")
        sys.exit(1)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        shutil.rmtree(dest)

    # Move actual files
    if src.exists():
        shutil.move(str(src), str(dest))
    elif symlink.exists() and not symlink.is_symlink():
        shutil.move(str(symlink), str(dest))

    # Remove symlink in .claude/skills/
    if symlink.is_symlink() or symlink.exists():
        symlink.unlink()

    # Clean up empty .agents/skills/ dir
    if AGENTS_SKILLS.exists() and not any(AGENTS_SKILLS.iterdir()):
        AGENTS_SKILLS.rmdir()

    return dest


def prompt_skill_selection(skills: list[dict]) -> str:
    """Let user pick a skill from search results."""
    print(f"\n  Found {len(skills)} skills:\n")
    for i, s in enumerate(skills):
        safety = s.get("safety", "unknown")
        print(f"  [{i+1}] {s['name']}")
        print(f"      {s['description'][:80]}")
        print(f"      by {s.get('author', '?')} | installs: {s.get('installs', '?')} | safety: {safety}")
        print()

    while True:
        choice = input("  Select skill number (or 'q' to quit): ").strip()
        if choice.lower() == "q":
            sys.exit(0)
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(skills):
                return skills[idx]["name"]
        except ValueError:
            pass
        print("  Invalid selection. Try again.")


def main():
    parser = argparse.ArgumentParser(description="Fetch and quarantine a Sundial skill")
    parser.add_argument("skill_query", help="Skill name or search query")
    parser.add_argument("--limit", type=int, default=5, help="Max search results")
    args = parser.parse_args()

    print(f"  Searching Sundial for: {args.skill_query}")
    skills = sundial_find(args.skill_query, limit=args.limit)

    if not skills:
        print("  No skills found.")
        sys.exit(1)

    # If exact match, use it directly
    exact = [s for s in skills if s["name"] == args.skill_query]
    if exact:
        skill_name = exact[0]["name"]
        print(f"  Exact match: {skill_name}")
    else:
        skill_name = prompt_skill_selection(skills)

    print(f"\n  Installing: {skill_name}")
    sundial_add(skill_name)

    print(f"  Quarantining to staging/...")
    staging_path = quarantine_skill(skill_name)
    print(f"  Done: {staging_path}")

    log_event("fetch", skill_name, "staging", path=str(staging_path))

    return staging_path


if __name__ == "__main__":
    main()
