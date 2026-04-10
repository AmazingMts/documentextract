import json
import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Article, Source
from app.schemas import ArticleOut, ArticleDetail, ArticleListResponse

router = APIRouter()


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    company: Optional[str] = None,
    topic: Optional[str] = None,
    q: Optional[str] = None,
    sort: str = Query("newest", pattern="^(newest|oldest)$"),
    db: AsyncSession = Depends(get_db),
):
    base_query = (
        select(Article, Source.company, Source.name)
        .join(Source, Article.source_id == Source.id)
        .where(Article.status == "done")
    )

    if company:
        base_query = base_query.where(Source.company == company)
    if topic:
        base_query = base_query.where(Article.topics.contains(topic.lower()))
    if q:
        q_lower = f"%{q.lower()}%"
        base_query = base_query.where(
            or_(
                func.lower(Article.title).like(q_lower),
                func.lower(Article.summary).like(q_lower),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = await db.scalar(count_query) or 0

    # Ordering
    order_col = Article.published_at if sort in ("newest", "oldest") else Article.published_at
    if sort == "newest":
        base_query = base_query.order_by(order_col.desc().nullslast())
    else:
        base_query = base_query.order_by(order_col.asc().nullsfirst())

    # Pagination
    offset = (page - 1) * limit
    base_query = base_query.offset(offset).limit(limit)

    result = await db.execute(base_query)
    rows = result.all()

    items = []
    for article, company_name, source_name in rows:
        item = ArticleOut(
            id=article.id,
            source_id=article.source_id,
            url=article.url,
            title=article.title,
            author=article.author,
            published_at=article.published_at,
            crawled_at=article.crawled_at,
            summary=article.summary,
            summarized_at=article.summarized_at,
            topics=article.topics,
            is_relevant=article.is_relevant,
            status=article.status,
            word_count=article.word_count,
            company=company_name,
            source_name=source_name,
        )
        items.append(item)

    # Collect distinct companies and topics for filter UI
    companies_result = await db.execute(
        select(Source.company)
        .join(Article, Article.source_id == Source.id)
        .where(Article.status == "done")
        .distinct()
        .order_by(Source.company)
    )
    companies = [r[0] for r in companies_result.all()]

    # Aggregate all topics from done articles
    topics_result = await db.execute(
        select(Article.topics).where(Article.status == "done").where(Article.topics != "[]")
    )
    topic_counter: dict[str, int] = {}
    for (topics_json,) in topics_result.all():
        try:
            for t in json.loads(topics_json):
                topic_counter[t] = topic_counter.get(t, 0) + 1
        except Exception:
            pass
    top_topics = sorted(topic_counter, key=lambda x: -topic_counter[x])[:30]

    return ArticleListResponse(
        items=items,
        total=total,
        page=page,
        pages=max(1, math.ceil(total / limit)),
        companies=companies,
        topics=top_topics,
    )


@router.get("/articles/{article_id}", response_model=ArticleDetail)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException

    result = await db.execute(
        select(Article, Source.company, Source.name)
        .join(Source, Article.source_id == Source.id)
        .where(Article.id == article_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Article not found")

    article, company_name, source_name = row
    return ArticleDetail(
        id=article.id,
        source_id=article.source_id,
        url=article.url,
        title=article.title,
        author=article.author,
        published_at=article.published_at,
        crawled_at=article.crawled_at,
        summary=article.summary,
        summarized_at=article.summarized_at,
        topics=article.topics,
        is_relevant=article.is_relevant,
        status=article.status,
        word_count=article.word_count,
        company=company_name,
        source_name=source_name,
        raw_content=article.raw_content,
        summary_model=article.summary_model,
        relevance_score=article.relevance_score,
        error_message=article.error_message,
    )
