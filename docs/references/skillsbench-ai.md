# SkillsBench - skillsbench.ai Reference

Source: https://www.skillsbench.ai

## Overview

SkillsBench is the first evaluation framework that measures how skills work for AI agents. Community-driven benchmark assessing agent performance on real-world engineering tasks across diverse domains.

- GitHub: https://github.com/benchflow-ai/skillsbench
- Organization: BenchFlow AI (xiangyi@benchflow.ai)
- License: Apache-2.0

## Key Stats

- **84 expert-curated tasks** across high-GDP-value domains (engineering, control systems, materials science, energy systems, etc.)
- **5 trials per task** with 95% confidence intervals
- **7 agent-model configurations** tested (Claude Code, Gemini CLI, Codex, etc.)
- **180 contributors**, 80% with PhDs or senior professional credentials
- **11 professional domains**

## Architecture (3 Layers)

1. **Skills Layer** - Domain-specific capabilities extending agent functionality
2. **Agent Harness Layer** - Execution environment managing tools and I/O
3. **Models Layer** - Foundational AI models providing computational capability

## Performance Results (Skill Impact)

Improvement when skills are enabled vs. without:

| Agent + Model | Improvement |
|--------------|-------------|
| Claude Code Opus 4.5 | +23.3 pp |
| Gemini CLI 3 Flash | +17.4 pp |
| Claude Code Haiku 4.5 | +16.7 pp |

## Task Structure

```
tasks/<task-id>/
├── instruction.md          # Task instructions for agent
├── task.toml               # Metadata and config
├── environment/
│   ├── Dockerfile          # Container setup
│   └── skills/             # Skills available to agent
├── solution/
│   └── solve.sh            # Oracle solution (must pass 100%)
└── tests/
    ├── test.sh             # Runs pytest
    └── test_outputs.py     # Test cases
```

## CLI (Harbor)

```bash
harbor tasks init "<task-name>"          # Create task
harbor tasks check <task-id>             # Validate
harbor run -p tasks/<task-id> -a oracle  # Run oracle
harbor run -p tasks/<task-id> -a claude-code -m 'anthropic/claude-opus-4-5'
```

## Related Projects (BenchFlow AI)

| Repo | Description |
|------|-------------|
| benchflow | AI benchmark runtime framework (Docker-based) |
| smolclaw | Mock environments for testing claw-like agents |
| pokemon-gym | Agent gym environment |
| terminal-bench-3 | Task submission repo |
| jfkarena | Arena system |
| paperbench | Paper benchmark |
