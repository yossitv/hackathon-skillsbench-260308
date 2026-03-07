# Daytona - daytona.io Reference

Source: https://www.daytona.io/

## Overview

Daytona is secure and elastic infrastructure for running AI-generated code. It provides sandboxed environments for AI agents to execute code safely.

- GitHub: github.com/daytonaio/daytona (61.5k stars)
- License: GNU AGPL
- SDKs: Python, TypeScript, Go

## Key Features

- **Sub-90ms sandbox creation** from code to execution
- **Separated & isolated runtime** - zero risk to your infrastructure
- **Massive parallelization** for concurrent AI workflows
- **Unlimited persistence** - sandboxes run indefinitely
- **OCI/Docker compatibility** - use any Docker image
- **Environment snapshots** - save, restore, resume agent workflows
- **Multi-region** - India, EU Central/West, US East/West

## APIs

| API | Description |
|-----|-------------|
| Process Execution | Execute code/commands with real-time output streaming |
| File System | Full CRUD operations with granular permissions |
| Git Integration | Native Git operations and secure credential handling |
| LSP Support | Language server with multi-language completion and analysis |

## Quick Start

```python
from daytona import Daytona

daytona = Daytona()
sandbox = daytona.create()

response = sandbox.process.code_run('print("Hello World!")')
print(response.result)

response = sandbox.process.exec('echo "Hello"', cwd="/home/daytona", timeout=10)
print(response.result)

sandbox.fs.upload_file(b"Hello, World!", "/home/daytona/data.txt")
```

## Computer Use Sandbox

Virtual desktops controllable via code:
- **Linux (Ubuntu)** - Full root access
- **macOS** - iOS development and testing
- **Windows** - Windows-specific automation

## Docker Support

- Declarative Image Builder via SDK
- Image Templates based on Docker
- Docker in Docker inside sandboxes
- Dockerfile and Docker Compose support

## Pricing (Pay-as-You-Go)

| Resource | Price |
|----------|-------|
| vCPU | $0.0504/h |
| Memory (GiB) | $0.0162/h |
| Storage (GiB) | $0.000108/h |

$200 in free compute included. GPU options available.

## Security & Compliance

- Open-source codebase (no black boxes)
- Customer-managed compute (your cloud or on-prem)
- HIPAA, SOC 2, GDPR compliant

## Human in the Loop

- SSH Access to any sandbox
- VS Code Browser - open sandboxes in editor
- Web Terminal - full terminal in browser
