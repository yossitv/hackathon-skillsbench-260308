#!/usr/bin/env bash
# Sundial CLI 検証スクリプト
# スキル検索とインストール済みスキル一覧を確認する

set -euo pipefail

echo "=== Sundial CLI 検証 ==="

echo ""
echo "--- スキル検索 ---"
npx sundial-hub find "python testing" --limit 3 --json 2>&1

echo ""
echo "--- インストール済みスキル ---"
npx sundial-hub installed 2>&1 | head -20

echo ""
echo "SUNDIAL: OK"
