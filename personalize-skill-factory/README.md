# Personalize Skill Factory

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  1. FETCH & QUARANTINE                                              │
│  ┌──────────────┐      ┌───────────────────┐                       │
│  │ Sundial Hub  │─────▶│ skills/staging/    │                       │
│  │ (npm CLI)    │      │ (isolated, not     │                       │
│  │              │      │  auto-loaded)      │                       │
│  └──────────────┘      └────────┬──────────┘                       │
│                                 │                                   │
│  2. SAFETY CHECK                ▼                                   │
│  ┌──────────────────────────────────────────┐                       │
│  │  Phase 1: Static Analysis                │                       │
│  │  ┌────────────┐                          │                       │
│  │  │ Claude API │ Scan SKILL.md + scripts  │                       │
│  │  │ (Sonnet)   │ for dangerous patterns   │                       │
│  │  └────────────┘                          │                       │
│  │                                          │                       │
│  │  Phase 2: Dynamic Analysis (optional)    │                       │
│  │  ┌────────────┐                          │                       │
│  │  │  Daytona   │ Execute in sandbox with  │                       │
│  │  │  Sandbox   │ network blocked          │                       │
│  │  └────────────┘                          │                       │
│  └──────────────────────┬───────────────────┘                       │
│                         │                                           │
│                         ▼ safe / review / dangerous                 │
│  3. APPROVE ─────▶ skills/developing/                               │
│                    (+ _baseline/ snapshot saved)                     │
│                         │                                           │
│  4. DEVELOPMENT LOOP    ▼                                           │
│  ┌──────────────────────────────────────────┐                       │
│  │                                          │                       │
│  │  ┌─────────────────┐   ┌──────────────┐ │                       │
│  │  │   Customize     │   │  Benchmark   │ │                       │
│  │  │                 │   │              │ │                       │
│  │  │  Claude API     │   │  Harbor CLI  │ │                       │
│  │  │  Hermes         │──▶│ (SkillsBench)│ │                       │
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
| Safety (Static) | **Claude API** | Scan for dangerous code patterns |
| Safety (Dynamic) | **Daytona Sandbox** | Execute in isolated environment with network blocked |
| Customize | **Claude API / Hermes / OpenRouter** | LLM-driven skill improvement |
| Benchmark | **Harbor CLI (SkillsBench)** | Run tasks with/without skill, measure score |
| Publish | **Sundial Hub** | Push improved skill back to registry |

## Dashboard

View pipeline status, benchmark trends, and SKILL.md diffs in the browser.

```bash
uv run --with streamlit --with pandas --with altair \
  streamlit run personalize-skill-factory/scripts/dashboard.py
```

Opens at http://localhost:8501.
