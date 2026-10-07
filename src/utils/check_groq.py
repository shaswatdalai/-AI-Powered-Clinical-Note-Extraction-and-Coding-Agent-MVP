"""Check that the Groq API key works and list available Qwen models.

Run from the project root:
    python -m src.utils.check_groq
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("GROQ_API_KEY")

if not key:
    print("MISSING: GROQ_API_KEY is not set in the environment.")
    print("Check that .env exists in the project root and contains GROQ_API_KEY=...")
    raise SystemExit(1)

print(f"Key loaded: {key[:8]}...{key[-4:]} (length {len(key)})")

r = httpx.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {key}"},
    timeout=30.0,
)

print(f"Status: {r.status_code}")

if r.status_code != 200:
    print(f"Body: {r.text[:300]}")
    raise SystemExit(1)

models = r.json().get("data", [])
qwen_models = [m["id"] for m in models if "qwen" in m["id"].lower()]

print(f"Total models available: {len(models)}")
print(f"Qwen models available:  {len(qwen_models)}")
for m in qwen_models:
    print(f"  - {m}")

if not qwen_models:
    print("\nNo Qwen models found. Consider using a fallback like:")
    print("  llama-3.3-70b-versatile")
    print("  openai/gpt-oss-120b")
    print("Run this script again after switching to see the full list.")