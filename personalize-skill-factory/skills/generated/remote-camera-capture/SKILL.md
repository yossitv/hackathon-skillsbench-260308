---
name: remote-camera-capture
version: 2
description: >
  SSH経由でリモートPCのカメラを起動し、写真を撮影してローカルにコピー・表示する。
  Use when: (1) ユーザーがリモートPCのカメラで写真を撮りたい場合,
  (2) "リモートで撮影して", "SSHでカメラ起動", "remote camera" などと言った場合,
  (3) SSH接続先のカメラ映像をローカルで確認したい場合。
---

# Remote Camera Capture

SSH経由でリモートPCに接続し、カメラで写真を撮影してローカルに取得・表示するスキル。

## 前提条件

- リモートPCにSSHアクセスできること（鍵認証推奨）
- リモートPCにカメラデバイスが接続されていること
- リモートPCに撮影ツールがインストールされていること（後述）

## ワークフロー

1. ユーザーにSSH接続情報を確認する（ホスト、ユーザー名、ポート）
2. SSHでリモートPCに接続し、カメラで写真を撮影する
3. SCPで撮影した写真をローカルにコピーする
4. Readツールで画像を表示する
5. リモート側の一時ファイルを削除する

## 接続情報の管理

設定ファイル: `.claude/remote-camera.json`

```json
{
  "host": "192.168.1.100",
  "user": "pi",
  "port": 22,
  "key": "~/.ssh/id_rsa"
}
```

### フロー

1. まず `.claude/remote-camera.json` を Read で読み込む
2. **ファイルが存在する場合**: その設定を使って接続する。ユーザーに確認は不要
3. **ファイルが存在しない場合**: ユーザーに以下を聞き、回答を `.claude/remote-camera.json` に保存する

| パラメータ | 例 | デフォルト |
|-----------|-----|-----------|
| ホスト | `192.168.1.100` or `mypc.local` | なし（必須） |
| ユーザー名 | `pi` | 現在のユーザー |
| SSHポート | `22` | `22` |
| SSH鍵パス | `~/.ssh/id_rsa` | デフォルト鍵 |

**NOTE**: `.claude/remote-camera.json` is gitignored by default (`.claude/` pattern). Do not commit credentials.

## 撮影コマンド（OS別）

### Linux（Raspberry Pi等）

`libcamera` または `fswebcam` を使う：

```bash
# libcamera（Raspberry Pi OS Bullseye以降）
ssh user@host "libcamera-still -o /tmp/capture.jpg --width 1920 --height 1080 --nopreview -t 1000"

# fswebcam（USB Webカメラ）
ssh user@host "fswebcam -r 1920x1080 --no-banner /tmp/capture.jpg"

# ffmpeg（汎用、V4L2デバイス）
ssh user@host "ffmpeg -f v4l2 -video_size 1920x1080 -i /dev/video0 -frames:v 1 -y /tmp/capture.jpg"
```

### macOS（リモートがMacの場合）

```bash
# imagesnap（brew install imagesnap）
ssh user@host "imagesnap /tmp/capture.jpg"
```

### ツール検出の順序

リモートで以下を実行し、利用可能なツールを自動検出する：

```bash
ssh user@host "which libcamera-still fswebcam ffmpeg imagesnap 2>/dev/null"
```

**優先順位:** `libcamera-still` > `imagesnap` > `fswebcam` > `ffmpeg`

## ローカルへのコピーと表示

```bash
# SCPでローカルにコピー（保存先は /tmp/remote_capture_YYYYMMDD_HHMMSS.jpg）
scp user@host:/tmp/capture.jpg /tmp/remote_capture_$(date +%Y%m%d_%H%M%S).jpg
```

コピー後、Readツールでローカルの画像ファイルを読み込んで表示する。

```
Read tool → file_path: /tmp/remote_capture_YYYYMMDD_HHMMSS.jpg
```

## クリーンアップ

撮影後、リモート側の一時ファイルを削除：

```bash
ssh user@host "rm -f /tmp/capture.jpg"
```

## エラーハンドリング

| エラー | 対処 |
|-------|------|
| SSH接続失敗 | ホスト名・ポート・鍵を再確認。`ssh -v` で診断 |
| カメラデバイスなし | `ls /dev/video*` でデバイス確認。`v4l2-ctl --list-devices` も有用 |
| 撮影ツール未インストール | ユーザーにインストールを案内（`sudo apt install fswebcam` 等） |
| Permission denied | カメラデバイスの権限確認。`sudo usermod -aG video $USER` |
| SCP失敗 | SSH接続は成功しているか、ファイルパスは正しいか確認 |

## 実行例

```bash
# 1. ツール検出
ssh pi@192.168.1.100 "which libcamera-still fswebcam ffmpeg 2>/dev/null"

# 2. 撮影
ssh pi@192.168.1.100 "fswebcam -r 1920x1080 --no-banner /tmp/capture.jpg"

# 3. ローカルにコピー
scp pi@192.168.1.100:/tmp/capture.jpg /tmp/remote_capture_20260308_143000.jpg

# 4. Readツールで表示（Claude Codeが画像を認識して表示）

# 5. クリーンアップ
ssh pi@192.168.1.100 "rm -f /tmp/capture.jpg"
```
