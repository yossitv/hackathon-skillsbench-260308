# Hermes Agent - hermes-agent.nousresearch.com Reference

Source: https://hermes-agent.nousresearch.com

## Overview

Hermes Agent is a self-improving autonomous AI agent by Nous Research. It runs persistently on a server, learns from experience, creates skills from completed tasks, and is accessible via Telegram, Discord, Slack, WhatsApp, and CLI.

- GitHub: https://github.com/NousResearch/hermes-agent
- License: MIT
- Skills format: agentskills.io compatible

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Prerequisites: Git only. Installer handles Python 3.11, Node.js v22, uv, ripgrep, ffmpeg.

Verify: `hermes doctor`, `hermes version`, `hermes status`

## Directory Structure

```
~/.hermes/
├── config.yaml       # Settings
├── .env              # API keys
├── auth.json         # OAuth credentials
├── SOUL.md           # Global persona (optional)
├── memories/         # MEMORY.md, USER.md
├── skills/           # All skills
│   ├── <category>/
│   │   └── <skill-name>/
│   │       ├── SKILL.md
│   │       ├── references/
│   │       ├── templates/
│   │       └── assets/
│   └── .hub/
│       ├── lock.json
│       ├── quarantine/
│       └── audit.log
├── cron/             # Scheduled jobs
├── sessions/         # Gateway sessions
└── logs/             # Error/gateway logs
```

## Skills System

Skills follow the agentskills.io open format. All skills reside in `~/.hermes/skills/`.

### Progressive Disclosure

| Level | Function | Output |
|-------|----------|--------|
| 0 | `skills_list()` | Name, description, category (~3k tokens) |
| 1 | `skill_view(name)` | Full content and metadata |
| 2 | `skill_view(name, path)` | Specific reference file |

### SKILL.md Format

```yaml
---
name: my-skill
description: Brief description
version: 1.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [python, automation]
    category: devops
---
```

Recommended body sections: "When to Use", "Procedure", "Pitfalls", "Verification".

### Platform Restrictions

| Value | Target |
|-------|--------|
| `macos` | macOS (Darwin) |
| `linux` | Linux |
| `windows` | Windows |

Omit `platforms` for universal availability.

### Skill Activation

Slash commands: `/gif-search funny cats`, `/axolotl help me fine-tune`

Natural language: `hermes chat --toolsets skills -q "What skills do you have?"`

### Agent-Managed Skills (skill_manage tool)

| Action | Purpose | Parameters |
|--------|---------|------------|
| `create` | New skill | `name`, `content`, optional `category` |
| `patch` | Targeted update | `name`, `old_string`, `new_string` |
| `edit` | Full rewrite | `name`, `content` |
| `delete` | Remove | `name` |
| `write_file` | Add supporting file | `name`, `file_path`, `file_content` |
| `remove_file` | Remove supporting file | `name`, `file_path` |

Creation triggers: complex tasks (5+ tool calls), error resolution, user corrections, non-trivial workflows.

### Skills Hub

```bash
hermes skills browse                              # Browse all
hermes skills search kubernetes                   # Search
hermes skills install openai/skills/k8s           # Install (with security scan)
hermes skills inspect openai/skills/k8s           # Preview
hermes skills list --source hub                   # List hub-installed
hermes skills audit                               # Rescan all
hermes skills uninstall k8s                        # Remove
hermes skills publish skills/my-skill --to github --repo owner/repo
hermes skills snapshot export setup.json           # Export config
hermes skills tap add myorg/skills-repo            # Add custom source
```

Trust tiers:

| Level | Source | Policy |
|-------|--------|--------|
| `builtin` | Shipped with Hermes | Always trusted |
| `official` | Repository optional-skills | No warnings |
| `trusted` | openai/skills, anthropics/skills | Trusted |
| `community` | All others | Blocked unless `--force` |

## Tools (40+)

| Category | Tools | Description |
|----------|-------|-------------|
| Web | `web_search`, `web_extract` | Search and extract web content |
| Terminal | `terminal`, `process` | Execute commands (local/docker/ssh/singularity/modal/daytona) |
| File | `read_file`, `write_file`, `patch`, `search_files` | File operations |
| Browser | `browser_navigate`, `browser_click`, `browser_type` | Browserbase automation |
| Vision | `vision_analyze` | Image analysis via multimodal models |
| Image Gen | `image_generate` | FLUX via FAL |
| TTS | `text_to_speech` | Edge TTS / ElevenLabs / OpenAI |
| Reasoning | `mixture_of_agents` | Multi-model reasoning |
| Skills | `skills_list`, `skill_view`, `skill_manage` | Skill management |
| Planning | `todo` | Task list for multi-step planning |
| Memory | `memory` | Persistent notes + user profile |
| Sessions | `session_search` | Search past conversations (FTS5) |
| Scheduling | `schedule_cronjob`, `list_cronjobs`, `remove_cronjob` | Cron management |
| Code | `execute_code` | Python scripts via RPC sandbox |
| Delegation | `delegate_task` | Spawn subagents |
| Interaction | `clarify` | Ask user questions |

Usage: `hermes chat --toolsets "web,terminal"`

## Memory System

Two files in `~/.hermes/memories/`, injected into system prompt at session start:

| File | Limit | Purpose |
|------|-------|---------|
| MEMORY.md | 2,200 chars | Agent's notes, environment facts, conventions |
| USER.md | 1,375 chars | User preferences, communication style |

Actions: `add`, `replace` (substring matching), `remove`.

Save: preferences, environment specifics, corrections, project conventions.
Skip: trivial info, searchable facts, large data, temporary paths.

Session search: SQLite + FTS5 for past conversation retrieval.
Honcho integration (optional): AI-generated user modeling.

## Configuration

### Inference Providers

**Primary:**
- Nous Portal (OAuth)
- OpenAI Codex (ChatGPT OAuth)
- OpenRouter (`OPENROUTER_API_KEY`)

**Chinese AI (first-class):**
- z.ai/GLM (`GLM_API_KEY`, provider: `zai`)
- Kimi/Moonshot (`KIMI_API_KEY`, provider: `kimi-coding`)
- MiniMax (`MINIMAX_API_KEY`, provider: `minimax`)

**Custom endpoint:**
```
OPENAI_BASE_URL=<url>
OPENAI_API_KEY=<key>
LLM_MODEL=<model>
```

**Self-hosted:** Ollama, vLLM, SGLang, llama.cpp, LiteLLM, ClawRouter

**Other compatible:** Together AI, Groq, DeepSeek, Fireworks, Cerebras, Mistral, Azure OpenAI, LocalAI, Jan

### Key Config Sections

```yaml
terminal:
  backend: local    # local, docker, ssh, singularity, modal, daytona
  timeout: 180

memory:
  memory_enabled: true
  memory_char_limit: 2200
  user_char_limit: 1375

compression:
  enabled: true
  threshold: 0.85

agent:
  reasoning_effort: ""  # xhigh, high, medium, low, minimal, none

display:
  tool_progress: all    # off, new, all, verbose

delegation:
  max_iterations: 50
  default_toolsets: [terminal, file, web]
```

### Optional API Keys

| Feature | Variable |
|---------|----------|
| Web scraping | `FIRECRAWL_API_KEY` |
| Browser automation | `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID` |
| Image generation | `FAL_KEY` |
| Premium TTS | `ELEVENLABS_API_KEY` |
| TTS + transcription | `VOICE_TOOLS_OPENAI_KEY` |
| RL Training | `TINKER_API_KEY`, `WANDB_API_KEY` |
| User modeling | `HONCHO_API_KEY` |

## Messaging Gateway

Platforms: Telegram, Discord, Slack, WhatsApp via single `hermes gateway` process.

```bash
hermes gateway setup     # Configure platforms
hermes gateway install   # System service
hermes gateway start/stop/restart/status
```

Session reset: daily at specific time or after idle (default 120 min).

Security: default deny. Options: allowlists, env var restrictions, DM pairing codes (1-hour expiry, crypto-random, rate-limited).

## Security (5-layer)

1. **User authorization** — allowlists, DM pairing
2. **Dangerous command approval** — blocks `rm -r`, `mkfs`, SQL DROP, `curl | sh`
3. **Container isolation** — Docker drops all caps, prevents privilege escalation, 256 process limit
4. **MCP credential filtering** — only safe env vars pass to subprocesses
5. **Context file scanning** — prompt injection detection

Note: dangerous command checks skipped in container backends (container is the boundary).

## CLI Commands

### Core
```bash
hermes                          # Interactive chat
hermes chat -q "query"          # Single query
hermes chat -c                  # Resume latest session
hermes chat -r <id>             # Resume specific session
hermes chat --model <name>      # Specific model
hermes chat --toolsets "web,terminal"
```

### Config
```bash
hermes setup                    # Full wizard
hermes config                   # View
hermes config edit              # Edit in editor
hermes config set KEY VAL       # Set value
hermes doctor                   # Diagnose
```

### Skills
```bash
hermes skills browse/search/install/inspect/list/audit/uninstall/publish
hermes skills snapshot export/import
hermes skills tap add/remove/list
```

### Sessions
```bash
hermes sessions list/export/delete/prune/stats
```

### Insights
```bash
hermes insights                 # Last 30 days
hermes insights --days 7        # Custom window
hermes insights --source telegram
```

### Slash Commands (in chat)
`/help`, `/quit`, `/clear`, `/new`, `/tools`, `/model`, `/history`, `/retry`, `/undo`, `/save`, `/compress`, `/usage`, `/paste`, `/cron`, `/skills`, `/<skill-name>`

## Context Files (auto-loaded)

- `AGENTS.md` — Project instructions (hierarchical, subdirs combined)
- `SOUL.md` — Persona (cwd first, then `~/.hermes/SOUL.md`)
- `.cursorrules`, `.cursor/rules/*.mdc` — Cursor IDE rules
- All capped at 20,000 characters

## Architecture

- Core loop: `run_agent.py` → build system prompt → LLM call → tool execution → SQLite persistence
- Self-registering tools via `registry.register()` at import
- Provider abstraction: any OpenAI-compatible API
- Gateway: `GatewayRunner` manages platform adapters
- Sessions in SQLite with FTS5 search
