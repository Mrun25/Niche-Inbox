"""
summarizer.py — Uses Mistral API to summarize articles into an HTML newsletter.
"""

import os
import json
import requests
from datetime import date

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


def _summarize_topic(topic: str, articles: list) -> str:
    """Ask Mistral to produce a short HTML summary for one topic's articles."""
    if not articles:
        return "<p><em>No articles available for this topic today.</em></p>"

    article_text = "\n\n".join(
        f"Title: {a['title']}\nSource: {a['source']}\nSummary: {a['description'] or 'N/A'}\nURL: {a['url']}"
        for a in articles
    )

    prompt = f"""You are a witty, sharp newspaper editor writing a daily digest column.

Given the following {topic} news articles, write a concise digest.
- Cover 3 to 5 of the most important articles provided.
- For EACH article you cover, render it exactly like this:
  <p><strong>Article Headline Here</strong><br>
  A single concise paragraph (3–4 sentences) summarising what happened, why it matters, and what comes next. <a href="URL">Read more</a></p>
- Do NOT merge multiple articles into a single block. Each article must have its own bold headline and paragraph.
- Return ONLY the HTML content. No markdown formatting, no code fences, no <html> or <body> tags. Use ONLY <p>, <strong>, <br>, and <a> tags.

Articles:
{article_text}
"""

    headers = {
        "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1500,
    }

    try:
        resp = requests.post(MISTRAL_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[summarizer] Mistral error for {topic}: {e}")
        # Fallback: plain list of article links
        fallback = "".join(
            f'<p><a href="{a["url"]}">{a["title"]}</a> — {a["source"]}</p>'
            for a in articles
        )
        return fallback


def build_newsletter(email: str, topics_articles: dict) -> str:
    """Build the full HTML newsletter for a user."""
    today = date.today().strftime("%A, %B %d, %Y")

    sections_html = ""
    for topic, articles in topics_articles.items():
        summary_html = _summarize_topic(topic, articles)
        sections_html += f"""
        <div class="section">
          <div class="section-label">{topic}</div>
          <div class="section-body">{summary_html}</div>
        </div>
        <div class="divider"></div>
        """

    newsletter = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=EB+Garamond:ital,wght@0,400;0,600;1,400&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap');

    body {{
      margin: 0;
      padding: 0;
      background: #f2ede3;
      font-family: 'EB Garamond', Georgia, serif;
      color: #1a1208;
    }}
    .wrapper {{
      max-width: 640px;
      margin: 30px auto;
      background: #fffdf7;
      border: 1px solid #c8b89a;
    }}
    /* ── Masthead ── */
    .masthead {{
      padding: 28px 48px 18px;
      border-bottom: 4px double #1a1208;
      text-align: center;
      background: #fffdf7;
    }}
    h1.paper-name {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 42px;
      font-weight: 900;
      letter-spacing: 4px;
      text-transform: uppercase;
      margin: 0 0 4px;
    }}
    .tagline {{
      font-family: 'EB Garamond', Georgia, serif;
      font-style: italic;
      font-size: 14px;
      color: #5c4a2a;
      letter-spacing: 1px;
      margin: 0 0 8px;
    }}
    .meta-bar {{
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #7a6a4a;
      border-top: 1px solid #c8b89a;
      padding-top: 8px;
      margin-top: 8px;
    }}
    /* ── Content ── */
    .content {{
      padding: 0 48px 32px;
    }}
    .intro {{
      font-size: 15px;
      font-style: italic;
      color: #5c4a2a;
      text-align: center;
      padding: 18px 0 0;
      margin-bottom: 4px;
    }}
    .divider {{
      border: none;
      border-top: 1px solid #c8b89a;
      margin: 0;
    }}
    .section {{
      padding: 22px 0 8px;
    }}
    .section-label {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 18px;
      font-weight: 900;
      letter-spacing: 4px;
      text-transform: uppercase;
      color: #7a6a4a;
      border-bottom: 4px solid #1a1208;
      padding-bottom: 6px;
      margin-bottom: 14px;
    }}
    .section-body p {{
      font-size: 16px;
      line-height: 1.75;
      margin: 0 0 16px;
    }}
    .section-body a {{
      color: #1a1208;
      text-decoration: underline;
      text-underline-offset: 3px;
    }}
    /* ── Footer ── */
    .footer {{
      background: #1a1208;
      color: #c8b89a;
      text-align: center;
      padding: 18px 40px;
      font-size: 11px;
      letter-spacing: 2px;
      text-transform: uppercase;
    }}
    .footer a {{
      color: #c8b89a;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="masthead">
      <h1 class="paper-name">Niche Inbox</h1>
      <div class="tagline">All the news that's fit to send</div>
      <div class="meta-bar">
        <span>{today}</span>
        <span>Personalised Edition</span>
        <span>{email}</span>
      </div>
    </div>
    <div class="content">
      <p class="intro">Good day, dear reader. Here is your curated briefing for today.</p>
      <div class="divider"></div>
      {sections_html}
    </div>
    <div class="footer">
      Niche Inbox &nbsp;·&nbsp; Built by Mrunmayee &nbsp;·&nbsp; {today}
    </div>
  </div>
</body>
</html>
"""
    return newsletter
