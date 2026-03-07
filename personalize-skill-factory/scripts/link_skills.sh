#!/usr/bin/env bash
# Link all generated skills to the parent project's .claude/skills/.
# Called by factory.py after finalizing a skill.
#
# Layout:
#   root/                          ← parent project
#   ├── .claude/skills/            ← symlinks go here
#   └── <repo>/                    ← this repo (cloned)
#       └── personalize-skill-factory/
#           ├── scripts/link_skills.sh  ← this file
#           └── skills/generated/

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
FACTORY_DIR="$(dirname "$SCRIPTS_DIR")"
REPO_DIR="$(dirname "$FACTORY_DIR")"
REPO_NAME="$(basename "$REPO_DIR")"
PARENT_DIR="$(dirname "$REPO_DIR")"
GENERATED_DIR="$FACTORY_DIR/skills/generated"
CLAUDE_SKILLS="$PARENT_DIR/.claude/skills"

mkdir -p "$CLAUDE_SKILLS"

# Link the factory itself
factory_link="$CLAUDE_SKILLS/personalize-skill-factory"
if [ ! -L "$factory_link" ]; then
  ln -s "../../$REPO_NAME/personalize-skill-factory" "$factory_link"
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
    ln -s "../../$REPO_NAME/personalize-skill-factory/skills/generated/$name" "$link"
    echo "Linked: $name"
  fi
done

echo "Done. Active skills:"
ls -1 "$CLAUDE_SKILLS"
