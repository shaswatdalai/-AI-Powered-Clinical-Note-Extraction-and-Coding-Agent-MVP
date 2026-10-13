import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("GROQ_API_KEY not set")
    raise SystemExit(1)

r = httpx.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "qwen/qwen3.8-27b",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
    },
    timeout=10.0,
)

print("status:", r.status_code)
print("retry-after:", r.headers.get("retry-after"))
print("x-ratelimit-remaining-requests:", r.headers.get("x-ratelimit-remaining-requests"))
print("x-ratelimit-remaining-tokens:", r.headers.get("x-ratelimit-remaining-tokens"))
print("x-ratelimit-limit-requests:", r.headers.get("x-ratelimit-limit-requests"))
print("x-ratelimit-limit-tokens:", r.headers.get("x-ratelimit-limit-tokens"))
print("body:", r.text[:300])  