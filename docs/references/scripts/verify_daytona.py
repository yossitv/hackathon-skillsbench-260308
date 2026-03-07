#!/usr/bin/env python3
"""Daytona SDK 検証スクリプト
サンドボックス作成 → コード実行 → 削除を確認する

前提:
  pip install daytona-sdk
  .env に DAYTONA_API_KEY, DAYTONA_BASE_URL を設定
"""

import os
import sys

def load_dotenv():
    """簡易 .env ローダー"""
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

load_dotenv()

from daytona_sdk import Daytona, DaytonaConfig

config = DaytonaConfig(
    api_key=os.environ.get("DAYTONA_API_KEY"),
    api_url=os.environ.get("DAYTONA_BASE_URL", "https://app.daytona.io/api"),
    target="us",
)

print("=== Daytona SDK 検証 ===")

daytona = Daytona(config)

print("--- サンドボックス作成 ---")
sandbox = daytona.create()
print(f"Sandbox ID: {sandbox.id}")

print("--- コード実行 ---")
response = sandbox.process.code_run('print("Hello from Daytona sandbox!")')
print(f"Result: {response.result}")

print("--- サンドボックス削除 ---")
daytona.delete(sandbox)
print("Deleted OK")

print("")
print("DAYTONA: OK")
