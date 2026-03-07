# /// script
# dependencies = ["anthropic", "daytona-sdk"]
# ///
"""
Personalize Skill Factory — Main Pipeline

Usage:
    uv run personalize-skill-factory/scripts/factory.py <skill-query> <task-id>

Flow:
    staging → developing → generated

    1. Fetch from Sundial → quarantine to staging/
    2. Safety check (Claude static + Daytona dynamic)
    3. Approve → move to developing/
    4. Customize + benchmark loop in developing/
    5. Finalize → move to generated/, link to .claude/skills/
    6. Optionally publish to Sundial
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure sibling scripts are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FACTORY_ROOT = REPO_ROOT / "personalize-skill-factory"
SKILLSBENCH_DIR = FACTORY_ROOT / "skillsbench"
STAGING_DIR = FACTORY_ROOT / "skills" / "staging"
DEVELOPING_DIR = FACTORY_ROOT / "skills" / "developing"
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
    print(f"    Recommendation:     {report.get('recommendation', '?')}")
    print(f"    Dangerous patterns: {len(report.get('dangerous_patterns', []))}")
    print(f"    Network URLs:       {len(report.get('network_urls', []))}")
    if report.get("dynamic_skipped"):
        print(f"    Dynamic analysis:   skipped ({report.get('dynamic_reason', '')})")
    return report


# ── Step 3: Approve → Move to developing/ ──────────────────────────────

def approve_to_developing(staging_path: Path, safety_report: dict) -> Path:
    """Show safety report, ask user to approve, move to developing/."""
    skill_md = (staging_path / "SKILL.md").read_text()

    if safety_report.get("dangerous_patterns"):
        print("\n  Dangerous patterns:")
        for p in safety_report["dangerous_patterns"]:
            print(f"    - {p}")

    if safety_report.get("network_urls"):
        print("\n  Network URLs found:")
        for u in safety_report["network_urls"]:
            print(f"    - {u}")

    print(f"\n  SKILL.md preview ({len(skill_md)} chars):")
    for line in skill_md[:500].splitlines():
        print(f"    {line}")
    if len(skill_md) > 500:
        print("    ...")

    choice = input("\n  [a]pprove to developing / [r]eject? ").strip().lower()

    if choice == "r":
        print("  Rejected. Cleaning up staging.")
        shutil.rmtree(staging_path)
        sys.exit(0)

    # Move staging → developing
    DEVELOPING_DIR.mkdir(parents=True, exist_ok=True)
    dest = DEVELOPING_DIR / staging_path.name
    if dest.exists():
        shutil.rmtree(dest)
    staging_path.rename(dest)
    print(f"  Moved to developing: {dest}")
    return dest


# ── Step 4: Customize + Benchmark Loop ──────────────────────────────────

def develop_loop(dev_path: Path, task_id: str):
    """Iterate: customize with Claude → benchmark → repeat."""
    from benchmark import benchmark_task, save_benchmark_result, show_benchmark_history

    iteration = 0
    while True:
        iteration += 1
        print(f"\n  ── Iteration {iteration} ──")
        print(f"  [b]enchmark / [c]ustomize with Claude / [e]dit manually / [d]one")
        choice = input("  > ").strip().lower()

        if choice == "d":
            break

        if choice == "b":
            print(f"  Running benchmark: {task_id}...")
            result = benchmark_task(task_id, skill_path=dev_path)
            save_benchmark_result(dev_path, task_id, result, label=f"iter-{iteration}")
            print(f"  Score: {result.get('score', 'N/A')}")
            show_benchmark_history(dev_path)

        elif choice == "c":
            print("  Customizing with Claude API...")
            new_md = customize_with_claude(dev_path, task_id)
            (dev_path / "SKILL.md").write_text(new_md)
            print("  SKILL.md updated.")
            # Show diff size
            print(f"  New SKILL.md: {len(new_md)} chars")

        elif choice == "e":
            print(f"  Edit the file directly:")
            print(f"    {dev_path / 'SKILL.md'}")
            input("  Press Enter when done editing...")

        else:
            print("  Invalid choice.")


def customize_with_claude(dev_path: Path, task_id: str = "") -> str:
    """Use Claude API to improve the skill, optionally using benchmark failure context."""
    import anthropic

    client = anthropic.Anthropic()
    skill_md = (dev_path / "SKILL.md").read_text()

    # Gather scripts content
    scripts_content = ""
    scripts_dir = dev_path / "scripts"
    if scripts_dir.exists():
        for f in scripts_dir.iterdir():
            if f.is_file():
                scripts_content += f"\n--- {f.name} ---\n{f.read_text()}\n"

    # Gather benchmark history for context
    benchmark_context = ""
    benchmarks_dir = dev_path / "_benchmarks"
    if benchmarks_dir.exists():
        runs = sorted(benchmarks_dir.glob("run-*.json"))
        if runs:
            latest = json.loads(runs[-1].read_text())
            benchmark_context = f"\nLatest benchmark result:\n{json.dumps(latest, indent=2)}\n"

    # Gather task instruction for context
    task_context = ""
    if task_id:
        task_instruction = SKILLSBENCH_DIR / "tasks-no-skills" / task_id / "instruction.md"
        if task_instruction.exists():
            task_context = f"\nTask instruction ({task_id}):\n{task_instruction.read_text()[:2000]}\n"

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""Analyze this agent skill and improve it for better benchmark performance.

Current SKILL.md:
{skill_md}

Scripts bundled with the skill:
{scripts_content if scripts_content else "(none)"}
{benchmark_context}
{task_context}

Improve the SKILL.md:
- Make instructions clearer and more actionable for the target task
- Add specific step-by-step guidance
- Add edge case handling
- Ensure scripts are referenced correctly
- Keep it under 500 lines
- Follow agentskills.io spec (YAML frontmatter + markdown body)

Return ONLY the improved SKILL.md content, nothing else."""
        }]
    )
    return message.content[0].text


# ── Step 5: Finalize → generated/ ──────────────────────────────────────

def finalize(dev_path: Path) -> Path:
    """Move from developing/ to generated/."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    dest = GENERATED_DIR / dev_path.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(dev_path, dest)
    # Keep developing copy for reference, or clean up
    shutil.rmtree(dev_path)
    print(f"  Finalized: {dest}")
    return dest


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
    parser.add_argument("--resume", action="store_true",
                        help="Resume developing an existing skill in developing/")
    args = parser.parse_args()

    print("=" * 60)
    print("  Personalize Skill Factory")
    print("=" * 60)

    if args.resume:
        # Resume from developing/
        dev_path = DEVELOPING_DIR / args.skill_query
        if not dev_path.exists():
            print(f"  Error: {dev_path} not found in developing/")
            sys.exit(1)
        print(f"\n  Resuming: {dev_path}")
    else:
        # Step 1: Fetch
        if args.skip_sundial:
            staging_path = STAGING_DIR / args.skill_query
            if not staging_path.exists():
                print(f"  Error: {staging_path} not found in staging/")
                sys.exit(1)
            print(f"\n[1/6] Using existing: {staging_path}")
        else:
            print(f"\n[1/6] Fetching: {args.skill_query}")
            staging_path = fetch_skill(args.skill_query)

        # Step 2: Safety
        print(f"\n[2/6] Safety check...")
        safety_report = check_safety(staging_path)

        # Step 3: Approve → developing
        print(f"\n[3/6] Review & approve")
        dev_path = approve_to_developing(staging_path, safety_report)

    # Step 4: Develop loop
    print(f"\n[4/6] Develop: customize + benchmark")
    develop_loop(dev_path, args.task_id)

    # Step 5: Finalize
    print(f"\n[5/6] Finalizing...")
    generated_path = finalize(dev_path)
    link_skills()

    # Step 6: Publish
    print(f"\n[6/6] Publish")
    publish_skill(generated_path)

    print(f"\nDone. Skill saved at: {generated_path}")


if __name__ == "__main__":
    main()
