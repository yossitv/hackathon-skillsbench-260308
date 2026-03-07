# /// script
# dependencies = []
# ///
"""
Benchmark — Run SkillsBench tasks via Harbor and compare scores.

Before run: uses tasks-no-skills/<task> (no skill injected)
After run:  copies skill into tasks-no-skills/<task>/environment/skills/ then runs

Usage:
    uv run benchmark.py <task-id> [--skill-path <path>] [--model <model>]
    uv run benchmark.py <task-id> --dev <skill-name>   # auto-inject from developing/

Output: dict with score (0 or 1), test details from ctrf.json
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FACTORY_ROOT = Path(__file__).resolve().parent.parent
SKILLSBENCH_DIR = FACTORY_ROOT / "skillsbench"
TASKS_NO_SKILLS = SKILLSBENCH_DIR / "tasks-no-skills"
DEVELOPING_DIR = FACTORY_ROOT / "skills" / "developing"


def validate_task(task_id: str) -> Path:
    """Check task exists and return its path."""
    task_path = TASKS_NO_SKILLS / task_id
    if not task_path.exists():
        print(f"  Error: Task not found: {task_path}")
        print(f"  Available tasks:")
        for t in sorted(TASKS_NO_SKILLS.iterdir()):
            if t.is_dir():
                print(f"    - {t.name}")
        sys.exit(1)
    return task_path


def inject_skill(task_path: Path, skill_path: Path) -> Path:
    """Copy skill into task's environment/skills/ directory."""
    dest = task_path / "environment" / "skills" / skill_path.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(skill_path, dest)
    print(f"  Injected skill: {skill_path.name} → {dest}")
    return dest


def remove_skill(injected_path: Path):
    """Remove injected skill after benchmark."""
    if injected_path.exists():
        shutil.rmtree(injected_path)
        print(f"  Cleaned up: {injected_path}")


def run_harbor(task_id: str, model: str = "anthropic/claude-sonnet-4-20250514") -> dict:
    """Execute harbor run and parse results."""
    cmd = [
        "uv", "run", "harbor", "run",
        "-p", f"tasks-no-skills/{task_id}",
        "-a", "claude-code",
        "-m", model,
    ]

    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(SKILLSBENCH_DIR),
        timeout=900,  # 15 min max
    )

    if result.returncode != 0:
        print(f"  Harbor stderr: {result.stderr[:500]}")

    return parse_results(task_id, result)


def parse_results(task_id: str, harbor_result: subprocess.CompletedProcess) -> dict:
    """Parse harbor output, reward.txt, and ctrf.json."""
    report = {
        "task_id": task_id,
        "score": None,
        "tests": None,
        "harbor_returncode": harbor_result.returncode,
        "harbor_stdout": harbor_result.stdout[-1000:] if harbor_result.stdout else "",
        "harbor_stderr": harbor_result.stderr[-500:] if harbor_result.stderr else "",
    }

    # Try to find reward.txt and ctrf.json from harbor output
    # Harbor typically writes to /logs/verifier/ inside container
    # but also may output the score in stdout
    stdout = harbor_result.stdout or ""

    # Parse score from stdout if available
    for line in stdout.splitlines():
        line = line.strip()
        if line in ("0", "1"):
            report["score"] = int(line)
        if "reward" in line.lower() and ("0" in line or "1" in line):
            try:
                report["score"] = int(line.split()[-1])
            except (ValueError, IndexError):
                pass

    # Try to parse ctrf.json if harbor left it accessible
    # This path may vary based on harbor's output location
    for ctrf_candidate in [
        SKILLSBENCH_DIR / "logs" / task_id / "verifier" / "ctrf.json",
        SKILLSBENCH_DIR / ".harbor" / task_id / "ctrf.json",
    ]:
        if ctrf_candidate.exists():
            try:
                report["tests"] = json.loads(ctrf_candidate.read_text())
            except json.JSONDecodeError:
                pass
            break

    return report


def save_benchmark_result(skill_path: Path, task_id: str, result: dict, label: str = ""):
    """Save benchmark result to skill's _benchmarks/ directory."""
    benchmarks_dir = skill_path / "_benchmarks"
    benchmarks_dir.mkdir(exist_ok=True)

    # Find next run number
    existing = sorted(benchmarks_dir.glob("run-*.json"))
    next_num = len(existing) + 1

    record = {
        "run": next_num,
        "task_id": task_id,
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": result.get("score"),
        "harbor_returncode": result.get("harbor_returncode"),
    }
    if result.get("tests"):
        record["tests"] = result["tests"]

    out_path = benchmarks_dir / f"run-{next_num:03d}.json"
    out_path.write_text(json.dumps(record, indent=2))
    print(f"  Saved: {out_path}")
    return record


def benchmark_task(task_id: str, skill_path: Path | None, model: str = "anthropic/claude-sonnet-4-20250514") -> dict:
    """Run a single benchmark. If skill_path is given, inject it first."""
    task_path = validate_task(task_id)
    injected = None

    try:
        if skill_path:
            injected = inject_skill(task_path, skill_path)

        result = run_harbor(task_id, model)
        return result

    finally:
        if injected:
            remove_skill(injected)


def dev_benchmark(task_id: str, skill_name: str, model: str = "anthropic/claude-sonnet-4-20250514") -> dict:
    """Run benchmark using a skill from developing/, save results to _benchmarks/."""
    skill_path = DEVELOPING_DIR / skill_name
    if not skill_path.exists():
        print(f"  Error: {skill_path} not found in developing/")
        print(f"  Available:")
        for d in sorted(DEVELOPING_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                print(f"    - {d.name}")
        sys.exit(1)

    result = benchmark_task(task_id, skill_path=skill_path, model=model)
    save_benchmark_result(skill_path, task_id, result, label="dev")
    return result


def show_benchmark_history(skill_path: Path):
    """Print benchmark history for a skill."""
    benchmarks_dir = skill_path / "_benchmarks"
    if not benchmarks_dir.exists():
        print("  No benchmarks yet.")
        return

    runs = sorted(benchmarks_dir.glob("run-*.json"))
    if not runs:
        print("  No benchmarks yet.")
        return

    print(f"\n  Benchmark History: {skill_path.name}")
    print(f"  {'─' * 50}")
    print(f"  {'Run':<6} {'Task':<35} {'Score':<8} {'Label'}")
    print(f"  {'─' * 50}")
    for run_file in runs:
        r = json.loads(run_file.read_text())
        score = r.get("score", "N/A")
        print(f"  {r.get('run', '?'):<6} {r.get('task_id', '?'):<35} {str(score):<8} {r.get('label', '')}")
    print(f"  {'─' * 50}")


def main():
    parser = argparse.ArgumentParser(description="Run SkillsBench benchmark")
    parser.add_argument("task_id", help="Task ID from tasks-no-skills/")
    parser.add_argument("--skill-path", type=Path, default=None,
                        help="Path to skill to inject (omit for baseline)")
    parser.add_argument("--model", default="anthropic/claude-sonnet-4-20250514",
                        help="Model to use")
    parser.add_argument("--compare", type=Path, default=None,
                        help="Run before (no skill) + after (with skill) and compare")
    parser.add_argument("--dev", default=None, metavar="SKILL_NAME",
                        help="Run using skill from developing/, save to _benchmarks/")
    parser.add_argument("--history", type=Path, default=None, metavar="SKILL_PATH",
                        help="Show benchmark history for a skill")
    args = parser.parse_args()

    if args.history:
        show_benchmark_history(args.history)
        return

    if args.dev:
        result = dev_benchmark(args.task_id, args.dev, model=args.model)
        print(f"\n  Score: {result.get('score', 'N/A')}")
        show_benchmark_history(DEVELOPING_DIR / args.dev)
        return

    if args.compare:
        print(f"  Running before (no skill)...")
        before = benchmark_task(args.task_id, skill_path=None, model=args.model)
        print(f"  Before score: {before.get('score', 'N/A')}\n")

        print(f"  Running after (with skill: {args.compare.name})...")
        after = benchmark_task(args.task_id, skill_path=args.compare, model=args.model)
        print(f"  After score: {after.get('score', 'N/A')}\n")

        # Save both results if skill is in developing/
        if args.compare.parent.name == "developing":
            save_benchmark_result(args.compare, args.task_id, before, label="before")
            save_benchmark_result(args.compare, args.task_id, after, label="after")

        print(f"  {'─' * 40}")
        print(f"  Task:   {args.task_id}")
        print(f"  Before: {before.get('score', 'N/A')}")
        print(f"  After:  {after.get('score', 'N/A')}")
        b = before.get("score") or 0
        a = after.get("score") or 0
        print(f"  Delta:  {a - b:+d}")
        print(f"  {'─' * 40}")
    else:
        result = benchmark_task(args.task_id, skill_path=args.skill_path, model=args.model)
        print(f"\n  Score: {result.get('score', 'N/A')}")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
