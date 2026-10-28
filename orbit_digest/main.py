import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from . import llm, render
from .rank import select
from .sources import FEEDS, collect, fetch
from .summarise import apply_summary

SEEN_LIMIT = 3000
DAY_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.html$")


def load_state(out: Path) -> dict:
    try:
        data = json.loads((out / "state.json").read_text(encoding="utf-8"))
        return {"seen": list(data.get("seen", [])), "days": dict(data.get("days", {}))}
    except (OSError, ValueError):
        return {"seen": [], "days": {}}


def save_state(out: Path, state: dict) -> None:
    state["seen"] = state["seen"][-SEEN_LIMIT:]
    (out / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")


def improve(item, use_llm: bool, poster=None) -> bool:
    apply_summary(item)
    if not use_llm or not llm.configured():
        return False
    data = llm.enhance(item, poster) if poster else llm.enhance(item)
    if not data:
        return False
    item.summary = [str(line) for line in data["summary"]][:3]
    item.why = str(data.get("why") or item.why)
    item.difficulty = str(data.get("difficulty") or item.difficulty)
    return True


def build_index(out: Path, state: dict) -> None:
    keys = sorted(m.group(1) for p in out.glob("*.html") if (m := DAY_FILE.match(p.name)))
    entries = []
    for number, key in enumerate(keys, 1):
        day = datetime.strptime(key, "%Y-%m-%d")
        counts = state["days"].get(key, {"papers": 0, "news": 0})
        entries.append((number, f"{key}.html", day.strftime("%A %d %B %Y"), counts["papers"], counts["news"]))
    entries.reverse()
    (out / "index.html").write_text(render.render_index(entries), encoding="utf-8")


def run(out_dir, now=None, use_llm: bool = True, fetcher=fetch, poster=None) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now(timezone.utc)
    local = now.astimezone()
    state = load_state(out)
    items, errors = collect(fetcher)
    papers, news = select(items, set(state["seen"]), now=now)
    used_llm = 0
    for item in papers + news:
        used_llm += improve(item, use_llm, poster)
    engine = "AI-assisted" if used_llm else "rule-based"
    key = local.strftime("%Y-%m-%d")
    entry = len({*state["days"], key})
    html = render.render_day(local.strftime("%A %d %B %Y"), entry, papers, news, engine, errors, len(FEEDS) + 1)
    (out / f"{key}.html").write_text(html, encoding="utf-8")
    state["seen"].extend(i.id for i in papers + news)
    state["days"][key] = {"papers": len(papers), "news": len(news)}
    save_state(out, state)
    build_index(out, state)
    return {"path": out / f"{key}.html", "papers": len(papers), "news": len(news), "errors": errors}


def cli() -> None:
    parser = argparse.ArgumentParser(description="Build today's space, robotics and AI digest.")
    parser.add_argument("--out", default=os.getenv("ORBIT_OUT", "digest"))
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()
    result = run(args.out, use_llm=not args.no_llm)
    print(f"{result['path']}  papers={result['papers']} news={result['news']}")
    for error in result["errors"]:
        print(f"warning: {error}")
