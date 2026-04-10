import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = structlog.get_logger()


async def _crawl_and_summarize():
    logger.info("scheduled_job_start", job="crawl_and_summarize")
    try:
        from app.crawler.pipeline import run_crawl_pipeline
        from app.summarizer.pipeline import run_summarization_pipeline
        await run_crawl_pipeline()
        await run_summarization_pipeline()
        logger.info("scheduled_job_done", job="crawl_and_summarize")
    except Exception as e:
        logger.error("scheduled_job_failed", job="crawl_and_summarize", error=str(e))


async def _summarize_sweep():
    """Catch any articles that were missed by the main pipeline."""
    try:
        from app.summarizer.pipeline import run_summarization_pipeline
        await run_summarization_pipeline()
    except Exception as e:
        logger.error("summarize_sweep_failed", error=str(e))


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    # Daily full crawl + summarize
    scheduler.add_job(
        _crawl_and_summarize,
        trigger="cron",
        hour=settings.crawl_schedule_hour,
        minute=settings.crawl_schedule_minute,
        id="daily_crawl",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Summarization sweep every 30 minutes (catches leftover pending articles)
    scheduler.add_job(
        _summarize_sweep,
        trigger="interval",
        minutes=30,
        id="summarize_sweep",
        replace_existing=True,
    )

    return scheduler
