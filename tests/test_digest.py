import json
from datetime import datetime, timedelta, timezone

from orbit_digest import llm, render, translate
from orbit_digest.main import run
from orbit_digest.models import Item
from orbit_digest.rank import score_item, select
from orbit_digest.sources import clean_text, parse_arxiv, parse_feed
from orbit_digest.summarise import extractive_summary, paper_difficulty, why_it_matters

NOW = datetime(2026, 10, 29, 18, 0, tzinfo=timezone.utc)

ARXIV = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
<id>http://arxiv.org/abs/2610.00001v2</id>
<title>Onboard autonomy for a lunar rover
 using reinforcement learning</title>
<summary>Rovers on the Moon cannot wait for commands from Earth. We propose an onboard planner that uses reinforcement learning. Results show a 30% reduction in idle time. The method is tested in simulation. It is also tested on a small robot.</summary>
<published>2026-10-28T17:00:00Z</published>
<author><name>A. Author</name></author>
<author><name>B. Author</name></author>
<link rel="alternate" href="http://arxiv.org/abs/2610.00001v2"/>
</entry>
<entry>
<id>http://arxiv.org/abs/2610.00002v1</id>
<title>A note on tax law</title>
<summary>This paper discusses taxes and accounting standards in detail for everyone.</summary>
<published>2026-10-28T16:00:00Z</published>
<author><name>C. Author</name></author>
</entry>
</feed>"""

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<item><title>Satellite servicing robot passes tests</title><link>https://example.com/a</link><guid>g-1</guid>
<description>&lt;p&gt;A robot arm for satellite repair passed orbit tests.&lt;/p&gt;</description>
<pubDate>Thu, 29 Oct 2026 10:00:00 +0000</pubDate></item>
<item><title>Celebrity gossip</title><link>https://example.com/b</link><guid>g-2</guid>
<description>Nothing relevant.</description><pubDate>Thu, 29 Oct 2026 09:00:00 +0000</pubDate></item>
</channel></rss>"""


def fake_fetcher(url, timeout=25):
    if "arxiv" in url:
        return ARXIV.encode()
    if "spacenews" in url:
        return RSS.encode()
    raise OSError("offline")


def test_parse_arxiv_strips_version_and_whitespace():
    items = parse_arxiv(ARXIV.encode())
    assert items[0].id == "http://arxiv.org/abs/2610.00001"
    assert items[0].title == "Onboard autonomy for a lunar rover using reinforcement learning"
    assert items[0].authors == ["A. Author", "B. Author"]


def test_parse_rss_cleans_html():
    items = parse_feed(RSS.encode(), "Example")
    assert items[0].text == "A robot arm for satellite repair passed orbit tests."
    assert items[0].kind == "news"


def test_clean_text_repairs_line_break_hyphens():
    assert clean_text("goal- directed navigation") == "goal-directed navigation"
    assert clean_text("edges - moving contrast") == "edges - moving contrast"


def test_ranking_prefers_relevant_items():
    relevant, boring = parse_arxiv(ARXIV.encode())
    score_item(relevant)
    score_item(boring)
    assert relevant.score > 10 > boring.score
    assert {"space", "ai"} <= set(relevant.topics)


def test_select_skips_seen_and_old_items():
    items = parse_arxiv(ARXIV.encode())
    papers, _ = select(items, set(), now=NOW)
    assert [p.title.startswith("Onboard") for p in papers] == [True]
    papers, _ = select(items, {items[0].id}, now=NOW)
    assert papers == []
    papers, _ = select(items, set(), now=NOW + timedelta(days=30))
    assert papers == []


def test_extractive_summary_has_two_sentences_in_order():
    text = parse_arxiv(ARXIV.encode())[0].text
    summary = extractive_summary(text)
    assert len(summary) == 2
    assert text.index(summary[0]) < text.index(summary[1])


def test_run_respects_item_limits(tmp_path):
    result = run(tmp_path, now=NOW, use_llm=False, fetcher=fake_fetcher, papers=0, news=0, translator=False)
    assert result["papers"] == 0 and result["news"] == 0


def test_difficulty_and_relevance_text():
    assert paper_difficulty("A simple survey of robots.") == "Beginner"
    assert paper_difficulty("We prove a theorem on stochastic convergence of a Kalman filter.") == "Hard"
    assert "far from Earth" in why_it_matters(["space", "robotics", "ai"])


def test_render_escapes_markup():
    item = Item(id="1", kind="paper", title="<script>alert(1)</script>", link="https://x.test/?a=1&b=2", text="",
                source="arXiv", published=NOW, summary=["<b>bold</b>"], why="w", difficulty="Hard")
    html = render.render_day("Today", 1, [item], [], "rule-based", [], 6)
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html and "&lt;b&gt;bold" in html


def test_run_writes_digest_and_never_repeats(tmp_path):
    first = run(tmp_path, now=NOW, use_llm=False, fetcher=fake_fetcher, translator=False)
    assert first["papers"] == 1 and first["news"] == 1
    assert len(first["errors"]) == 4
    assert (tmp_path / "2026-10-29.html").exists() and (tmp_path / "index.html").exists()
    second = run(tmp_path, now=NOW, use_llm=False, fetcher=fake_fetcher, translator=False, force=True)
    assert second["papers"] == 0 and second["news"] == 0
    state = json.loads((tmp_path / "state.json").read_text())
    assert len(state["seen"]) == 2


def test_llm_output_is_validated():
    item = Item(id="1", kind="paper", title="t", link="l", text="x", source="s", published=NOW)
    good = lambda *a, **k: {"choices": [{"message": {"content": '{"summary": ["a","b","c"], "why": "w", "difficulty": "Hard"}'}}]}
    bad = lambda *a, **k: {"choices": [{"message": {"content": "no json here"}}]}
    assert llm.enhance(item, good)["summary"] == ["a", "b", "c"]
    assert llm.enhance(item, bad) is None


def test_polish_uses_templates_for_why_and_translator_for_text():
    item = Item(id="1", kind="paper", title="Rover", link="l", text="x", source="s", published=NOW,
                summary=["One.", "Two."], difficulty="Hard")
    item.why = "Useful background on how robots sense, plan and act in the real world."
    assert translate.add_polish(item, lambda text: f"PL:{text}")
    assert item.pl["title"] == "PL:Rover"
    assert item.pl["summary"] == ["PL:One.", "PL:Two."]
    assert item.pl["why"].startswith("Przydatne tło")
    assert item.pl["difficulty"] == "Trudny"


def test_polish_is_skipped_when_translation_fails():
    item = Item(id="1", kind="news", title="t", link="l", text="x", source="s", published=NOW,
                summary=["One."], why="custom", difficulty="Easy read")
    assert translate.add_polish(item, lambda text: None) is False
    assert item.pl == {}


def test_render_adds_click_to_switch_only_with_polish():
    base = dict(id="1", kind="paper", title="Title", link="https://x.test", text="", source="arXiv",
                published=NOW, summary=["Line."], why="Why.", difficulty="Beginner")
    plain = render.packet(Item(**base), 1)
    assert "data-pl" not in plain and "click for Polish" not in plain
    item = Item(**base)
    item.pl = {"title": "Tytuł <b>", "summary": ["Linia."], "why": "Dlaczego.", "difficulty": "Początkujący", "kind": "Praca"}
    html = render.packet(item, 1)
    assert "data-pl" in html and "click for Polish" in html
    assert "Tytuł &lt;b&gt;" in html and "Tłumaczenie maszynowe" in html


def test_second_run_on_the_same_day_keeps_the_page(tmp_path):
    first = run(tmp_path, now=NOW, use_llm=False, fetcher=fake_fetcher, translator=False)
    before = first["path"].read_text(encoding="utf-8")
    again = run(tmp_path, now=NOW, use_llm=False, fetcher=fake_fetcher, translator=False)
    assert again["skipped"] and again["papers"] == 1
    assert first["path"].read_text(encoding="utf-8") == before
