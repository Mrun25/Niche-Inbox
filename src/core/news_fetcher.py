"""
news_fetcher.py — Fetches live headlines from NewsAPI for given topics.
"""

import os
import requests
from datetime import date

NEWSAPI_BASE = "https://newsapi.org/v2/everything"
NEWSAPI_TOP  = "https://newsapi.org/v2/top-headlines"

TOPIC_QUERIES = {
    "Top Headlines": {
        "endpoint": NEWSAPI_TOP,
        "params": {"language": "en"},
    },
    "Business & Economy": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "business economy finance markets", "language": "en", "sortBy": "publishedAt"},
    },
    "Technology": {
        "endpoint": NEWSAPI_TOP,
        "params": {"category": "technology", "language": "en"},
    },
    "Science & Health": {
        "endpoint": NEWSAPI_TOP,
        "params": {"category": "science", "language": "en"},
    },
    "Politics & World Affairs": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "politics world affairs government international", "language": "en", "sortBy": "publishedAt"},
    },
    "Sports": {
        "endpoint": NEWSAPI_TOP,
        "params": {"category": "sports", "language": "en"},
    },
    "Entertainment & Culture": {
        "endpoint": NEWSAPI_TOP,
        "params": {"category": "entertainment", "language": "en"},
    },
    "Environment & Climate": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "environment climate change sustainability energy", "language": "en", "sortBy": "publishedAt"},
    },
    "Job Openings & Careers": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "jobs hiring employment careers recruitment", "language": "en", "sortBy": "publishedAt"},
    },
    "Crime & Justice": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "crime justice police court", "language": "en", "sortBy": "publishedAt"},
    },
    "Travel & Tourism": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "travel tourism airlines hospitality", "language": "en", "sortBy": "publishedAt"},
    },
    "Food & Lifestyle": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "food lifestyle dining diet", "language": "en", "sortBy": "publishedAt"},
    },
    "Education": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "education school university college", "language": "en", "sortBy": "publishedAt"},
    },
    "Defence & Military": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "defence military army navy airforce weapons", "language": "en", "sortBy": "publishedAt"},
    },
    "Law & Policy": {
        "endpoint": NEWSAPI_BASE,
        "params": {"q": "law policy legislation supreme court congress", "language": "en", "sortBy": "publishedAt"},
    },
}


def fetch_articles(topics: list, articles_per_topic: int = 7) -> dict:
    """
    Returns a dict: { topic_name: [ {title, description, url, source} ] }
    """
    api_key = os.getenv("NEWSAPI_KEY")
    results = {}

    for topic in topics:
        if topic not in TOPIC_QUERIES:
            continue
        config = TOPIC_QUERIES[topic]
        params = {**config["params"], "apiKey": api_key, "pageSize": articles_per_topic}
        try:
            resp = requests.get(config["endpoint"], params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            articles = [
                {
                    "title":       a.get("title", ""),
                    "description": a.get("description", ""),
                    "url":         a.get("url", ""),
                    "source":      a.get("source", {}).get("name", ""),
                }
                for a in data.get("articles", [])
                if a.get("title") and "[Removed]" not in a.get("title", "")
            ]
            results[topic] = articles[:articles_per_topic]
            print(f"[news_fetcher] {topic}: {len(results[topic])} articles fetched.")
        except Exception as e:
            print(f"[news_fetcher] Error fetching {topic}: {e}")
            results[topic] = []

    return results
