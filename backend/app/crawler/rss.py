import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
import trafilatura
import structlog

from app.crawler.rate_limiter import domain_limiter, global_semaphore, extract_domain
from app.crawler.sources import BlogSource, RELEVANCE_KEYWORDS

logger = structlog.get_logger()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DistSysBlogBot/1.0; +https://github.com/AmazingMts/-)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                import time as time_mod
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return parsedate_to_datetime(val).replace(tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def is_relevant(title: str, excerpt: str, topic_hints: list[str]) -> bool:
    text = (title + " " + excerpt).lower()
    for kw in RELEVANCE_KEYWORDS:
        if kw in text:
            return True
    for hint in topic_hints:
        if hint.lower() in text:
            return True
    return False


async def fetch_full_content(url: str, client: httpx.AsyncClient) -> str | None:
    domain = extract_domain(url)
    await domain_limiter.acquire(domain)
    async with global_semaphore:
        try:
            resp = await client.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            content = trafilatura.extract(
                resp.text,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )
            return content
        except Exception as e:
            logger.warning("fetch_content_failed", url=url, error=str(e))
            return None


async def crawl_rss_source(source: BlogSource, existing_urls: set[str]) -> list[dict]:
    """
    Parse RSS feed for a source and return list of article dicts ready for DB insert.
    existing_urls: set of URLs already in the database (for deduplication).
    """
    logger.info("crawling_rss", source=source.name, feed_url=source.feed_url)
    results = []

    try:
        feed = feedparser.parse(
            source.feed_url,
            request_headers={"User-Agent": HEADERS["User-Agent"]},
        )
    except Exception as e:
        logger.error("rss_parse_failed", source=source.name, error=str(e))
        return results

    if feed.bozo and not feed.entries:
        logger.warning("rss_malformed", source=source.name, bozo_exception=str(feed.bozo_exception))
        return results

    entries = feed.entries[: source.crawl_limit]
    logger.info("rss_entries_found", source=source.name, count=len(entries))

    async with httpx.AsyncClient() as client:
        for entry in entries:
            url = getattr(entry, "link", None)
            if not url:
                continue
            if url in existing_urls:
                continue

            title = getattr(entry, "title", "Untitled")
            author = getattr(entry, "author", None)
            published_at = _parse_date(entry)
            excerpt = getattr(entry, "summary", "") or ""

            relevant = is_relevant(title, excerpt, source.topic_hints)

            if not relevant:
                results.append({
                    "url": url,
                    "title": title,
                    "author": author,
                    "published_at": published_at,
                    "raw_content": None,
                    "word_count": None,
                    "topics": "[]",
                    "is_relevant": False,
                    "status": "skipped",
                })
                continue

            # Fetch full article body
            content = await fetch_full_content(url, client)
            word_count = len(content.split()) if content else None

            results.append({
                "url": url,
                "title": title,
                "author": author,
                "published_at": published_at,
                "raw_content": content,
                "word_count": word_count,
                "topics": "[]",
                "is_relevant": True,
                "status": "pending" if content else "failed",
                "error_message": None if content else "Failed to fetch article content",
            })

    logger.info("rss_crawl_done", source=source.name, articles=len(results))
    return results
