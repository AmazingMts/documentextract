"""
Alibaba Cloud Bailian (百炼) LLM wrapper via OpenAI-compatible API.
Singapore endpoint: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
"""
import asyncio
import structlog
from openai import AsyncOpenAI, RateLimitError, APIStatusError, APIConnectionError

from app.config import settings
from app.summarizer.prompts import SYSTEM_PROMPT, build_user_prompt

logger = structlog.get_logger()

# qwen-plus context: 128k tokens ≈ ~500k chars; keep a safe margin
MAX_CONTENT_CHARS = 300_000

# Semaphore to cap concurrent LLM calls
_semaphore = asyncio.Semaphore(settings.max_concurrent_summaries)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


def _truncate_content(content: str) -> tuple[str, bool]:
    """
    If content exceeds MAX_CONTENT_CHARS, retain first 60% + last 20%.
    Returns (truncated_content, was_truncated).
    """
    if len(content) <= MAX_CONTENT_CHARS:
        return content, False

    first_part = int(MAX_CONTENT_CHARS * 0.6)
    last_part = int(MAX_CONTENT_CHARS * 0.2)
    truncated = (
        content[:first_part]
        + "\n\n[... content truncated ...]\n\n"
        + content[-last_part:]
    )
    return truncated, True


async def summarize_article(
    title: str,
    company: str,
    url: str,
    content: str,
    word_count: int | None = None,
) -> str:
    """
    Call Bailian (Qwen) to summarize an article. Returns the summary text.
    Raises on unrecoverable errors.
    """
    truncated_content, was_truncated = _truncate_content(content)

    user_message = build_user_prompt(
        title=title,
        company=company,
        url=url,
        content=truncated_content,
        truncated=was_truncated,
        original_word_count=word_count,
    )

    async with _semaphore:
        for attempt in range(5):
            try:
                client = get_client()
                response = await client.chat.completions.create(
                    model=settings.summarize_model,
                    max_tokens=1024,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                )
                return response.choices[0].message.content

            except RateLimitError as e:
                retry_after = int(
                    e.response.headers.get("retry-after", 2 ** attempt * 5)
                    if hasattr(e, "response") and e.response is not None
                    else 2 ** attempt * 5
                )
                logger.warning("rate_limit_hit", attempt=attempt, wait=retry_after)
                await asyncio.sleep(retry_after)

            except APIStatusError as e:
                if e.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning("api_server_error", status=e.status_code, attempt=attempt, wait=wait)
                    await asyncio.sleep(wait)
                else:
                    logger.error("api_client_error", status=e.status_code, message=str(e))
                    raise

            except APIConnectionError as e:
                wait = 2 ** attempt
                logger.warning("api_connection_error", attempt=attempt, wait=wait, error=str(e))
                await asyncio.sleep(wait)

        raise RuntimeError(f"Max retries exceeded for article: {url}")
