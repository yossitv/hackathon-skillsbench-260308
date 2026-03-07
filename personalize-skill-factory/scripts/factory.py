# /// script
# dependencies = ["anthropic"]
# ///
"""
Personalize Skill Factory — Main Pipeline

Usage:
    uv run factory.py <skill-query> <task-id> [--skip-sundial] [--skip-benchmark]

Flow:
    1. Search & fetch skill from Sundial → quarantine to staging/
    2. Safety check via Daytona sandbox
    3. User approval → customize with Claude API if needed
    4. Benchmark (before: no skill, after: with skill) via harbor
    5. Save to generated/ and link to .claude/skills/
    6. Optionally publish to Sundial
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FACTORY_ROOT = REPO_ROOT / "personalize-skill-factory"
SKILLSBENCH_DIR = FACTORY_ROOT / "skillsbench"
STAGING_DIR = FACTORY_ROOT / "skills" / "staging"
GENERATED_DIR = FACTORY_ROOT / "skills" / "generated"
SCRIPTS_DIR = FACTORY_ROOT / "scripts"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, print it, and return the result."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


# ── Step 1: Fetch from Sundial ──────────────────────────────────────────

def fetch_skill(skill_query: str) -> Path:
    """Search Sundial, add skill, quarantine to staging/."""
    from quarantine import quarantine_skill, sundial_add

    skill_name = sundial_add(skill_query)
    staging_path = quarantine_skill(skill_name)
    print(f"  Quarantined to: {staging_path}")
    return staging_path


# ── Step 2: Safety Check ────────────────────────────────────────────────

def check_safety(staging_path: Path) -> dict:
    """Run safety check via Daytona sandbox."""
    from safety_check import run_safety_check

    report = run_safety_check(staging_path)
    print(f"\n  Safety Report:")
    print(f"    Dangerous patterns: {len(report.get('dangerous_patterns', []))}")
    print(f"    Network attempts:   {len(report.get('network_attempts', []))}")
    print(f"    Files modified:     {len(report.get('files_changed', []))}")
    return report


# ── Step 3: User Approval + Customization ───────────────────────────────

def approve_and_customize(staging_path: Path, safety_report: dict) -> Path:
    """Ask user to approve, optionally customize with Claude API."""
    skill_md = (staging_path / "SKILL.md").read_text()

    if safety_report.get("dangerous_patterns"):
        print("\n  ⚠ Dangerous patterns detected:")
        for p in safety_report["dangerous_patterns"]:
            print(f"    - {p}")

    if safety_report.get("network_attempts"):
        print("\n  ⚠ Network access attempted:")
        for n in safety_report["network_attempts"]:
            print(f"    - {n}")

    print(f"\n  Current SKILL.md preview ({len(skill_md)} chars):")
    print("  " + "\n  ".join(skill_md[:500].splitlines()))
    if len(skill_md) > 500:
        print("  ...")

    choice = input("\n  [a]pprove / [c]ustomize with Claude / [r]eject? ").strip().lower()

    if choice == "r":
        print("  Rejected. Cleaning up staging.")
        import shutil
        shutil.rmtree(staging_path)
        sys.exit(0)

    if choice == "c":
        skill_md = customize_with_claude(staging_path)
        (staging_path / "SKILL.md").write_text(skill_md)
        print("  SKILL.md updated with Claude improvements.")

    # Move from staging → generated
    skill_name = staging_path.name
    dest = GENERATED_DIR / skill_name
    if dest.exists():
        import shutil
        shutil.rmtree(dest)
    staging_path.rename(dest)
    print(f"  Moved to: {dest}")
    return dest


def customize_with_claude(staging_path: Path) -> str:
    """Use Claude API to analyze and improve the skill."""
    import anthropic

    client = anthropic.Anthropic()
    skill_md = (staging_path / "SKILL.md").read_text()

    scripts_content = ""
    scripts_dir = staging_path / "scripts"
    if scripts_dir.exists():
        for f in scripts_dir.iterdir():
            if f.is_file():
                scripts_content += f"\n--- {f.name} ---\n{f.read_text()}\n"

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""Analyze this agent skill and improve it.

Current SKILL.md:
{skill_md}

Scripts bundled with the skill:
{scripts_content if scripts_content else "(none)"}

Improve the SKILL.md to be more effective:
- Make instructions clearer and more actionable
- Add edge case handling
- Ensure scripts are referenced correctly
- Keep it under 500 lines
- Follow agentskills.io spec (YAML frontmatter + markdown body)

Return ONLY the improved SKILL.md content, nothing else."""
        }]
    )
    return message.content[0].text


# ── Step 4: Benchmark ──────────────────────────────────────────────────

def run_benchmark(task_id: str, skill_path: Path | None) -> dict:
    """Run SkillsBench benchmark via harbor."""
    from benchmark import benchmark_task

    return benchmark_task(task_id, skill_path)


# ── Step 5: Link Skills ────────────────────────────────────────────────

def link_skills():
    """Run link_skills.sh to update .claude/skills/ symlinks."""
    result = run(["bash", str(SCRIPTS_DIR / "link_skills.sh")])
    if result.returncode != 0:
        print(f"  Warning: link failed: {result.stderr}")


# ── Step 6: Publish ────────────────────────────────────────────────────

def publish_skill(skill_path: Path):
    """Optionally publish to Sundial."""
    from publish import publish_to_sundial

    choice = input("\n  Publish to Sundial? [y/N] ").strip().lower()
    if choice == "y":
        publish_to_sundial(skill_path)


# ── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Personalize Skill Factory")
    parser.add_argument("skill_query", help="Skill name or search query for Sundial")
    parser.add_argument("task_id", help="SkillsBench task ID to benchmark against")
    parser.add_argument("--skip-sundial", action="store_true",
                        help="Use existing skill in staging/ instead of fetching")
    parser.add_argument("--skip-benchmark", action="store_true",
                        help="Skip harbor benchmark (useful for testing)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Personalize Skill Factory")
    print("=" * 60)

    # Step 1: Fetch
    if args.skip_sundial:
        staging_path = STAGING_DIR / args.skill_query
        if not staging_path.exists():
            print(f"  Error: {staging_path} not found in staging/")
            sys.exit(1)
        print(f"\n[1/6] Using existing skill: {staging_path}")
    else:
        print(f"\n[1/6] Fetching skill: {args.skill_query}")
        staging_path = fetch_skill(args.skill_query)

    # Step 2: Safety
    print(f"\n[2/6] Running safety check...")
    safety_report = check_safety(staging_path)

    # Step 3: Approve + Customize
    print(f"\n[3/6] Review & customize")
    generated_path = approve_and_customize(staging_path, safety_report)

    # Step 4: Benchmark
    if not args.skip_benchmark:
        print(f"\n[4/6] Benchmarking: {args.task_id}")
        print("  Running before (no skill)...")
        before = run_benchmark(args.task_id, skill_path=None)
        print(f"  Before score: {before.get('score', 'N/A')}")

        print("  Running after (with skill)...")
        after = run_benchmark(args.task_id, skill_path=generated_path)
        print(f"  After score:  {after.get('score', 'N/A')}")

        print(f"\n  {'─' * 40}")
        print(f"  Before: {before.get('score', 'N/A')}")
        print(f"  After:  {after.get('score', 'N/A')}")
        delta = (after.get('score', 0) or 0) - (before.get('score', 0) or 0)
        print(f"  Delta:  {delta:+.1f}")
        print(f"  {'─' * 40}")
    else:
        print(f"\n[4/6] Benchmark skipped")

    # Step 5: Link
    print(f"\n[5/6] Linking skills to .claude/skills/")
    link_skills()

    # Step 6: Publish
    print(f"\n[6/6] Publish")
    publish_skill(generated_path)

    print(f"\nDone. Skill saved at: {generated_path}")


if __name__ == "__main__":
    main()
