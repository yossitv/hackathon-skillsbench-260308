---
name: personalize-skill-factory
description: "Personalize agent skills pipeline: fetch from Sundial, verify safety in Daytona sandbox, customize with Claude API, benchmark on SkillsBench (before/after comparison), visualize with dashboard, and publish. Use when user wants to find, improve, benchmark, visualize, or personalize an agent skill."
---

# Personalize Skill Factory

End-to-end pipeline: fetch → quarantine → safety check → customize → benchmark → publish.

## Quick Start

```bash
# Full pipeline (from Sundial)
uv run personalize-skill-factory/scripts/factory.py <skill-query> <task-id>

# AI generates skill from scratch (no Sundial needed)
uv run personalize-skill-factory/scripts/factory.py --generate <task-id>
uv run personalize-skill-factory/scripts/factory.py --generate <task-id> --auto

# With multi-model optimization
uv run personalize-skill-factory/scripts/factory.py --generate <task-id> --optimizer smart
uv run personalize-skill-factory/scripts/factory.py <skill-query> <task-id> --optimizer openrouter:google/gemini-2.5-pro

# Auto mode with comparison
uv run personalize-skill-factory/scripts/factory.py <skill-query> <task-id> --auto --optimizer hermes

# Individual steps
uv run personalize-skill-factory/scripts/quarantine.py <skill-query>
uv run personalize-skill-factory/scripts/safety_check.py skills/staging/<name>
uv run personalize-skill-factory/scripts/benchmark.py <task-id> --compare-baseline <skill-name>
uv run personalize-skill-factory/scripts/publish.py skills/generated/<name>
```

## Pipeline Steps

### 0. Generate from Scratch (`--generate` in `factory.py`)

AI analyzes the SkillsBench task (instruction.md, tests, Dockerfile, existing scripts) and generates a SKILL.md from scratch. Skips fetch/safety/approve — goes straight to developing/ for customize + benchmark.

### 1. Fetch & Quarantine (`quarantine.py`)

Search Sundial for a skill, install it, and immediately move from `.agents/skills/` to `skills/staging/` so Claude Code cannot auto-load unverified code.

- `sundial_find(query)` — search registry, return metadata
- `sundial_add(name)` — install via `npx sundial-hub add`
- `quarantine_skill(name)` — move to staging, remove symlinks

### 2. Safety Check (`safety_check.py`)

Two-phase verification:

- **Static analysis**: Claude API scans SKILL.md + scripts/ for dangerous patterns (shell injection, credential theft, network exfiltration, obfuscated code)
- **Dynamic analysis**: Upload to Daytona sandbox, block network with iptables, execute scripts, detect blocked connection attempts and file changes

Returns a report with `recommendation: "safe" | "review" | "dangerous"`.

### 3. Customize (in `factory.py`)

Multi-model skill optimization via `--optimizer`:

| Optimizer | Command | Description |
|-----------|---------|-------------|
| `claude` (default) | `--optimizer claude` | Claude API (Sonnet) |
| `hermes` | `--optimizer hermes` | Hermes Agent CLI (uses configured model) |
| `hermes:<model>` | `--optimizer hermes:deepseek/deepseek-r1` | Hermes with specific model |
| `openrouter:<model>` | `--optimizer openrouter:google/gemini-2.5-pro` | OpenRouter API (any model) |

Sends current SKILL.md + benchmark failures + task instruction to the chosen model for improvement.

### 4. Benchmark (`benchmark.py`)

Run SkillsBench tasks via Harbor:

- **Before**: run task without any skill (baseline)
- **After**: inject skill into `tasks-no-skills/<task>/environment/skills/`, run again
- Parse `reward.txt` (0/1) and `ctrf.json` for test details
- Clean up injected skill after each run

### 5. Publish (`publish.py`)

Push approved skill to Sundial Hub via `npx sundial-hub push`.

### 6. Dashboard (`dashboard.py`)

View pipeline status, benchmark trends, and SKILL.md diffs in the browser.

```bash
uv run --with streamlit --with pandas --with altair \
  streamlit run personalize-skill-factory/scripts/dashboard.py
```

When the user asks to "show the dashboard", "view pipeline status", or "open the dashboard", run the command above.

## Directory Structure

```
personalize-skill-factory/
├── SKILL.md              # This file
├── scripts/
│   ├── factory.py        # Main pipeline orchestrator
│   ├── quarantine.py     # Sundial fetch + isolate
│   ├── safety_check.py   # Claude static + Daytona dynamic analysis
│   ├── benchmark.py      # Harbor run wrapper + score comparison
│   ├── dashboard.py      # Streamlit dashboard (pipeline, benchmarks, diffs)
│   ├── event_log.py      # Structured JSONL event logger
│   ├── publish.py        # Sundial push
│   └── link_skills.sh    # Symlink generated/ → .claude/skills/
├── skills/
│   ├── staging/          # Unverified (straight from Sundial, not visible to Claude)
│   ├── developing/       # Safety-approved, customizing + benchmarking in progress
│   │   └── <skill>/
│   │       ├── SKILL.md
│   │       └── _benchmarks/   # Auto-saved benchmark results
│   │           ├── run-001.json
│   │           └── run-002.json
│   └── generated/        # Finalized, linked to .claude/skills/, publish-ready
├── skillsbench/          # SkillsBench submodule (86 tasks, Harbor CLI)
└── references/
```

## Skill Lifecycle

```
   --generate ──┐
                ▼
staging → developing → generated
  │          │             │
  │          ├── customize │
  │          ├── benchmark │
  │          └── repeat    │
  │                        │
  quarantine    dev loop     finalize + publish
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API for safety analysis + customization |
| `DAYTONA_API_KEY` | No | Daytona sandbox (skipped if missing) |
| `DAYTONA_BASE_URL` | No | Daytona endpoint (default: https://app.daytona.io/api) |
| `OPENROUTER_API_KEY` | No | OpenRouter API for multi-model optimization |

## Available SkillsBench Tasks

Run `ls personalize-skill-factory/skillsbench/tasks-no-skills/` to see all 86 tasks.
