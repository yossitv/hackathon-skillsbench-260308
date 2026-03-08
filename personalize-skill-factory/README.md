# Personalize Skill Factory

An end-to-end pipeline that fetches, generates, verifies, customizes, benchmarks, and publishes agent skills. Built for **Track 05: Continual Learning** at the Skillathon hackathon.

## How It Works

The factory only needs a **SkillsBench task ID** to run. It automatically decides the best path to create a skill:

```
                         ┌──────────────────┐
                         │   task ID given   │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │ Search Sundial    │
                         │ for existing skill│
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              Found on Sundial           Not found
                    │                           │
                    ▼                           ▼
           Fetch & Quarantine         AI Generates Skill
           Safety Check (Claude       from task context:
           static + Daytona dynamic)  • instruction.md
           Approve to developing/     • test_outputs.py
                    │                 • task.toml
                    │                 • existing scripts
                    │                           │
                    └─────────┬─────────────────┘
                              │
                              ▼
                    Customize + Benchmark Loop
                    (Claude / OpenRouter / Hermes)
                              │
                              ▼
                    Finalize → .claude/skills/
                              │
                              ▼
                    Publish to Sundial (optional)
```

### Skill Resolution: Sundial vs AI Generation

When you provide a task ID, the pipeline resolves the skill source automatically:

1. **Sundial search** — The task ID (or an optional `skill_query`) is used to search the Sundial Hub registry. If a matching skill exists, it is fetched, quarantined, and safety-checked before use.

2. **Auto-fallback to AI generation** — If Sundial returns no results, the factory automatically generates a skill from scratch. The AI reads the SkillsBench task's `instruction.md`, `test_outputs.py`, `task.toml`, and any bundled scripts to produce a SKILL.md tailored to the task.

3. **Explicit generation** — You can skip the Sundial search entirely with `--generate` to force AI generation.

In all cases, the generated or fetched skill enters the same **customize + benchmark loop** for iterative improvement.

```bash
# Let the pipeline decide (Sundial → auto-fallback to AI)
factory.py dialogue-parser

# Explicit Sundial search with custom query
factory.py "dialogue graph" dialogue-parser

# Force AI generation (skip Sundial)
factory.py --generate dialogue-parser

# Full auto pipeline
factory.py --generate dialogue-parser --auto --optimizer smart
```

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  1. FETCH & QUARANTINE  (or AI GENERATE if not on Sundial)          │
│  ┌──────────────┐      ┌───────────────────┐                       │
│  │ Sundial Hub  │─────▶│ skills/staging/    │                       │
│  │ (npm CLI)    │      │ (isolated, not     │                       │
│  │              │      │  auto-loaded)      │                       │
│  └──────────────┘      └────────┬──────────┘                       │
│         │ not found              │                                   │
│         ▼                        │                                   │
│  ┌──────────────┐                │                                   │
│  │ AI Generate  │───────────┐    │                                   │
│  │ (Claude /    │           │    │                                   │
│  │  OpenRouter) │           │    │                                   │
│  └──────────────┘           │    │                                   │
│                             │    │                                   │
│  2. SAFETY CHECK            │    ▼                                   │
│  ┌──────────────────────────│───────────────┐                       │
│  │  Static: Claude API      │ (skipped for  │                       │
│  │  Dynamic: Daytona sandbox│  AI-generated)│                       │
│  └──────────────────────────┤───────────────┘                       │
│                             │                                        │
│  3. APPROVE ────────────────┴──▶ skills/developing/                 │
│                    (+ _baseline/ snapshot saved)                     │
│                         │                                           │
│  4. DEVELOPMENT LOOP    ▼                                           │
│  ┌──────────────────────────────────────────┐                       │
│  │                                          │                       │
│  │  ┌─────────────────┐   ┌──────────────┐ │                       │
│  │  │   Customize     │   │  Benchmark   │ │                       │
│  │  │                 │   │              │ │                       │
│  │  │  Claude API     │   │  Harbor CLI  │ │                       │
│  │  │  Hermes Agent   │──▶│ (SkillsBench)│ │                       │
│  │  │  OpenRouter     │   │              │ │                       │
│  │  │                 │   │  Score +     │ │                       │
│  │  │  Improve        │◀──│  Test results│ │                       │
│  │  │  SKILL.md       │   │              │ │                       │
│  │  └─────────────────┘   └──────────────┘ │                       │
│  │         ▲                     │          │                       │
│  │         └─────────────────────┘          │                       │
│  │          Repeat N iterations             │                       │
│  └──────────────────────┬───────────────────┘                       │
│                         │                                           │
│  5. FINALIZE            ▼                                           │
│  ┌──────────────────────────────────────────┐                       │
│  │  skills/developing/ ──▶ skills/generated/│                       │
│  │  link_skills.sh ──▶ .claude/skills/      │                       │
│  │  (symlink, Claude Code can now use it)   │                       │
│  └──────────────────────┬───────────────────┘                       │
│                         │                                           │
│  6. PUBLISH (optional)  ▼                                           │
│  ┌──────────────┐                                                   │
│  │ Sundial Hub  │ Push improved skill back                          │
│  │ (npm CLI)    │ to registry                                       │
│  └──────────────┘                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Services Used

| Step | Service | Purpose |
|------|---------|---------|
| Fetch | **Sundial Hub** | Search & download skills from registry |
| Generate | **Claude API / OpenRouter** | AI creates skill from task analysis |
| Safety (Static) | **Claude API** | Scan for dangerous code patterns |
| Safety (Dynamic) | **Daytona Sandbox** | Execute in isolated environment with network blocked |
| Customize | **Claude API / Hermes / OpenRouter** | LLM-driven skill improvement |
| Benchmark | **Harbor CLI (SkillsBench)** | Run tasks with/without skill, measure score |
| Publish | **Sundial Hub** | Push improved skill back to registry |

## Benchmark Results

### dialogue-graph (k=3 trials)

| Version | Scores | Mean |
|---------|--------|------|
| **Before** (original from SkillsBench) | 0.167, 0.667, 0.833 | **0.556** |
| **After** (personalized) | 0.0*, 0.833, 1.000 | **0.611** |

\* Agent failure (no output), not skill quality.

Key finding: the personalized skill achieved a **perfect 1.0 score** that the original never reached. The change was minimal — 15 lines of DOT visualization guidance added to the original 101-line skill.

See [`example/dialogue-graph/`](example/dialogue-graph/) for the full before/after comparison.

## Multi-Model Optimization

```bash
# Model profiles (auto-select best model for the use case)
factory.py --generate <task-id> --optimizer smart      # Highest intelligence
factory.py --generate <task-id> --optimizer balanced   # Good quality, reasonable cost
factory.py --generate <task-id> --optimizer cheap      # Bulk iterations
factory.py --generate <task-id> --optimizer fast       # Lowest latency

# Direct model selection via OpenRouter
factory.py --generate <task-id> --optimizer openrouter:google/gemini-2.5-pro
factory.py --generate <task-id> --optimizer openrouter:deepseek/deepseek-r1

# List all profiles
factory.py --list-models
```

## Dashboard

View pipeline status, benchmark trends, and SKILL.md diffs in the browser.

```bash
uv run --with streamlit --with pandas --with altair \
  streamlit run personalize-skill-factory/scripts/dashboard.py
```

Opens at http://localhost:8501.

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API for safety analysis, generation, and customization |
| `DAYTONA_API_KEY` | No | Daytona sandbox for dynamic safety analysis |
| `DAYTONA_BASE_URL` | No | Daytona endpoint (default: https://app.daytona.io/api) |
| `OPENROUTER_API_KEY` | No | OpenRouter API for multi-model optimization |

## Directory Structure

```
personalize-skill-factory/
├── SKILL.md              # Skill definition (makes this factory usable as a Claude skill)
├── README.md             # This file
├── scripts/
│   ├── factory.py        # Main pipeline orchestrator (all 6 steps)
│   ├── quarantine.py     # Sundial fetch + isolation
│   ├── safety_check.py   # Claude static + Daytona dynamic analysis
│   ├── benchmark.py      # Harbor run wrapper + score comparison
│   ├── dashboard.py      # Streamlit web dashboard
│   ├── event_log.py      # Structured JSONL event logger
│   ├── publish.py        # Sundial push
│   └── link_skills.sh    # Symlink generated/ → .claude/skills/
├── skills/
│   ├── staging/          # Unverified (from Sundial, not visible to Claude)
│   ├── developing/       # Safety-approved or AI-generated, iterating
│   │   └── <skill>/
│   │       ├── SKILL.md
│   │       ├── _baseline/    # Original version for comparison
│   │       └── _benchmarks/  # Auto-saved benchmark results
│   └── generated/        # Finalized, linked to .claude/skills/
├── example/              # Before/after comparison with benchmark data
│   └── dialogue-graph/
│       ├── README.md
│       ├── before/SKILL.md
│       └── after/SKILL.md
├── skillsbench/          # SkillsBench submodule (86 tasks, Harbor CLI)
└── logs/
    └── pipeline.jsonl    # Event log
```
