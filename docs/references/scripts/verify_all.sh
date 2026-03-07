#!/usr/bin/env bash
# 全サービス一括検証スクリプト
#
# 使い方:
#   cd docs/references/scripts
#   bash verify_all.sh
#
# 前提:
#   - .env に ANTHROPIC_API_KEY, DAYTONA_API_KEY, DAYTONA_BASE_URL を設定
#   - pip install anthropic daytona-sdk
#   - npx (Node.js) が利用可能
#   - skillsbench/ に uv 環境がセットアップ済み

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# .env を読み込み
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  source "$ROOT_DIR/.env"
  set +a
  echo "[.env loaded]"
fi

echo ""
echo "========================================="
echo " 1/4  Sundial"
echo "========================================="
bash "$SCRIPT_DIR/verify_sundial.sh"

echo ""
echo "========================================="
echo " 2/4  Daytona"
echo "========================================="
python3 "$SCRIPT_DIR/verify_daytona.py"

echo ""
echo "========================================="
echo " 3/4  Claude API"
echo "========================================="
python3 "$SCRIPT_DIR/verify_claude_api.py"

echo ""
echo "========================================="
echo " 4/4  SkillsBench (Harbor)"
echo "========================================="
bash "$SCRIPT_DIR/verify_skillsbench.sh"

echo ""
echo "========================================="
echo " ALL SERVICES VERIFIED"
echo "========================================="
