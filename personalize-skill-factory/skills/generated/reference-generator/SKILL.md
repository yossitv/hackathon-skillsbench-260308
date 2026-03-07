---
name: reference-generator
description: >
  Fetch useful web content and save as reference docs at docs/references/<domain>.md.
  Use when: (1) User provides a URL and wants to capture its content as a reusable
  reference, (2) User says "fetch this site", "save this as a reference", or
  "add reference for X", (3) User wants to build up a library of reference docs
  from documentation sites, specs, or repos.
---

# Reference Generator

Fetch site content and save as structured reference docs for reuse across skills.

## Workflow

1. User provides a URL
2. Fetch the site content (check for `llms.txt` or sitemap first for full coverage)
3. Extract structured knowledge: specs, APIs, patterns, examples, agent lists
4. Save to `docs/references/<domain-or-repo-name>.md`

### Naming Convention

Use the site's domain or repo name as the filename:

| Source | Filename |
|--------|----------|
| `https://agentskills.io` | `agentskills-io.md` |
| `https://harborframework.com/docs` | `harborframework-com.md` |
| `https://github.com/anthropics/skills` | `anthropics-skills.md` |
| `https://docs.astral.sh/uv/` | `docs-astral-sh-uv.md` |

### Content Guidelines

- Start with `# <Title> - <domain> Reference` and `Source: <url>`
- Extract ALL actionable content: specs, APIs, code examples, config formats
- Preserve structure (headings, tables, code blocks)
- Remove marketing fluff, navigation chrome, JS framework code
- Keep it comprehensive but focused on what an agent would need
- If the site has multiple pages, crawl the important ones (check `llms.txt` first)

### Storage Location

```
<project-root>/docs/references/
├── agentskills-io.md
├── harborframework-com.md
└── <domain-or-repo>.md
```

These docs are available to any skill via relative path from the project root.

## Existing References

Check what's already collected:

```bash
ls docs/references/
```
