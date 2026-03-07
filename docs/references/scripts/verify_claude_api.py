#!/usr/bin/env python3
"""Claude (Anthropic) API 検証スクリプト
API コールを送信してレスポンスを確認する

前提:
  pip install anthropic
  .env に ANTHROPIC_API_KEY を設定
"""

import os

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

import anthropic

print("=== Claude API 検証 ===")

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say hello in exactly 5 words."}],
)

print(f"Response: {message.content[0].text}")
print(f"Model:    {message.model}")
print(f"Usage:    input={message.usage.input_tokens}, output={message.usage.output_tokens}")
print("")
print("CLAUDE API: OK")
