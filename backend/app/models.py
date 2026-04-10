from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    feed_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    feed_type: Mapped[str] = mapped_column(String(20), default="rss")  # "rss" | "scrape"
    topic_hints: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_crawled: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    articles: Mapped[list["Article"]] = relationship("Article", back_populates="source")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summarized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topics: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=False)
    # pending | summarizing | done | failed | skipped
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped["Source"] = relationship("Source", back_populates="articles")


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    articles_found: Mapped[int] = mapped_column(Integer, default=0)
    articles_new: Mapped[int] = mapped_column(Integer, default=0)
    articles_summarized: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running | completed | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
