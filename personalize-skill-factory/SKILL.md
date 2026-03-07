---
name: personalize-skill-factory
description: >
  Fetch agent skills from Sundial, verify safety in Daytona sandbox, customize
  with Claude API, benchmark on SkillsBench, and publish improvements. Use when:
  (1) User wants to find and improve an agent skill, (2) User says "personalize
  this skill", "benchmark a skill", or "improve skill for <task>", (3) User wants
  a before/after comparison of skill effectiveness.
---

# Personalize Skill Factory

End-to-end pipeline: fetch → quarantine → safety check → customize → benchmark → publish.

## Quick Start

```bash
# Full pipeline
uv run personalize-skill-factory/scripts/factory.py <skill-query> <task-id>

# Individual steps
uv run personalize-skill-factory/scripts/quarantine.py <skill-query>
uv run personalize-skill-factory/scripts/safety_check.py skills/staging/<name>
uv run personalize-skill-factory/scripts/benchmark.py <task-id> --compare skills/generated/<name>
uv run personalize-skill-factory/scripts/publish.py skills/generated/<name>
```

## Pipeline Steps

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

If the user chooses to customize, send the current SKILL.md + failure context to Claude API for improvement. The improved version replaces the original.

### 4. Benchmark (`benchmark.py`)

Run SkillsBench tasks via Harbor:

- **Before**: run task without any skill (baseline)
- **After**: inject skill into `tasks-no-skills/<task>/environment/skills/`, run again
- Parse `reward.txt` (0/1) and `ctrf.json` for test details
- Clean up injected skill after each run

### 5. Publish (`publish.py`)

Push approved skill to Sundial Hub via `npx sundial-hub push`.

## Directory Structure

```
personalize-skill-factory/
├── SKILL.md              # This file
├── scripts/
│   ├── factory.py        # Main pipeline orchestrator
│   ├── quarantine.py     # Sundial fetch + isolate
│   ├── safety_check.py   # Claude static + Daytona dynamic analysis
│   ├── benchmark.py      # Harbor run wrapper + score comparison
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
| `ANTHROPIC_API_KEY` | Yes | Claude API for analysis + customization |
| `DAYTONA_API_KEY` | No | Daytona sandbox (skipped if missing) |
| `DAYTONA_BASE_URL` | No | Daytona endpoint (default: https://app.daytona.io/api) |

## Available SkillsBench Tasks

Run `ls personalize-skill-factory/skillsbench/tasks-no-skills/` to see all 86 tasks.
