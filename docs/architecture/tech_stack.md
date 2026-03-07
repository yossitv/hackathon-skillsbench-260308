# Tech Stack

- **Language:** Python 3.12+
- **Package Manager:** uv
- **CLI:** argparse (標準ライブラリ)
- **Container:** Docker (Harbor が依存)

## Sponsor Services

### Sundial (sundialhub.com)
- **役割:** スキルの取得元 (Factory の入力)
- **CLI:** `npx sundial-hub add <skill-name>`
- **出力:** `.claude/skills/<skill-name>/SKILL.md` + references/, scripts/
- **仕様:** agentskills.io 準拠の SKILL.md フォーマット (YAML frontmatter + Markdown body)
- **50,000+ スキル** がレジストリに登録済み
- **参考:** docs/references/sundialhub-com.md

### SkillsBench / Harbor (BenchFlow)
- **役割:** before/after ベンチマーク測定 (Factory の評価軸)
- **CLI:** `uv run harbor run -p tasks/<task-id> -a claude-code`
- **出力:** テスト結果 (pytest ctrf.json), reward.txt (0 or 1)
- **84 タスク** across 11 domains, 5 trials per task, 95% CI
- **タスク構造:** instruction.md + task.toml + Dockerfile + tests/ + solution/
- **改善実績:** Claude Code Opus 4.5 でスキルあり +23.3pp
- **参考:** docs/references/skillsbench-ai.md

### Claude API (Anthropic)
- **役割:** 弱点分析 + 改善版 SKILL.md 生成 (Factory の中核ロジック)
- **SDK:** `pip install anthropic` (Python)
- **認証:** `ANTHROPIC_API_KEY` 環境変数
- **使い方:** 失敗テストログ + 現行 SKILL.md を送信 → 改善版を返却
- **ハッカソンクレジット:** Discord で申請可能
- **参考:** https://platform.claude.com/docs/en/about-claude/models/overview

### Daytona (daytona.io) — optional
- **役割:** 隔離されたサンドボックス環境
- **SDK:** `pip install daytona` (Python)
- **特徴:** Sub-90ms sandbox 起動, Docker-in-Docker, 環境スナップショット
- **Pricing:** $200 free compute included, vCPU $0.0504/h
- **MVP では不使用** — ローカル実行で十分。Phase 2 で統合検討
- **参考:** docs/references/daytona-io.md
