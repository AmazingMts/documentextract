#!/usr/bin/env python3
"""
Export summarized articles from SQLite to frontend/public/articles.json
Run from the backend/ directory:
    python ../scripts/export_articles.py
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend/app to path
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from app.database import init_db, AsyncSessionLocal
from app.models import Article, Source
from sqlalchemy import select


async def export():
    await init_db()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Article, Source.company, Source.name)
            .join(Source, Article.source_id == Source.id)
            .where(Article.status == "done")
            .order_by(Article.published_at.desc().nullslast())
        )
        rows = result.all()

    articles = []
    for article, company, source_name in rows:
        articles.append({
            "id": article.id,
            "url": article.url,
            "title": article.title,
            "author": article.author,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "crawled_at": article.crawled_at.isoformat() if article.crawled_at else None,
            "summary": article.summary,
            "topics": article.topics,  # already a JSON string
            "word_count": article.word_count,
            "company": company,
            "source_name": source_name,
        })

    out_path = BACKEND_DIR.parent / "frontend" / "public" / "articles.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(articles)} articles → {out_path}")
    return len(articles)


if __name__ == "__main__":
    count = asyncio.run(export())
    sys.exit(0 if count >= 0 else 1)
