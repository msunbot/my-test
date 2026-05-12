"""
Fetch articles from RSS feeds. Falls back to HTTP scraping if feedparser
can't parse a feed cleanly.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx
from bs4 import BeautifulSoup

from config import Source, ALL_KEYWORDS

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; RoboticsNewsBot/1.0; "
        "+https://github.com/your-handle/robotics-news)"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


@dataclass
class Article:
    url: str
    title: str
    summary: str
    source_name: str
    lang: str
    published: Optional[str] = None
    full_text: Optional[str] = None
    relevance_score: float = 0.0
    translation: Optional[str] = None
    category: str = "general"


def _is_relevant(text: str) -> bool:
    """Quick keyword pass to avoid sending junk to Claude."""
    lower = text.lower()
    return any(kw in lower for kw in ALL_KEYWORDS)


def _parse_date(entry) -> Optional[str]:
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            return val
    return None


def fetch_source(source: Source, timeout: int = 15) -> list[Article]:
    """Fetch and parse one RSS source, return candidate Article objects."""
    articles: list[Article] = []
    try:
        feed = feedparser.parse(
            source.url,
            request_headers=HEADERS,
            agent=HEADERS["User-Agent"],
        )
        if feed.bozo and not feed.entries:
            log.warning("Feed parse error for %s: %s", source.name, feed.bozo_exception)
            return articles

        for entry in feed.entries[:20]:
            title   = getattr(entry, "title",   "") or ""
            summary = getattr(entry, "summary", "") or ""
            link    = getattr(entry, "link",    "") or ""

            if not link:
                continue

            combined = f"{title} {summary}"
            if not _is_relevant(combined):
                continue

            articles.append(Article(
                url=link,
                title=title.strip(),
                summary=_clean_html(summary)[:800],
                source_name=source.name,
                lang=source.lang,
                published=_parse_date(entry),
                category=source.category,
            ))

    except Exception as exc:
        log.error("Error fetching %s: %s", source.name, exc)

    return articles


def fetch_full_text(url: str, timeout: int = 12) -> Optional[str]:
    """Scrape body text from an article page (best-effort)."""
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Heuristic: longest <article> or <main>, else body
        for selector in ["article", "main", "[class*='article']", "[class*='content']", "body"]:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(separator="\n", strip=True)
                if len(text) > 300:
                    return text[:4000]

    except Exception as exc:
        log.debug("Full-text fetch failed for %s: %s", url, exc)

    return None


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(separator=" ", strip=True)


def fetch_all_sources(sources: list[Source]) -> list[Article]:
    """Fetch all sources and return deduplicated candidates."""
    seen_urls: set[str] = set()
    candidates: list[Article] = []

    for source in sources:
        articles = fetch_source(source)
        for art in articles:
            if art.url not in seen_urls:
                seen_urls.add(art.url)
                candidates.append(art)
        log.info("%-20s  %d candidates", source.name, len(articles))

    log.info("Total candidates across all sources: %d", len(candidates))
    return candidates
