# Project Configuration

> **Purpose:** This file defines environment-specific commands for agents.

---

## Tech Stack & Environment

### Language & Framework
- **Language:** Python
- **Framework:** CLI (click/argparse)
- **Runtime:** Python 3.12+

### Manifest Files
- **Dependencies:** pyproject.toml
- **Lockfile:** uv.lock

### File Extensions
- **Main:** .py
- **Test:** test_*.py, *_test.py
- **Skill:** SKILL.md

### Source Roots
- generated-skills/personalize-skill-factory/scripts/

---

## Standard Commands

### Dependency Management
```bash
# Install dependencies
uv sync

# Update dependencies
uv lock --upgrade
```

### Testing
```bash
# Run all tests
uv run pytest

# Run SkillsBench benchmark
uv run harbor run -p tasks/<task-id> -a oracle
```

### Build & Compilation
```bash
# No build step (Python CLI)
```

### Development
```bash
# Run factory
uv run python generated-skills/personalize-skill-factory/scripts/factory.py <skill-name> <task-id>

# Sundial skill add
npx sundial-hub add <skill-name>

# Harbor task check
uv run harbor tasks check tasks/<task-id>
```

---

**Last Updated:** 2026-03-08
**Created by:** /reverse-docs command (0-1)
