from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SourceOut(BaseModel):
    id: int
    name: str
    company: str
    url: str
    feed_url: Optional[str]
    feed_type: str
    active: bool
    last_crawled: Optional[datetime]

    model_config = {"from_attributes": True}


class ArticleOut(BaseModel):
    id: int
    source_id: int
    url: str
    title: str
    author: Optional[str]
    published_at: Optional[datetime]
    crawled_at: datetime
    summary: Optional[str]
    summarized_at: Optional[datetime]
    topics: str  # JSON string
    is_relevant: bool
    status: str
    word_count: Optional[int]
    # Joined from Source
    company: Optional[str] = None
    source_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ArticleDetail(ArticleOut):
    raw_content: Optional[str]
    summary_model: Optional[str]
    relevance_score: Optional[float]
    error_message: Optional[str]


class ArticleListResponse(BaseModel):
    items: List[ArticleOut]
    total: int
    page: int
    pages: int
    companies: List[str]
    topics: List[str]


class CrawlRunOut(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    articles_found: int
    articles_new: int
    articles_summarized: int
    status: str
    error: Optional[str]

    model_config = {"from_attributes": True}
