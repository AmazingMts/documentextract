from contextlib import asynccontextmanager
import structlog

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import articles, admin, sources

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await _seed_sources()
    await _reset_stuck_articles()

    # Start scheduler
    from app.scheduler.jobs import create_scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("scheduler_started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("scheduler_stopped")


async def _seed_sources():
    """Insert default sources if the sources table is empty."""
    from app.database import AsyncSessionLocal
    from app.models import Source
    from app.crawler.sources import SOURCES
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Source))
        if count == 0:
            for s in SOURCES:
                source = Source(
                    name=s.name,
                    company=s.company,
                    url=s.url,
                    feed_url=s.feed_url,
                    feed_type=s.feed_type,
                    topic_hints=str(s.topic_hints),
                )
                session.add(source)
            await session.commit()
            logger.info("sources_seeded", count=len(SOURCES))


async def _reset_stuck_articles():
    """Reset articles stuck in 'summarizing' from a previous crash."""
    from app.database import AsyncSessionLocal
    from app.models import Article
    from sqlalchemy import update

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(Article)
            .where(Article.status == "summarizing")
            .values(status="pending")
        )
        if result.rowcount:
            logger.info("reset_stuck_articles", count=result.rowcount)
        await session.commit()


app = FastAPI(
    title="Distributed Systems Blog Aggregator",
    description="Crawls and summarizes distributed systems engineering blogs from major tech companies.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(sources.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
