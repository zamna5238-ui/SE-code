"""Experiment 3 - AI language-model approach using Google Gemini (modelled on Etezadi et al., 2025).

Gemini reads the change and the whole requirement set, then gives every requirement an
impact score from 0 (certainly not affected) to 10 (certainly affected). Requirements are
ranked by that score, so the LLM is evaluated exactly like Experiments 1 and 2 (top-5/top-10).

Setup (free key):
  1. Get a Gemini API key at https://aistudio.google.com  ->  "Get API key"
  2. Set it before running:
       Windows PowerShell:  $env:GEMINI_API_KEY="paste-your-key"
       Windows cmd:         set GEMINI_API_KEY=paste-your-key
       Mac/Linux:           export GEMINI_API_KEY=paste-your-key
  3. python run_all.py

Optional: choose another model with GEMINI_MODEL (default: gemini-2.5-flash).

Answers are cached in results/llm_cache.json, so re-running costs nothing and gives the
same numbers (temperature 0). Delete the cache file to ask Gemini again.
"""

import json
import os
import re
import time

from common import RESULTS

NAME = "exp3_llm_gemini"
CACHE = RESULTS / "llm_cache.json"
DEFAULT_MODEL = "gemini-2.5-flash"

PROMPT = """You are a requirements engineer doing change impact analysis.

A change has been requested to a software requirements specification.
Decide, for EVERY requirement listed below, how likely it is to be affected by the change,
meaning it would have to be re-checked, updated or removed because of this change.

CHANGE REQUEST:
{change}

REQUIREMENTS:
{reqs}

Reply with ONLY a JSON object mapping every requirement ID to an integer from 0 to 10
(0 = certainly not affected, 10 = certainly affected). Example: {{"R1": 0, "R2": 8}}"""


def _key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def available():
    return bool(_key())


def model_name():
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)


_CLIENT = None


def _client():
    global _CLIENT
    if _CLIENT is None:
        from google import genai
        from google.genai import types

        # 90-second limit per request, so the program never hangs silently
        _CLIENT = genai.Client(
            api_key=_key(), http_options=types.HttpOptions(timeout=90_000)
        )
    return _CLIENT


def _call(prompt):
    from google.genai import types

    client = _client()
    for attempt in range(5):
        try:
            resp = client.models.generate_content(
                model=model_name(),
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )  # no "thinking": faster
            return resp.text
        except Exception as e:  # noqa: BLE001  (free tier: rate limits -> wait and retry)
            msg = str(e)
            if any(
                w in msg
                for w in (
                    "API_KEY_INVALID",
                    "API key not valid",
                    "UNAUTHENTICATED",
                    "PERMISSION_DENIED",
                    "401",
                    "403",
                )
            ):
                raise SystemExit(
                    f"[exp3] Gemini rejected the API key:\n  {msg[:300]}\n"
                    "Create a new key at https://aistudio.google.com -> Get API key, then run again."
                )
            wait = 15 * (attempt + 1)
            print(
                f"[exp3] Gemini error ({type(e).__name__}: {str(e)[:120]}); retrying in {wait}s"
            )
            time.sleep(wait)
    raise RuntimeError(
        "Gemini failed 5 times - check your GEMINI_API_KEY and internet connection"
    )


def _parse(text):
    match = re.search(r"\{.*\}", text or "", re.S)
    if not match:
        return {}
    return {
        k.strip(): float(v)
        for k, v in json.loads(match.group(0)).items()
        if isinstance(v, (int, float)) or str(v).replace(".", "", 1).isdigit()
    }


def _ask(change, cands):
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    key = f"{model_name()}|{change['source']}|{change['id']}"
    if key in cache:
        return cache[key]
    reqs = "\n".join(f"{rid}: {txt}" for rid, txt in cands.items())
    print(f"[exp3] asking Gemini ({model_name()}) about {change['id']} ...", flush=True)
    scores = _parse(_call(PROMPT.format(change=change["query"], reqs=reqs)))
    if not scores:
        print(
            f"[exp3] {change['id']}: could not read Gemini's answer - all scores set to 0"
        )
    cache[key] = scores
    CACHE.write_text(json.dumps(cache, indent=1))
    return scores


def rank(change, cands):
    scores = _ask(change, cands)
    ids = list(cands)
    # ties (and IDs the model forgot) keep the original order, so results are reproducible
    return sorted(ids, key=lambda r: -scores.get(r, 0.0))
