# Sundial - sundialhub.com Reference

Source: https://www.sundialhub.com/

## Overview

Sundial is the open registry for agent skills - "the package manager for agent skills." Browse, install, and publish reusable AI capabilities for agents.

- GitHub: sundial-org
- Twitter: @sundialso
- Spec: agentskills.io
- Founders: Belinda Mo, Florent Tavernier

## What Are Agent Skills?

Reusable capabilities defined in the open SKILL.md format. Each skill is a folder with:
- SKILL.md (required) - YAML metadata + markdown instructions
- references/ (optional)
- scripts/ (optional)
- assets/ (optional)

Progressive disclosure: agents load only name + description (~200 bytes) initially, full instructions on activation.

## Getting Started

```bash
# 1. Add a skill
npx sundial-hub add <skill-name>

# 2. Launch agent
claude

# 3. Activate
/skill
```

## Popular Skills

| Skill | Description |
|-------|-------------|
| Vercel Deploy | Deploy apps and create preview links |
| PubMed Database | Search biomedical literature via API |
| AlphaFold Database | Access AI-predicted protein structures |
| Tinker | Fine-tune LLMs with SFT and RL training |
| AI Co-Scientist | Run research with hypothesis exploration |
| Agent Browser | Browse the web, fill forms, scrape data |
| Postgres Optimization | Database tuning |

## Compatible Agents

Claude Code, Cursor, GitHub Copilot, ChatGPT, Claude.ai, Codex CLI, Antigravity, OpenCode, Windsurf, Cline, Aider, Amp

## Key Properties

- **Portable** - works across platforms
- **Composable** - combine with other skills
- **Self-documenting** - easy to audit
- **Reusable** - any agent that reads markdown

## Verification Script

- [`scripts/verify_sundial.sh`](scripts/verify_sundial.sh) — スキル検索 (`--json`) とインストール済み一覧を確認
