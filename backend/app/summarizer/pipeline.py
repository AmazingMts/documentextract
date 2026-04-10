"""
Summarization queue processor: picks up pending articles and calls Claude.
"""
import json
import re
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update

from app.database import AsyncSessionLocal
from app.models import Article, Source, CrawlRun
from app.summarizer.client import summarize_article
from app.config import settings

logger = structlog.get_logger()

BATCH_SIZE = 50


def _extract_topics(summary: str) -> list[str]:
    """Parse topic tags from the **Topics**: line in Claude's output."""
    match = re.search(r"\*\*Topics\*\*:\s*(.+)", summary, re.IGNORECASE)
    if not match:
        return []
    raw = match.group(1).strip()
    topics = [t.strip().lower() for t in re.split(r"[,;]", raw) if t.strip()]
    return topics[:15]  # cap at 15 tags


async def run_summarization_pipeline():
    """Process up to BATCH_SIZE pending articles."""
    logger.info("summarization_pipeline_start")

    async with AsyncSessionLocal() as session:
        # Fetch pending articles with their source info
        result = await session.execute(
            select(Article, Source.company, Source.name)
            .join(Source, Article.source_id == Source.id)
            .where(Article.status == "pending")
            .where(Article.is_relevant == True)
            .where(Article.raw_content != None)
            .order_by(Article.published_at.desc().nullslast())
            .limit(BATCH_SIZE)
        )
        rows = result.all()

    if not rows:
        logger.info("no_pending_articles")
        return

    logger.info("summarizing_articles", count=len(rows))
    summarized = 0
    failed = 0

    for article, company, source_name in rows:
        # Mark as summarizing (crash-safe)
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(Article)
                .where(Article.id == article.id)
                .values(status="summarizing")
            )
            await session.commit()

        try:
            summary = await summarize_article(
                title=article.title,
                company=company,
                url=article.url,
                content=article.raw_content,
                word_count=article.word_count,
            )

            topics = _extract_topics(summary)
            topics_json = json.dumps(topics)

            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(Article)
                    .where(Article.id == article.id)
                    .values(
                        status="done",
                        summary=summary,
                        summarized_at=datetime.now(timezone.utc),
                        summary_model=settings.summarize_model,
                        topics=topics_json,
                    )
                )
                await session.commit()

            summarized += 1
            logger.info("article_summarized", article_id=article.id, title=article.title[:60])

        except Exception as e:
            failed += 1
            logger.error("article_summarization_failed", article_id=article.id, error=str(e))
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(Article)
                    .where(Article.id == article.id)
                    .values(status="failed", error_message=str(e))
                )
                await session.commit()

    logger.info("summarization_pipeline_done", summarized=summarized, failed=failed)
    return summarized
