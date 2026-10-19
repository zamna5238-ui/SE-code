"""Quick check that your Gemini key works (takes a few seconds).

Run:  python src/test_gemini.py
"""

import os
import sys

key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if not key:
    sys.exit("GEMINI_API_KEY is not set in this terminal. Set it first (see README).")
print(
    f"Key found (starts with '{key[:4]}', length {len(key)}). Contacting Gemini ...",
    flush=True,
)

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
try:
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=30_000))
    r = client.models.generate_content(
        model=model,
        contents="Reply with the single word OK.",
        config=types.GenerateContentConfig(temperature=0),
    )
    print(f"SUCCESS - {model} replied: {r.text.strip()!r}")
except Exception as e:  # noqa: BLE001
    print(f"FAILED - {type(e).__name__}: {str(e)[:400]}")
    print(
        "Fixes: make a new key at https://aistudio.google.com -> 'Get API key' (usually starts with 'AIza'),"
        " check your internet connection, then try again."
    )
    sys.exit(1)
