"""
Crawl orchestrator: iterates all active sources, deduplicates, stores new articles.
"""
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database import AsyncSessionLocal
from app.models import Source, Article, CrawlRun
from app.crawler.sources import SOURCES
from app.crawler.rss import crawl_rss_source
from app.crawler.scraper import crawl_scrape_source

logger = structlog.get_logger()


async def get_existing_urls() -> set[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Article.url))
        return {row[0] for row in result.all()}


async def run_crawl_pipeline() -> CrawlRun:
    """
    Full crawl: fetch all active sources, insert new articles.
    Returns the completed CrawlRun record.
    """
    logger.info("crawl_pipeline_start")

    async with AsyncSessionLocal() as session:
        run = CrawlRun(status="running", started_at=datetime.now(timezone.utc))
        session.add(run)
        await session.commit()
        await session.refresh(run)
        run_id = run.id

    total_found = 0
    total_new = 0

    try:
        existing_urls = await get_existing_urls()

        # Fetch source IDs from DB
        async with AsyncSessionLocal() as session:
            db_sources = (await session.execute(
                select(Source).where(Source.active == True)
            )).scalars().all()
            source_map = {s.url: s.id for s in db_sources}

        # Map our static SOURCES to their DB IDs
        active_sources = [s for s in SOURCES if s.url in source_map]

        for src in active_sources:
            source_id = source_map[src.url]
            try:
                if src.feed_type == "rss":
                    articles_data = await crawl_rss_source(src, existing_urls)
                else:
                    articles_data = await crawl_scrape_source(src, existing_urls)
            except Exception as e:
                logger.error("source_crawl_failed", source=src.name, error=str(e))
                articles_data = []

            total_found += len(articles_data)
            new_count = await _store_articles(articles_data, source_id)
            total_new += new_count

            # Update source last_crawled
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(Source)
                    .where(Source.id == source_id)
                    .values(last_crawled=datetime.now(timezone.utc))
                )
                await session.commit()

            # Add newly discovered URLs to the dedup set
            for a in articles_data:
                existing_urls.add(a["url"])

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(CrawlRun)
                .where(CrawlRun.id == run_id)
                .values(
                    status="completed",
                    finished_at=datetime.now(timezone.utc),
                    articles_found=total_found,
                    articles_new=total_new,
                )
            )
            await session.commit()

        logger.info("crawl_pipeline_done", found=total_found, new=total_new)

    except Exception as e:
        logger.error("crawl_pipeline_failed", error=str(e))
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(CrawlRun)
                .where(CrawlRun.id == run_id)
                .values(
                    status="failed",
                    finished_at=datetime.now(timezone.utc),
                    error=str(e),
                )
            )
            await session.commit()
        raise

    async with AsyncSessionLocal() as session:
        run = await session.get(CrawlRun, run_id)
        return run


async def _store_articles(articles_data: list[dict], source_id: int) -> int:
    """Insert articles into DB, skipping duplicates. Returns count of new rows."""
    if not articles_data:
        return 0

    new_count = 0
    async with AsyncSessionLocal() as session:
        for data in articles_data:
            # Use INSERT OR IGNORE semantics via try/except on the unique constraint
            from sqlalchemy.exc import IntegrityError
            try:
                article = Article(
                    source_id=source_id,
                    url=data["url"],
                    title=data["title"],
                    author=data.get("author"),
                    published_at=data.get("published_at"),
                    raw_content=data.get("raw_content"),
                    word_count=data.get("word_count"),
                    topics=data.get("topics", "[]"),
                    is_relevant=data.get("is_relevant", False),
                    status=data.get("status", "pending"),
                    error_message=data.get("error_message"),
                )
                session.add(article)
                await session.flush()
                new_count += 1
            except IntegrityError:
                await session.rollback()
            except Exception as e:
                await session.rollback()
                logger.warning("article_insert_failed", url=data.get("url"), error=str(e))

        await session.commit()

    return new_count
