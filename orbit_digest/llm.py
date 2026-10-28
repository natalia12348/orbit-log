import json
import os
import re
import urllib.request
from typing import Optional

PROMPT = (
    "You write a daily digest for a junior who wants to work in space robotics and AI. "
    "Return ONLY JSON with keys: \"summary\" (list of exactly 2 short plain-English sentences), "
    "\"why\" (one sentence on why it matters for that career), "
    "\"difficulty\" (Beginner, Intermediate or Hard for a paper; Easy read for news)."
)


def post(url: str, payload: dict, headers: dict, timeout: int = 30) -> dict:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def configured() -> bool:
    return bool(os.getenv("LLM_BASE_URL") or os.getenv("LLM_API_KEY"))


def enhance(item, poster=post) -> Optional[dict]:
    base = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    headers = {"Content-Type": "application/json"}
    if os.getenv("LLM_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['LLM_API_KEY']}"
    payload = {
        "model": os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"Title: {item.title}\nType: {item.kind}\nText: {item.text[:3000]}"},
        ],
    }
    try:
        content = poster(f"{base}/chat/completions", payload, headers)["choices"][0]["message"]["content"]
        match = re.search(r"\{.*\}", content, re.S)
        data = json.loads(match.group(0)) if match else None
    except (OSError, KeyError, IndexError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("summary"), list) or not data["summary"]:
        return None
    return data


def translate_text(text: str, poster=post) -> Optional[str]:
    base = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    headers = {"Content-Type": "application/json"}
    if os.getenv("LLM_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['LLM_API_KEY']}"
    payload = {
        "model": os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "Translate the user's text from English to natural Polish. Keep technical terms accurate. Return only the translation."},
            {"role": "user", "content": text},
        ],
    }
    try:
        result = poster(f"{base}/chat/completions", payload, headers)["choices"][0]["message"]["content"].strip()
    except (OSError, KeyError, IndexError, ValueError):
        return None
    return result or None
