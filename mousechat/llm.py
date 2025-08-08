# mousechat/llm.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_KEY:
    raise RuntimeError("Missing OPENROUTER_API_KEY in .env")

# Pick any model supported by OpenRouter: https://openrouter.ai/docs#models
MODEL = "openai/gpt-4o-mini"  # example: can be openai/gpt-4o-mini, anthropic/claude-3.5-sonnet, etc.

def ask_llm(prompt: str) -> str:
    """
    Calls OpenRouter Chat Completions API and returns the model's text.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://yourapp.example",  # optional, for analytics
        "X-Title": "MouseChat Desktop",              # optional, for analytics
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter API error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()
