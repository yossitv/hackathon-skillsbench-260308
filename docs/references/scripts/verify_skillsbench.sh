#!/usr/bin/env bash
# SkillsBench (Harbor) 検証スクリプト
# Harbor CLI の動作確認とタスク一覧・バリデーションを行う

set -euo pipefail

SKILLSBENCH_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/skillsbench"

echo "=== SkillsBench (Harbor) 検証 ==="

echo ""
echo "--- Harbor CLI ---"
cd "$SKILLSBENCH_DIR"
uv run harbor --help 2>&1 | head -20

echo ""
echo "--- タスク一覧 (先頭10件 / 全$(ls tasks/ | wc -l | tr -d ' ')件) ---"
ls tasks/ | head -10

echo ""
echo "--- タスク検証 (3d-scan-calc) ---"
uv run harbor tasks check tasks/3d-scan-calc -m anthropic/claude-sonnet-4-20250514 2>&1 | head -30

echo ""
echo "SKILLSBENCH: OK"
