"""
HTML scraper fallback for blogs without RSS feeds (e.g., Discord, Twitter/X).
"""
import re
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
import structlog
from bs4 import BeautifulSoup

from app.crawler.rate_limiter import domain_limiter, global_semaphore, extract_domain
from app.crawler.rss import HEADERS, is_relevant, _parse_date
from app.crawler.sources import BlogSource

logger = structlog.get_logger()

# URL path patterns that suggest an article (not a category/tag/page)
ARTICLE_PATH_PATTERNS = [
    r"/\d{4}/\d{2}/",        # /2024/03/
    r"/blog/[a-z0-9-]{10,}", # /blog/some-article-slug
    r"/engineering/[a-z]",   # /engineering/some-post
    r"/post/",
    r"/article/",
    r"/tech/",
]


def looks_like_article(url: str) -> bool:
    path = urlparse(url).path.lower()
    # Exclude pagination, category, tag, feed pages
    if any(x in path for x in ["/page/", "/tag/", "/category/", "/feed", "?", "#"]):
        return False
    return any(re.search(p, path) for p in ARTICLE_PATH_PATTERNS)


async def discover_article_links(source: BlogSource, client: httpx.AsyncClient) -> list[str]:
    """Fetch the blog index page and extract article links."""
    domain = extract_domain(source.url)
    await domain_limiter.acquire(domain)

    async with global_semaphore:
        try:
            resp = await client.get(source.url, headers=HEADERS, timeout=30, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            logger.error("scrape_index_failed", source=source.name, error=str(e))
            return []

    soup = BeautifulSoup(resp.text, "lxml")
    base_domain = f"{urlparse(source.url).scheme}://{urlparse(source.url).netloc}"
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(base_domain, href)
        # Only same-domain links that look like articles
        if urlparse(full_url).netloc == urlparse(source.url).netloc:
            if looks_like_article(full_url):
                links.add(full_url.split("#")[0].rstrip("/"))

    return list(links)[: source.crawl_limit]


async def crawl_scrape_source(source: BlogSource, existing_urls: set[str]) -> list[dict]:
    logger.info("crawling_scrape", source=source.name, url=source.url)
    results = []

    async with httpx.AsyncClient() as client:
        links = await discover_article_links(source, client)
        logger.info("scrape_links_found", source=source.name, count=len(links))

        for url in links:
            if url in existing_urls:
                continue

            domain = extract_domain(url)
            await domain_limiter.acquire(domain)

            async with global_semaphore:
                try:
                    resp = await client.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
                    resp.raise_for_status()
                    html = resp.text
                except Exception as e:
                    logger.warning("scrape_article_failed", url=url, error=str(e))
                    continue

            # Extract metadata + content
            metadata = trafilatura.extract_metadata(html)
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )

            title = (metadata.title if metadata and metadata.title else None) or url.split("/")[-1]
            author = metadata.author if metadata and metadata.author else None
            published_at = None
            if metadata and metadata.date:
                try:
                    from datetime import datetime, timezone
                    published_at = datetime.fromisoformat(metadata.date).replace(tzinfo=timezone.utc)
                except Exception:
                    pass

            if not is_relevant(title, content or "", source.topic_hints):
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
                "error_message": None if content else "Failed to extract content",
            })

    logger.info("scrape_crawl_done", source=source.name, articles=len(results))
    return results
