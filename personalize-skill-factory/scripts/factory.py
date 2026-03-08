# /// script
# dependencies = ["anthropic", "daytona-sdk"]
# ///
"""
Personalize Skill Factory — Main Pipeline

Usage:
    uv run personalize-skill-factory/scripts/factory.py <skill-query> <task-id>
    uv run personalize-skill-factory/scripts/factory.py <skill-query> <task-id> --auto
    uv run personalize-skill-factory/scripts/factory.py --generate <task-id>
    uv run personalize-skill-factory/scripts/factory.py --generate <task-id> --auto

Flow:
    staging → developing → generated

    1. Fetch from Sundial → quarantine to staging/  (or --generate to create from scratch)
    2. Safety check (Claude static + Daytona dynamic)  (skipped for --generate)
    3. Approve → move to developing/                   (skipped for --generate)
    4. Customize + benchmark loop in developing/
    5. Finalize → move to generated/, link to .claude/skills/
    6. Optionally publish to Sundial

Generate mode (--generate):
    AI analyzes the SkillsBench task (instruction.md, tests, environment) and
    generates a SKILL.md from scratch. No Sundial needed.

Auto mode (--auto):
    Runs the full pipeline without user interaction.
    Rejects if safety check returns "dangerous".
    Runs benchmark once, customize once, benchmark again, then finalize.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure sibling scripts are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from event_log import emit as log_event

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


# ── Step 0: Generate Skill from Scratch ─────────────────────────────────

GENERATE_PROMPT = """You are an expert at creating agent skills (agentskills.io spec).

Given the following SkillsBench task, generate a SKILL.md that helps an AI agent solve it.

## Task: {task_id}

### Instruction
{instruction}

### Test file (what the agent's output is validated against)
{test_content}

### Environment
- Docker image: {docker_image}
- Difficulty: {difficulty}
- Category: {category}
- Tags: {tags}

### Existing skill scripts available
{existing_scripts}

## Rules for generating SKILL.md

1. Start with YAML frontmatter: `---\\nname: <skill-name>\\ndescription: <one-line>\\n---`
2. The skill name should be a short kebab-case identifier derived from the task
3. Focus on GUIDING the agent, not implementing the solution
4. Include: when to use, API reference for any bundled scripts, output format requirements
5. Highlight specific requirements from tests (exact field names, shapes, formats)
6. Do NOT include full solution code — the agent should write its own
7. DO include concrete examples of expected output formats
8. Keep it under 200 lines
9. If scripts/ exist, document their API (classes, methods, parameters)

Return ONLY the SKILL.md content, nothing else."""


def generate_skill(task_id: str, optimizer: str = "claude") -> Path:
    """AI generates a skill from scratch by analyzing the SkillsBench task."""

    task_dir = SKILLSBENCH_DIR / "tasks-no-skills" / task_id
    if not task_dir.exists():
        # Try tasks/ as fallback
        task_dir = SKILLSBENCH_DIR / "tasks" / task_id
    if not task_dir.exists():
        print(f"  Error: task '{task_id}' not found in tasks-no-skills/ or tasks/")
        sys.exit(1)

    # Read task context
    instruction = ""
    instr_path = task_dir / "instruction.md"
    if instr_path.exists():
        instruction = instr_path.read_text()

    test_content = ""
    test_path = task_dir / "tests" / "test_outputs.py"
    if test_path.exists():
        test_content = test_path.read_text()[:4000]

    # Parse task.toml
    docker_image = "unknown"
    difficulty = "unknown"
    category = "unknown"
    tags = ""
    toml_path = task_dir / "task.toml"
    if toml_path.exists():
        toml_text = toml_path.read_text()
        import re
        m = re.search(r'image\s*=\s*"([^"]+)"', toml_text)
        if m:
            docker_image = m.group(1)
        m = re.search(r'difficulty\s*=\s*"([^"]+)"', toml_text)
        if m:
            difficulty = m.group(1)
        m = re.search(r'category\s*=\s*"([^"]+)"', toml_text)
        if m:
            category = m.group(1)
        m = re.search(r'tags\s*=\s*\[([^\]]+)\]', toml_text)
        if m:
            tags = m.group(1)

    # Check for existing scripts in the task's skill directory
    existing_scripts = ""
    skills_dir = task_dir / "environment" / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            scripts_path = skill_dir / "scripts"
            if scripts_path.exists():
                for f in scripts_path.iterdir():
                    if f.is_file() and f.suffix in (".py", ".js", ".sh"):
                        content = f.read_text()[:3000]
                        existing_scripts += f"\n--- {skill_dir.name}/scripts/{f.name} ---\n{content}\n"

    prompt = GENERATE_PROMPT.format(
        task_id=task_id,
        instruction=instruction,
        test_content=test_content,
        docker_image=docker_image,
        difficulty=difficulty,
        category=category,
        tags=tags,
        existing_scripts=existing_scripts or "(none)",
    )

    # Generate via optimizer
    print(f"  Generating skill for task '{task_id}' with {optimizer}...")
    if optimizer == "claude":
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        skill_md = message.content[0].text
    elif optimizer.startswith("openrouter:"):
        import urllib.request
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        model = optimizer.split(":", 1)[1]
        body = json.dumps({
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        skill_md = data["choices"][0]["message"]["content"]
    else:
        # Default to claude for generation
        import anthropic
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        skill_md = message.content[0].text

    # Clean up: extract SKILL.md content if wrapped in markdown fences
    if "```" in skill_md:
        import re
        match = re.search(r'```(?:markdown|yaml|md)?\n(---\n.*?)```', skill_md, re.DOTALL)
        if match:
            skill_md = match.group(1).rstrip()

    # Derive skill name from task_id
    skill_name = task_id.replace("-", "_")

    # Place in developing/
    DEVELOPING_DIR.mkdir(parents=True, exist_ok=True)
    dest = DEVELOPING_DIR / skill_name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    # Write generated SKILL.md
    (dest / "SKILL.md").write_text(skill_md)

    # Copy scripts from task environment if they exist
    if skills_dir.exists():
        for existing_skill_dir in skills_dir.iterdir():
            scripts_src = existing_skill_dir / "scripts"
            if scripts_src.exists() and scripts_src.is_dir():
                shutil.copytree(scripts_src, dest / "scripts")
                break

    # Save as baseline (AI-generated v0)
    baseline_dir = dest / "_baseline"
    baseline_dir.mkdir(exist_ok=True)
    shutil.copy2(dest / "SKILL.md", baseline_dir / "SKILL.md")
    if (dest / "scripts").exists():
        shutil.copytree(dest / "scripts", baseline_dir / "scripts")

    # Also install into the task for benchmarking
    task_skill_dir = task_dir / "environment" / "skills" / skill_name
    task_skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dest / "SKILL.md", task_skill_dir / "SKILL.md")
    if (dest / "scripts").exists():
        scripts_dest = task_skill_dir / "scripts"
        if scripts_dest.exists():
            shutil.rmtree(scripts_dest)
        shutil.copytree(dest / "scripts", scripts_dest)

    print(f"  Generated skill: {dest}")
    print(f"  SKILL.md: {len(skill_md)} chars")
    log_event("generate", skill_name, "developing",
              task_id=task_id, optimizer=optimizer, skill_md_chars=len(skill_md))

    return dest


# ── Step 1: Fetch from Sundial ──────────────────────────────────────────

def fetch_skill(skill_query: str) -> Path:
    """Search Sundial, add skill, quarantine to staging/."""
    from quarantine import quarantine_skill, sundial_add

    skill_name = sundial_add(skill_query)
    staging_path = quarantine_skill(skill_name)
    print(f"  Quarantined to: {staging_path}")
    log_event("fetch", skill_name, "staging", query=skill_query, path=str(staging_path))
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
    log_event("safety_check", staging_path.name, "staging",
              recommendation=report.get("recommendation", "?"),
              dangerous_patterns=len(report.get("dangerous_patterns", [])),
              network_urls=len(report.get("network_urls", [])),
              dynamic_skipped=report.get("dynamic_skipped", False))
    return report


# ── Step 3: Approve → Move to developing/ ──────────────────────────────

def approve_to_developing(staging_path: Path, safety_report: dict, auto: bool = False) -> Path:
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

    if auto:
        recommendation = safety_report.get("recommendation", "review")
        if recommendation == "dangerous":
            print("  Auto-rejected: safety check returned 'dangerous'.")
            shutil.rmtree(staging_path)
            sys.exit(1)
        print(f"  Auto-approved (recommendation: {recommendation})")
    else:
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

    # Save Sundial original as baseline for comparison
    baseline_dir = dest / "_baseline"
    baseline_dir.mkdir(exist_ok=True)
    skill_md_path = dest / "SKILL.md"
    if skill_md_path.exists():
        shutil.copy2(skill_md_path, baseline_dir / "SKILL.md")
    scripts_src = dest / "scripts"
    if scripts_src.exists():
        baseline_scripts = baseline_dir / "scripts"
        if baseline_scripts.exists():
            shutil.rmtree(baseline_scripts)
        shutil.copytree(scripts_src, baseline_scripts)
    print(f"  Baseline saved: {baseline_dir}")
    log_event("approve", dest.name, "developing",
              recommendation=safety_report.get("recommendation", "?"),
              auto=auto)

    return dest


# ── Step 4: Customize + Benchmark Loop ──────────────────────────────────

def develop_loop(dev_path: Path, task_id: str, optimizer: str = "claude"):
    """Iterate: customize → benchmark → repeat."""
    from benchmark import benchmark_task, save_benchmark_result, show_benchmark_history, compare_baseline

    print(f"  Optimizer: {optimizer}")
    iteration = 0
    while True:
        iteration += 1
        print(f"\n  ── Iteration {iteration} ──")
        print(f"  [b]enchmark / [c]ustomize ({optimizer}) / [e]dit manually / [v] compare vs baseline / [d]one")
        choice = input("  > ").strip().lower()

        if choice == "d":
            break

        if choice == "b":
            print(f"  Running benchmark: {task_id}...")
            result = benchmark_task(task_id, skill_path=dev_path)
            save_benchmark_result(dev_path, task_id, result, label=f"iter-{iteration}")
            print(f"  Score: {result.get('score', 'N/A')}")
            log_event("benchmark", dev_path.name, "developing",
                      label=f"iter-{iteration}", score=result.get("score"), task_id=task_id)
            show_benchmark_history(dev_path)

        elif choice == "v":
            compare_baseline(dev_path, task_id)

        elif choice == "c":
            print(f"  Customizing with {optimizer}...")
            new_md = customize_skill(dev_path, task_id, optimizer=optimizer)
            (dev_path / "SKILL.md").write_text(new_md)
            print("  SKILL.md updated.")
            print(f"  New SKILL.md: {len(new_md)} chars")
            log_event("customize", dev_path.name, "developing",
                      optimizer=optimizer, iteration=iteration, skill_md_chars=len(new_md))

        elif choice == "e":
            print(f"  Edit the file directly:")
            print(f"    {dev_path / 'SKILL.md'}")
            input("  Press Enter when done editing...")

        else:
            print("  Invalid choice.")


def auto_develop_loop(dev_path: Path, task_id: str, iterations: int = 1, optimizer: str = "claude"):
    """Auto mode: baseline benchmark → (customize → benchmark) × N."""
    from benchmark import benchmark_task, save_benchmark_result, show_benchmark_history

    print(f"  Optimizer: {optimizer}")

    # Step 0: Benchmark with Sundial original (baseline)
    baseline_dir = dev_path / "_baseline"
    baseline_score = None
    if baseline_dir.exists() and (baseline_dir / "SKILL.md").exists():
        print(f"\n  ── Baseline: Sundial Original ──")
        print(f"  Benchmarking original skill...")
        baseline_result = benchmark_task(task_id, skill_path=baseline_dir)
        save_benchmark_result(dev_path, task_id, baseline_result, label="baseline-sundial")
        baseline_score = baseline_result.get("score")
        print(f"  Baseline score: {baseline_score}")
        log_event("benchmark", dev_path.name, "developing",
                  label="baseline-sundial", score=baseline_score, task_id=task_id)

    for i in range(iterations):
        print(f"\n  ── Auto Iteration {i + 1}/{iterations} ──")

        # Customize
        print(f"  Customizing with {optimizer}...")
        new_md = customize_skill(dev_path, task_id, optimizer=optimizer)
        (dev_path / "SKILL.md").write_text(new_md)
        print(f"  SKILL.md updated ({len(new_md)} chars)")
        log_event("customize", dev_path.name, "developing",
                  optimizer=optimizer, iteration=i + 1, skill_md_chars=len(new_md))

        # Benchmark after customize
        print(f"  Benchmarking (personalized)...")
        after = benchmark_task(task_id, skill_path=dev_path)
        save_benchmark_result(dev_path, task_id, after, label=f"auto-{i+1}-{optimizer}")
        after_score = after.get("score") or 0
        print(f"  Score: {after_score}")
        log_event("benchmark", dev_path.name, "developing",
                  label=f"auto-{i+1}-{optimizer}", score=after_score,
                  task_id=task_id, iteration=i + 1)

        # Report vs baseline
        print(f"\n  {'─' * 50}")
        if baseline_score is not None:
            delta = after_score - (baseline_score or 0)
            print(f"  Sundial original:  {baseline_score}")
            print(f"  {optimizer} (i{i+1}): {after_score}  (delta: {delta:+.1f})")
        else:
            print(f"  {optimizer} (i{i+1}): {after_score}")
        print(f"  {'─' * 50}")

    show_benchmark_history(dev_path)


CUSTOMIZE_PROMPT = """Analyze this agent skill and improve it for better benchmark performance.

Current SKILL.md:
{skill_md}

Scripts bundled with the skill:
{scripts_content}
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


def _build_customize_prompt(dev_path: Path, task_id: str = "") -> str:
    """Build the prompt for skill customization (shared across all optimizers)."""
    skill_md = (dev_path / "SKILL.md").read_text()

    scripts_content = ""
    scripts_dir = dev_path / "scripts"
    if scripts_dir.exists():
        for f in scripts_dir.iterdir():
            if f.is_file():
                scripts_content += f"\n--- {f.name} ---\n{f.read_text()}\n"

    benchmark_context = ""
    benchmarks_dir = dev_path / "_benchmarks"
    if benchmarks_dir.exists():
        runs = sorted(benchmarks_dir.glob("run-*.json"))
        if runs:
            latest = json.loads(runs[-1].read_text())
            benchmark_context = f"\nLatest benchmark result:\n{json.dumps(latest, indent=2)}\n"

    task_context = ""
    if task_id:
        task_instruction = SKILLSBENCH_DIR / "tasks-no-skills" / task_id / "instruction.md"
        if task_instruction.exists():
            task_context = f"\nTask instruction ({task_id}):\n{task_instruction.read_text()[:2000]}\n"

    return CUSTOMIZE_PROMPT.format(
        skill_md=skill_md,
        scripts_content=scripts_content or "(none)",
        benchmark_context=benchmark_context,
        task_context=task_context,
    )


def customize_with_claude(dev_path: Path, task_id: str = "") -> str:
    """Use Claude API to improve the skill."""
    import anthropic

    prompt = _build_customize_prompt(dev_path, task_id)
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def customize_with_openrouter(dev_path: Path, task_id: str = "", model: str = "deepseek/deepseek-r1") -> str:
    """Use OpenRouter API (OpenAI-compatible) to improve the skill with any model."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set. Get one at https://openrouter.ai/keys")

    # OpenRouter is OpenAI-compatible — use httpx directly to avoid extra deps
    import urllib.request

    prompt = _build_customize_prompt(dev_path, task_id)
    body = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/personalize-skill-factory",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())

    return data["choices"][0]["message"]["content"]


def customize_with_hermes(dev_path: Path, task_id: str = "", model: str = "") -> str:
    """Use Hermes Agent CLI to improve the skill.

    Hermes supports: Nous Portal, OpenRouter, DeepSeek, Groq, self-hosted, etc.
    It also has built-in skill_manage, memory, and multi-tool capabilities.
    """
    prompt = _build_customize_prompt(dev_path, task_id)

    cmd = ["hermes", "chat", "--toolsets", "file,skills", "-q", prompt]
    if model:
        cmd.extend(["--model", model])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    if result.returncode != 0:
        raise RuntimeError(f"Hermes failed: {result.stderr[:500]}")

    # Hermes outputs conversational text — extract the SKILL.md content
    output = result.stdout
    # Try to extract markdown content between --- delimiters (YAML frontmatter)
    if "---" in output:
        parts = output.split("---")
        if len(parts) >= 3:
            # Reconstruct: frontmatter + body
            return "---" + "---".join(parts[1:]).rstrip()

    # Fallback: return full output (user may need to clean up)
    return output.strip()


# ── Model Profiles (from artificialanalysis.ai leaderboard) ───────────
# Balance intelligence, speed, and cost for skill optimization.

MODEL_PROFILES = {
    "smart": {
        "desc": "Highest intelligence — best for complex skill rewrites",
        "models": [
            "google/gemini-2.5-pro",          # Intelligence #1
            "openai/gpt-4.1",                 # Intelligence top-tier
            "anthropic/claude-sonnet-4-20250514",  # Intelligence #5
        ],
    },
    "balanced": {
        "desc": "Good quality at reasonable cost",
        "models": [
            "deepseek/deepseek-r1",           # Open-weight reasoning, cheap
            "google/gemini-2.5-flash",        # Fast + smart
            "qwen/qwen3-235b-a22b",           # Open-weight, strong
        ],
    },
    "cheap": {
        "desc": "Lowest cost per token — for bulk iterations",
        "models": [
            "deepseek/deepseek-r1",           # Very cheap reasoning
            "deepseek/deepseek-chat-v3-0324",  # Non-reasoning, cheapest
            "qwen/qwen3-30b-a3b",             # Small but capable
        ],
    },
    "fast": {
        "desc": "Lowest latency — for rapid iteration demos",
        "models": [
            "google/gemini-2.5-flash",        # 362 t/s
            "meta-llama/llama-4-scout",       # Fast open-weight
            "deepseek/deepseek-chat-v3-0324",
        ],
    },
}


def resolve_optimizer(optimizer: str) -> str:
    """Resolve optimizer shorthand to full spec.

    Supports:
      claude, hermes, hermes:<model>,
      openrouter:<model>,
      smart, balanced, cheap, fast  (profile → openrouter:<first-model>)
    """
    if optimizer in MODEL_PROFILES:
        model = MODEL_PROFILES[optimizer]["models"][0]
        print(f"  Profile '{optimizer}': {MODEL_PROFILES[optimizer]['desc']}")
        print(f"  Selected model: {model}")
        return f"openrouter:{model}"
    return optimizer


def list_profiles():
    """Print available model profiles."""
    print(f"\n  {'═' * 55}")
    print(f"  Model Profiles (from AI Model Leaderboard)")
    print(f"  {'─' * 55}")
    for name, info in MODEL_PROFILES.items():
        print(f"  --optimizer {name:<10}  {info['desc']}")
        for m in info["models"]:
            print(f"    → {m}")
    print(f"  {'─' * 55}")
    print(f"  Direct: --optimizer openrouter:<any-openrouter-model>")
    print(f"  {'═' * 55}")

def customize_skill(dev_path: Path, task_id: str = "", optimizer: str = "claude") -> str:
    """Dispatch to the appropriate optimizer."""
    if optimizer == "claude":
        return customize_with_claude(dev_path, task_id)
    elif optimizer == "hermes":
        return customize_with_hermes(dev_path, task_id)
    elif optimizer.startswith("hermes:"):
        # hermes:<model> — use specific model via Hermes
        model = optimizer.split(":", 1)[1]
        return customize_with_hermes(dev_path, task_id, model=model)
    elif optimizer.startswith("openrouter:"):
        # openrouter:<model> — use OpenRouter API directly
        model = optimizer.split(":", 1)[1]
        return customize_with_openrouter(dev_path, task_id, model=model)
    elif optimizer == "openrouter":
        return customize_with_openrouter(dev_path, task_id)
    else:
        raise ValueError(f"Unknown optimizer: {optimizer}. Use: claude, hermes, hermes:<model>, openrouter:<model>")


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
    log_event("finalize", dev_path.name, "generated", path=str(dest))
    return dest


def link_skills():
    """Run link_skills.sh to update .claude/skills/ symlinks."""
    result = run(["bash", str(SCRIPTS_DIR / "link_skills.sh")])
    if result.returncode != 0:
        print(f"  Warning: link failed: {result.stderr}")


# ── Step 6: Publish ────────────────────────────────────────────────────

def publish_skill(skill_path: Path, auto: bool = False):
    """Optionally publish to Sundial."""
    from publish import publish_to_sundial

    if auto:
        print("  Auto mode: skipping publish.")
        return

    choice = input("\n  Publish to Sundial? [y/N] ").strip().lower()
    if choice == "y":
        publish_to_sundial(skill_path)


# ── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Personalize Skill Factory")
    parser.add_argument("skill_query", nargs="?", default=None,
                        help="Skill name or search query for Sundial (not needed with --generate)")
    parser.add_argument("task_id", help="SkillsBench task ID to benchmark against")
    parser.add_argument("--generate", action="store_true",
                        help="AI generates a skill from scratch by analyzing the task (no Sundial needed)")
    parser.add_argument("--skip-sundial", action="store_true",
                        help="Use existing skill in staging/ instead of fetching")
    parser.add_argument("--resume", action="store_true",
                        help="Resume developing an existing skill in developing/")
    parser.add_argument("--auto", action="store_true",
                        help="Run full pipeline without user interaction")
    parser.add_argument("--auto-iterations", type=int, default=1,
                        help="Number of benchmark→customize→benchmark cycles in auto mode (default: 1)")
    parser.add_argument("--optimizer", default="claude",
                        help="Skill optimizer: claude, hermes, hermes:<model>, openrouter:<model>, "
                             "or profile: smart, balanced, cheap, fast (default: claude)")
    parser.add_argument("--list-models", action="store_true",
                        help="List available model profiles and exit")
    args = parser.parse_args()

    if args.list_models:
        list_profiles()
        sys.exit(0)

    # Resolve profile names (smart/balanced/cheap/fast) to openrouter:<model>
    optimizer = resolve_optimizer(args.optimizer)

    print("=" * 60)
    print("  Personalize Skill Factory")
    if args.auto:
        print(f"  Mode: AUTO ({args.auto_iterations} iteration(s))")
    print(f"  Optimizer: {optimizer}")
    print("=" * 60)

    if args.generate:
        # AI generates skill from scratch — skip Sundial, safety, approve
        print(f"\n[1/6] Generating skill from task: {args.task_id}")
        dev_path = generate_skill(args.task_id, optimizer=optimizer)
        print(f"\n[2/6] Safety check... SKIPPED (AI-generated)")
        print(f"\n[3/6] Review & approve... SKIPPED (AI-generated)")
    elif args.resume:
        # Resume from developing/
        dev_path = DEVELOPING_DIR / args.skill_query
        if not dev_path.exists():
            print(f"  Error: {dev_path} not found in developing/")
            sys.exit(1)
        print(f"\n  Resuming: {dev_path}")
    else:
        if not args.skill_query:
            print("  Error: skill_query required (or use --generate)")
            sys.exit(1)
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
        dev_path = approve_to_developing(staging_path, safety_report, auto=args.auto)

    # Step 4: Develop loop
    print(f"\n[4/6] Develop: customize + benchmark")
    if args.auto:
        auto_develop_loop(dev_path, args.task_id, iterations=args.auto_iterations, optimizer=optimizer)
    else:
        develop_loop(dev_path, args.task_id, optimizer=optimizer)

    # Step 5: Finalize
    print(f"\n[5/6] Finalizing...")
    generated_path = finalize(dev_path)
    link_skills()

    # Step 6: Publish
    print(f"\n[6/6] Publish")
    publish_skill(generated_path, auto=args.auto)

    print(f"\nDone. Skill saved at: {generated_path}")


if __name__ == "__main__":
    main()
