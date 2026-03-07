# Personalize Skill Factory — Requirements

## 目的

Sundial の汎用スキルを取得 → SkillsBench で測定 → Claude で改善 → 再測定。
before/after のスコア差で改善を証明する。

## 機能要件 (MVP)

1. **スキル取得**: `npx sundial-hub add <skill>` で SKILL.md を取得
2. **Before 測定**: `harbor run -p tasks/<task> -a claude-code` でスコア取得
3. **弱点分析 + 修正**: 失敗テスト + SKILL.md を Claude API に送り改善版を生成
4. **After 測定**: 改善版で再度 `harbor run` してスコア取得
5. **レポート**: before/after を比較出力

## フロー

```
factory.py <skill-name> <task-id>

1. npx sundial-hub add <skill-name>
2. harbor run → before score
3. Claude API: 失敗テスト + SKILL.md → 改善版 SKILL.md
4. harbor run → after score
5. print: before vs after
```

## 外部依存

| Service | 用途 | 認証 |
|---------|------|------|
| Sundial | スキル取得 | 不要 |
| Harbor (SkillsBench) | ベンチマーク | ANTHROPIC_API_KEY |
| Claude API | 分析・生成 | ANTHROPIC_API_KEY |

## 前提条件

- Python 3.12+, uv, Docker, Node.js (npx)
- `ANTHROPIC_API_KEY` が設定済み
- SkillsBench リポがローカルにある

## スコープ外

- GUI, Daytona 連携, 反復ループ, 自動公開, マルチモデル
