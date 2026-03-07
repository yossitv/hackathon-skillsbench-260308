#!/usr/bin/env bash
# Setup Personalize Skill Factory for a project.
#
# Usage:
#   cd my-project
#   git clone <repo-url> personalize-skill-factory
#   cd personalize-skill-factory
#   bash setup.sh
#
# This creates symlinks in the PARENT directory's .claude/skills/
# so Claude Code discovers the factory and all generated skills.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_NAME="$(basename "$REPO_DIR")"
PARENT_DIR="$(dirname "$REPO_DIR")"
FACTORY_SUBDIR="$REPO_DIR/personalize-skill-factory"
CLAUDE_SKILLS="$PARENT_DIR/.claude/skills"

echo "Repo:     $REPO_DIR"
echo "Parent:   $PARENT_DIR"
echo "Factory:  $FACTORY_SUBDIR"
echo "Skills:   $CLAUDE_SKILLS"
echo ""

mkdir -p "$CLAUDE_SKILLS"

# Link the factory skill (personalize-skill-factory/ inside the repo)
factory_link="$CLAUDE_SKILLS/personalize-skill-factory"
if [ -L "$factory_link" ]; then
  echo "Skip (exists): personalize-skill-factory"
else
  ln -s "../../$REPO_NAME/personalize-skill-factory" "$factory_link"
  echo "Linked: personalize-skill-factory"
fi

# Link each generated skill
GENERATED_DIR="$FACTORY_SUBDIR/skills/generated"
if [ -d "$GENERATED_DIR" ]; then
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
fi

echo ""
echo "Done. Active skills in $CLAUDE_SKILLS:"
ls -1 "$CLAUDE_SKILLS"
