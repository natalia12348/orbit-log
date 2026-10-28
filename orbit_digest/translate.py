import json
import time
import urllib.parse
import urllib.request
from html import unescape
from typing import Optional

from . import llm
from .summarise import WHY_TO_PL

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
DIFFICULTY_PL = {
    "Beginner": "Początkujący",
    "Intermediate": "Średni",
    "Hard": "Trudny",
    "Easy read": "Łatwa lektura",
}
KIND_PL = {"paper": "Praca", "news": "Wiadomość"}


def mymemory(text: str) -> Optional[str]:
    query = urllib.parse.urlencode({"q": text[:480], "langpair": "en|pl"})
    request = urllib.request.Request(f"{MYMEMORY_URL}?{query}", headers={"User-Agent": "orbit-digest/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode())
    except (OSError, ValueError):
        return None
    translated = unescape(str(data.get("responseData", {}).get("translatedText", ""))).strip()
    if str(data.get("responseStatus")) != "200" or not translated or translated.upper().startswith("MYMEMORY"):
        return None
    time.sleep(0.3)
    return translated


def default_translator():
    return llm.translate_text if llm.configured() else mymemory


def add_polish(item, translator) -> bool:
    title = translator(item.title)
    lines = [translator(line) for line in item.summary]
    if not title or not all(lines):
        return False
    why = WHY_TO_PL.get(item.why) or translator(item.why)
    if not why:
        return False
    item.pl = {
        "title": title,
        "summary": lines,
        "why": why,
        "difficulty": DIFFICULTY_PL.get(item.difficulty, item.difficulty),
        "kind": KIND_PL.get(item.kind, item.kind),
    }
    return True
