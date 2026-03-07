#!/usr/bin/env bash
# Link all generated skills to .claude/skills/ so Claude Code can discover them.
# Run from project root: bash personalize-skill-factory/scripts/link_skills.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GENERATED_DIR="$REPO_ROOT/personalize-skill-factory/skills/generated"
CLAUDE_SKILLS="$REPO_ROOT/.claude/skills"

mkdir -p "$CLAUDE_SKILLS"

# Always link the factory itself
factory_link="$CLAUDE_SKILLS/personalize-skill-factory"
if [ ! -L "$factory_link" ]; then
  ln -s ../../personalize-skill-factory "$factory_link"
  echo "Linked: personalize-skill-factory"
fi

# Link each generated skill
for skill_dir in "$GENERATED_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  link="$CLAUDE_SKILLS/$name"

  if [ -L "$link" ]; then
    echo "Skip (exists): $name"
  else
    ln -s "../../personalize-skill-factory/skills/generated/$name" "$link"
    echo "Linked: $name"
  fi
done

echo "Done. Active skills:"
ls -1 "$CLAUDE_SKILLS"
