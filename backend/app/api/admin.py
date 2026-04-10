import asyncio

from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from sqlalchemy import update

from app.config import settings
from app.schemas import CrawlRunOut

router = APIRouter(prefix="/admin", tags=["admin"])


def _check_key(key: str):
    if key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")


@router.post("/crawl", response_model=dict)
async def trigger_crawl(background_tasks: BackgroundTasks, x_admin_key: str = Header(...)):
    _check_key(x_admin_key)

    async def _run():
        from app.crawler.pipeline import run_crawl_pipeline
        from app.summarizer.pipeline import run_summarization_pipeline
        await run_crawl_pipeline()
        await run_summarization_pipeline()

    background_tasks.add_task(_run)
    return {"status": "crawl_started", "message": "Crawl and summarization running in background"}


@router.post("/resummmarize", response_model=dict)
async def trigger_resummarize(
    background_tasks: BackgroundTasks,
    status_filter: str = "failed",
    x_admin_key: str = Header(...),
):
    """Re-queue articles with a given status for re-summarization."""
    _check_key(x_admin_key)

    if status_filter not in ("failed", "pending", "all"):
        raise HTTPException(status_code=400, detail="status_filter must be failed, pending, or all")

    async def _run():
        from app.database import AsyncSessionLocal
        from app.models import Article
        from app.summarizer.pipeline import run_summarization_pipeline

        async with AsyncSessionLocal() as session:
            where_clause = (
                Article.is_relevant == True
            )
            if status_filter != "all":
                where_clause = where_clause & (Article.status == status_filter)
            else:
                where_clause = where_clause & (Article.status.in_(["failed", "skipped"]))

            await session.execute(
                update(Article)
                .where(where_clause)
                .values(status="pending")
            )
            await session.commit()

        await run_summarization_pipeline()

    background_tasks.add_task(_run)
    return {"status": "resummarize_started", "filter": status_filter}


@router.get("/stats", response_model=dict)
async def get_stats(x_admin_key: str = Header(...)):
    _check_key(x_admin_key)

    from app.database import AsyncSessionLocal
    from app.models import Article, Source, CrawlRun
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as session:
        total_articles = await session.scalar(select(func.count()).select_from(Article))
        done = await session.scalar(select(func.count()).select_from(Article).where(Article.status == "done"))
        pending = await session.scalar(select(func.count()).select_from(Article).where(Article.status == "pending"))
        failed = await session.scalar(select(func.count()).select_from(Article).where(Article.status == "failed"))
        skipped = await session.scalar(select(func.count()).select_from(Article).where(Article.status == "skipped"))
        sources = await session.scalar(select(func.count()).select_from(Source).where(Source.active == True))
        last_run = (await session.execute(
            select(CrawlRun).order_by(CrawlRun.started_at.desc()).limit(1)
        )).scalar_one_or_none()

    return {
        "total_articles": total_articles,
        "done": done,
        "pending": pending,
        "failed": failed,
        "skipped": skipped,
        "active_sources": sources,
        "last_crawl": {
            "started_at": last_run.started_at.isoformat() if last_run else None,
            "status": last_run.status if last_run else None,
            "articles_new": last_run.articles_new if last_run else 0,
        },
    }
