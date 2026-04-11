"""
summarizer.py
-------------
Uses the Mistral API to turn raw article data
into a polished, personalized newsletter body (HTML).
"""

import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def build_prompt(topics_articles: dict[str, list[dict]]) -> str:
    """Build the prompt string from fetched articles."""
    sections = []
    for topic, articles in topics_articles.items():
        if not articles:
            continue
        lines = [f"### {topic}"]
        for a in articles:
            lines.append(f"- **{a['title']}** ({a['source']})")
            if a.get("description"):
                lines.append(f"  {a['description']}")
            lines.append(f"  Read more: {a['url']}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def generate_newsletter(topics_articles: dict[str, list[dict]], user_name: str = "Reader") -> str:
    """
    Send articles to Mistral and get back a formatted HTML newsletter.
    Returns the HTML string.
    """
    raw_content = build_prompt(topics_articles)

    system_prompt = """You are a professional newsletter writer.
Your job is to take raw news article data and produce a clean, engaging, 
personalized daily digest in HTML format.

Rules:
- Use clean, minimal HTML with inline styles (email-safe)
- Start with a friendly greeting using the reader's name
- Group articles by topic with a clear heading per section
- Write 1-2 sentence summaries in your own words for each article
- Include the original article link as "Read more →"
- End with a short friendly sign-off
- Keep the tone warm, informative, and concise
- No external CSS, no JavaScript
- Do NOT wrap your output in markdown ```html tags, just output the raw HTML directly
"""

    user_message = f"""Here are today's news articles for {user_name}:

{raw_content}

Please write the HTML email digest now."""

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
    )

    return response.choices[0].message.content
