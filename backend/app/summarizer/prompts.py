SYSTEM_PROMPT = """\
You are a technical writer specializing in distributed systems and infrastructure engineering.
Your task is to read engineering blog posts and produce concise, accurate technical summaries
for software engineers who work on large-scale systems.

Focus on:
- The technical problem being solved
- The architectural approach or algorithm used
- Key engineering trade-offs and decisions
- Measurable results (latency, throughput, scale figures)
- Novel techniques or lessons learned

Be precise and use correct technical terminology. Avoid marketing language.
If the article is not primarily about distributed systems, infrastructure, or databases,
still summarize it but note the primary topic.
"""

USER_PROMPT_TEMPLATE = """\
Article title: {title}
Company: {company}
URL: {url}
{truncation_note}
Full article text:
{content}

---
Produce a technical summary with the following structure:

**Problem**: One sentence on the technical challenge addressed.
**Approach**: 2-3 sentences on the solution architecture, algorithms, or design decisions.
**Key Details**:
- [bullet 1]
- [bullet 2]
- [bullet 3]
(3-5 bullets of notable technical specifics)
**Results**: Any quantitative outcomes (latency, throughput, scale, uptime). Write "Not mentioned" if absent.
**Topics**: A comma-separated list of technical topic tags (e.g., consensus, replication, kafka, kubernetes).

Keep the total summary under 350 words.
"""


def build_user_prompt(
    title: str,
    company: str,
    url: str,
    content: str,
    truncated: bool = False,
    original_word_count: int | None = None,
) -> str:
    truncation_note = ""
    if truncated:
        note = f"[NOTE: Article was truncated from ~{original_word_count} words to fit context limits. "
        note += "First 60% and last 20% of the article were retained.]\n"
        truncation_note = note

    return USER_PROMPT_TEMPLATE.format(
        title=title,
        company=company,
        url=url,
        content=content,
        truncation_note=truncation_note,
    )
