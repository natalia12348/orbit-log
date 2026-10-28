import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape

from .models import Item

USER_AGENT = "orbit-digest/1.0 (personal daily digest)"
ARXIV_URL = "http://export.arxiv.org/api/query"
ARXIV_QUERY = (
    "(cat:cs.RO OR cat:eess.SY OR cat:astro-ph.IM) AND "
    "(abs:space OR abs:spacecraft OR abs:satellite OR abs:rover OR abs:onboard "
    "OR abs:planetary OR abs:lunar OR abs:autonomous)"
)
FEEDS = [
    ("SpaceNews", "https://spacenews.com/feed/"),
    ("IEEE Spectrum Robotics", "https://spectrum.ieee.org/feeds/topic/robotics.rss"),
    ("ESA Engineering", "https://www.esa.int/rssfeed/Our_Activities/Space_Engineering_Technology"),
    ("NASA Technology", "https://www.nasa.gov/technology/feed/"),
    ("Phys.org Space", "https://phys.org/rss-feed/space-news/"),
]
ATOM = "{http://www.w3.org/2005/Atom}"
TAGS = re.compile(r"<[^>]+>")
SPACES = re.compile(r"\s+")


def fetch(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last = None
    for _ in range(2):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except OSError as error:
            last = error
    raise last


BROKEN_HYPHEN = re.compile(r"(\w)- (?=[a-z])")


def clean_text(value: str) -> str:
    text = SPACES.sub(" ", unescape(TAGS.sub(" ", value or ""))).strip()
    return BROKEN_HYPHEN.sub(r"\1-", text)


def parse_date(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return datetime.now(timezone.utc)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_arxiv(data: bytes) -> list:
    root = ET.fromstring(data)
    items = []
    for entry in root.findall(f"{ATOM}entry"):
        raw_id = (entry.findtext(f"{ATOM}id") or "").strip()
        if not raw_id:
            continue
        link = raw_id
        for node in entry.findall(f"{ATOM}link"):
            if node.get("rel") == "alternate" and node.get("href"):
                link = node.get("href")
        items.append(
            Item(
                id=re.sub(r"v\d+$", "", raw_id),
                kind="paper",
                title=clean_text(entry.findtext(f"{ATOM}title")),
                link=link,
                text=clean_text(entry.findtext(f"{ATOM}summary")),
                source="arXiv",
                published=parse_date(entry.findtext(f"{ATOM}published")),
                authors=[clean_text(a.findtext(f"{ATOM}name")) for a in entry.findall(f"{ATOM}author")],
            )
        )
    return items


def parse_feed(data: bytes, source: str) -> list:
    root = ET.fromstring(data)
    items = []
    if root.tag.endswith("rss") or root.find("channel") is not None:
        for node in root.iter("item"):
            link = (node.findtext("link") or "").strip()
            title = clean_text(node.findtext("title"))
            if not link or not title:
                continue
            items.append(
                Item(
                    id=(node.findtext("guid") or link).strip(),
                    kind="news",
                    title=title,
                    link=link,
                    text=clean_text(node.findtext("description")),
                    source=source,
                    published=parse_date(node.findtext("pubDate")),
                )
            )
        return items
    for node in root.findall(f"{ATOM}entry"):
        link = ""
        for ref in node.findall(f"{ATOM}link"):
            if ref.get("href"):
                link = ref.get("href")
                break
        title = clean_text(node.findtext(f"{ATOM}title"))
        if not link or not title:
            continue
        items.append(
            Item(
                id=(node.findtext(f"{ATOM}id") or link).strip(),
                kind="news",
                title=title,
                link=link,
                text=clean_text(node.findtext(f"{ATOM}summary") or node.findtext(f"{ATOM}content")),
                source=source,
                published=parse_date(node.findtext(f"{ATOM}updated") or node.findtext(f"{ATOM}published")),
            )
        )
    return items


def collect(fetcher=fetch, max_papers: int = 100) -> tuple:
    items = []
    errors = []
    query = urllib.parse.urlencode(
        {
            "search_query": ARXIV_QUERY,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_papers,
        }
    )
    try:
        items.extend(parse_arxiv(fetcher(f"{ARXIV_URL}?{query}")))
    except (OSError, ET.ParseError) as error:
        errors.append(f"arXiv: {error}")
    for name, url in FEEDS:
        try:
            items.extend(parse_feed(fetcher(url), name))
        except (OSError, ET.ParseError) as error:
            errors.append(f"{name}: {error}")
    return items, errors
