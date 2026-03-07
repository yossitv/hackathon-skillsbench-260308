# Agent Skills - agentskills.io Reference

Source: https://agentskills.io

## Overview

Agent Skills are a lightweight, open format for extending AI agent capabilities with specialized knowledge and workflows. Originally developed by Anthropic, released as an open standard.

A skill is a folder containing a `SKILL.md` file with metadata and instructions, plus optional scripts, templates, and reference materials.

```
skill-name/
├── SKILL.md          # Required: instructions + metadata
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
```

## Supported Agents

| Agent | Skills Directory | Docs |
|-------|-----------------|------|
| Claude Code | `.claude/skills/` | https://code.claude.com/docs/en/skills |
| Claude | via platform | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| OpenAI Codex | `.codex/skills/` | https://developers.openai.com/codex/skills/ |
| Cursor | | https://cursor.com/docs/context/skills |
| VS Code (Copilot) | `.github/skills/` | https://code.visualstudio.com/docs/copilot/customization/agent-skills |
| GitHub Copilot | `.github/skills/` | https://docs.github.com/en/copilot/concepts/agents/about-agent-skills |
| Gemini CLI | | https://geminicli.com/docs/cli/skills/ |
| OpenCode | `.opencode/skill/` | https://opencode.ai/docs/skills/ |
| Goose | `.goose/skills/` | https://block.github.io/goose/docs/guides/context-engineering/using-skills/ |
| Amp | `.agents/skills/` | https://ampcode.com/manual#agent-skills |
| Factory | `.factory/skills/` | https://docs.factory.ai/cli/configuration/skills.md |
| Letta | | https://docs.letta.com/letta-code/skills/ |
| OpenHands | | https://docs.openhands.dev/overview/skills |
| Roo Code | | https://docs.roocode.com/features/skills |
| Junie | | https://junie.jetbrains.com/docs/agent-skills.html |
| Databricks | | https://docs.databricks.com/aws/en/assistant/skills |
| Snowflake | | https://docs.snowflake.com/en/user-guide/cortex-code/extensibility#extensibility-skills |
| Firebender | | https://docs.firebender.com/multi-agent/skills |
| TRAE | | https://www.trae.ai/blog/trae_tutorial_0115 |
| Spring AI | | https://spring.io/blog/2026/01/13/spring-ai-generic-agent-skills/ |
| Mux | | https://mux.coder.com/agent-skills |
| Mistral Vibe | | https://github.com/mistralai/mistral-vibe |
| Laravel Boost | | https://laravel.com/docs/12.x/boost#agent-skills |

Cross-client convention: `.agents/skills/` is the widely-adopted path for interoperability.

## Specification

### SKILL.md Format

YAML frontmatter + Markdown body:

```yaml
---
name: skill-name
description: A description of what this skill does and when to use it.
license: Apache-2.0                    # optional
compatibility: Requires git, docker    # optional, max 500 chars
metadata:                              # optional
  author: example-org
  version: "1.0"
allowed-tools: Bash(git:*) Read        # optional, experimental
---
```

### Frontmatter Fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | Max 64 chars. Lowercase, numbers, hyphens only. No leading/trailing/consecutive hyphens. Must match parent directory name. |
| `description` | Yes | Max 1024 chars. Describe what it does AND when to use it. |
| `license` | No | License name or reference to bundled file. |
| `compatibility` | No | Max 500 chars. Environment requirements. |
| `metadata` | No | Arbitrary key-value mapping. |
| `allowed-tools` | No | Space-delimited pre-approved tools (experimental). |

### Body Content

No format restrictions. Recommended sections:
- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

### Optional Directories

- **scripts/**: Executable code. Should be self-contained, include helpful error messages, handle edge cases.
- **references/**: Additional documentation loaded on demand. Keep files focused and small.
- **assets/**: Static resources (templates, images, data files).

## Progressive Disclosure (3-tier)

1. **Catalog (~50-100 tokens/skill)**: `name` + `description` loaded at session start for all skills
2. **Instructions (<5000 tokens recommended)**: Full `SKILL.md` body loaded when skill activates
3. **Resources (as needed)**: Files in `scripts/`, `references/`, `assets/` loaded on demand

Keep SKILL.md under 500 lines. Move detailed reference material to separate files.

## Client Implementation Guide

### Step 1: Discover Skills

Scan locations:

| Scope | Path | Purpose |
|-------|------|---------|
| Project | `<project>/.<client>/skills/` | Client-specific |
| Project | `<project>/.agents/skills/` | Cross-client |
| User | `~/.<client>/skills/` | Client-specific |
| User | `~/.agents/skills/` | Cross-client |

Rules:
- Look for subdirectories containing `SKILL.md`
- Skip `.git/`, `node_modules/`
- Project-level overrides user-level on name collisions
- Consider trust gating for project-level skills from untrusted repos

### Step 2: Parse SKILL.md

1. Extract YAML frontmatter between `---` delimiters
2. Parse `name` and `description` (required)
3. Body = everything after closing `---`
4. Be lenient: warn on issues but load when possible
5. Skip only if description missing or YAML completely unparseable

### Step 3: Disclose Available Skills

Build a catalog in the system prompt or tool description:

```xml
<available_skills>
  <skill>
    <name>pdf-processing</name>
    <description>Extract text and tables from PDF files...</description>
    <location>/path/to/skills/pdf-processing/SKILL.md</location>
  </skill>
</available_skills>
```

Include behavioral instructions telling the model how to activate skills.

### Step 4: Activate Skills

Two patterns:
- **File-read activation**: Model reads SKILL.md via standard file-read tool
- **Dedicated tool**: Register `activate_skill` tool that returns content

Wrap in structured tags for identification:

```xml
<skill_content name="pdf-processing">
[SKILL.md body]
<skill_resources>
  <file>scripts/extract.py</file>
</skill_resources>
</skill_content>
```

### Step 5: Context Management

- **Protect skill content from context compaction** (exempt from pruning)
- **Deduplicate activations** (track which skills are already loaded)
- **Subagent delegation** (optional): Run skill in separate session for complex workflows

## Evaluating Skill Quality

### Test Case Structure

Store in `evals/evals.json`:

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "Find top 3 months by revenue from data/sales.csv",
      "expected_output": "A bar chart showing top 3 months",
      "files": ["evals/files/sales.csv"],
      "assertions": [
        "Output includes a bar chart image",
        "Chart shows exactly 3 months",
        "Both axes are labeled"
      ]
    }
  ]
}
```

### Eval Workspace Structure

```
workspace/
└── iteration-N/
    ├── eval-<case>/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── timing.json    # {total_tokens, duration_ms}
    │   │   └── grading.json   # assertion results
    │   └── without_skill/
    │       └── ...
    └── benchmark.json         # aggregated stats
```

### Grading

Evaluate each assertion as PASS/FAIL with evidence:

```json
{
  "assertion_results": [
    {"text": "Output includes chart", "passed": true, "evidence": "Found chart.png"},
    {"text": "Axes labeled", "passed": false, "evidence": "X-axis has no label"}
  ],
  "summary": {"passed": 3, "failed": 1, "total": 4, "pass_rate": 0.75}
}
```

### Benchmark Aggregation

```json
{
  "run_summary": {
    "with_skill": {"pass_rate": {"mean": 0.83}, "tokens": {"mean": 3800}},
    "without_skill": {"pass_rate": {"mean": 0.33}, "tokens": {"mean": 2100}},
    "delta": {"pass_rate": 0.50, "tokens": 1700}
  }
}
```

### Iteration Loop

1. Give eval signals + current SKILL.md to LLM → propose improvements
2. Apply changes
3. Rerun all test cases in new `iteration-<N+1>/`
4. Grade and aggregate
5. Human review. Repeat until satisfied.

Key principles:
- Generalize fixes, don't patch for specific test cases
- Keep skill lean (fewer, better instructions)
- Explain the "why" (reasoning > rigid directives)
- Bundle repeated scripts into `scripts/`

## Script Design for Agents

- **No interactive prompts** (agents run non-interactive shells)
- **Include `--help`** output for discoverability
- **Helpful error messages** (what went wrong + what to try)
- **Structured output** (JSON/CSV over free-form text)
- **Idempotent** (agents may retry)
- **Safe defaults** (require `--confirm` for destructive ops)
- **Predictable output size** (support pagination/truncation)

### Self-contained Scripts (inline deps)

Python with PEP 723:
```python
# /// script
# dependencies = ["beautifulsoup4"]
# ///
```
Run: `uv run scripts/extract.py`

## Validation

```bash
skills-ref validate ./my-skill
```

Reference library: https://github.com/agentskills/agentskills/tree/main/skills-ref
Example skills: https://github.com/anthropics/skills
