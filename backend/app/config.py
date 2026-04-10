from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    dashscope_api_key: str = ""
    llm_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    database_url: str = "sqlite+aiosqlite:///./data/articles.db"
    crawl_schedule_hour: int = 6
    crawl_schedule_minute: int = 0
    summarize_model: str = "qwen-plus"
    max_concurrent_summaries: int = 3
    enable_relevance_classification: bool = False
    admin_api_key: str = "change-me"
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
