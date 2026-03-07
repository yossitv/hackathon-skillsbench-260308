# Personalize Skill Factory + Crane Game Agent

## Concept

2段構成で2トラックに提出する。

### Step 1: Track 05 Continual Learning — Personalize Skill Factory

Sundial の汎用スキルを取得 → SkillsBench でベンチマーク → 弱点分析 → 自動カスタマイズ → 再ベンチマークで改善を証明するパイプライン。

### Step 2: Track 02 Physical World — Crane Game × Jetson × OpenClaw

Factory の実例として、物理クレーンゲーム（Jetson 搭載）に OpenClaw を導入して収益化する環境構築スキルを Factory に作らせる。

## 開発フロー（スポンサーツール全活用）

```
┌─────────────────────────────────────────────────────┐
│  1. スキル取得         Sundial (sundialhub.com)      │
│     npx sundial-hub add <skill>                      │
│     → 汎用スキルを Sundial レジストリから取得          │
├─────────────────────────────────────────────────────┤
│  2. 開発環境           Daytona (daytona.io)          │
│     daytona.create() でサンドボックス起動              │
│     → スキルの編集・テストを隔離環境で実行             │
├─────────────────────────────────────────────────────┤
│  3. カスタマイズ       Claude (Anthropic credits)     │
│     Claude API でスキルの弱点分析 + 改善案生成         │
│     → ベンチマーク失敗パターンから自動修正             │
├─────────────────────────────────────────────────────┤
│  4. ベンチマーク       SkillsBench (BenchFlow)        │
│     harbor run -p tasks/<task> -a claude-code         │
│     → before/after スコアで改善を定量評価             │
├─────────────────────────────────────────────────────┤
│  5. 実機検証           Jetson + OpenClaw              │
│     Factory が生成したスキルでクレーンゲーム環境構築    │
│     → 物理ハードウェアで動作確認                      │
└─────────────────────────────────────────────────────┘
```

## スポンサーサービス活用チェック

### Track 05: Continual Learning (Personalize Skill Factory)

- [x] **Sundial** — スキルの取得・検索・公開（Factory の入力源）
- [x] **Daytona** — スキル編集・テストのサンドボックス
- [x] **Claude (Anthropic)** — スキル弱点分析・改善案生成（Factory の中核）
- [x] **SkillsBench (BenchFlow)** — before/after ベンチマーク評価（Factory の評価軸）
- [ ] **Nous Research** — 使わない見込み（SkillsBench が Hermes 未対応の可能性）
- [ ] **Founders, Inc.** — 会場のみ、サービス利用なし

### Track 02: Physical World (Crane Game x Jetson x OpenClaw)

- [x] **Sundial** — ロボティクス/Jetson 系スキル探索・完成スキルの公開
- [ ] **Daytona** — 実機 Jetson で検証するため不要の可能性
- [x] **Claude (Anthropic)** — エージェント実行・スキル生成
- [x] **SkillsBench (BenchFlow)** — クレーンゲームタスクを作成してベンチマーク
- [ ] **Nous Research** — 使わない見込み
- [ ] **Founders, Inc.** — 会場のみ、サービス利用なし

## Demo (2.5分)

1. (30s) Sundial でスキルを取得、SkillsBench で before スコア
2. (60s) Factory が Claude で弱点分析 → カスタムスキル生成（Daytona 上で実行）
3. (30s) after スコアで改善を見せる
4. (30s) 実例: クレーンゲーム環境構築スキルを Factory に生成させた結果

## TODO

- [ ] OpenClaw の詳細調査（GitHub リポ、仕様）
- [ ] Sundial でクレーンゲーム/Jetson/ロボティクス関連スキルを探す
- [ ] SkillsBench の Physical World タスクを確認
- [ ] Factory のカスタマイズロジック設計（Claude API 活用）
- [ ] Daytona サンドボックスでの開発環境セットアップ
- [ ] before/after ベンチマーク実行

---

# Tracks Reference

Data Tracks

01
Computer Science
Software Engineering
Machine Learning
Cybersecurity
Create realistic task scenarios that challenge frontier models. Design complete skill sets for software development, ML pipelines, and security operations.


02
Physical World
Robotics
Manufacturing
Energy
Infrastructure
Build tasks for agents operating in physical domains. Design skill sets for hardware control, sensor integration, and real-world system management.


03
Industry
Healthcare
Finance
Office Suite
Insurance
Media Production
Create complex industry workflows that test agent reasoning. Design complete skill sets for domain-specific document processing and analysis.


04
Natural Science
Physics
Mathematics
Chemistry
Biology
Build tasks requiring scientific reasoning and experimental design. Create skill sets for data analysis, hypothesis testing, and research workflows.

Continual Learning Track

05
Continual Learning
Recursive Language Models
GEPA
Reinforcement Learning
In-Context Learning
Improve models or prompts iteratively using methods like Recursive Language Models, GEPA on the in-context learning layer, or RL on the model layer. We select 50 tasks from SkillsBench for evaluation. Your method will be tested on the original SkillsBench and applied to other benchmarks like Terminal-Bench.