"""Check that the Groq API key works and list available models.

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
print(f"Total models available: {len(models)}")
print("All model IDs:")
for m in models:
    print(f"  - {m['id']}")