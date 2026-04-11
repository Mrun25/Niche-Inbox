"""
news_fetcher.py
---------------
Fetches top articles for each selected topic using NewsAPI.
Requires NEWSAPI_KEY in your .env file.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSAPI_BASE = "https://newsapi.org/v2/top-headlines"

TOPIC_TO_CATEGORY = {
    "Headlines": "general",
    "Technology": "technology",
    "Politics": "politics",
    "Sports": "sports",
    "World Stocks": "business",
    "Science": "science",
    "Entertainment": "entertainment",
}

JOB_SEARCH_KEYWORDS = ["job openings", "hiring", "recruitment 2025"]


def fetch_articles_for_topic(topic: str, max_articles: int = 5) -> list[dict]:
    """
    Fetch top articles for a given topic.
    Returns a list of dicts with keys: title, description, url, source.
    """
    if topic == "Job Openings":
        return _fetch_job_openings(max_articles)

    category = TOPIC_TO_CATEGORY.get(topic, "general")

    params = {
        "category": category,
        "country": "us",   # required by the free-tier NewsAPI plan
        "language": "en",
        "pageSize": max_articles,
        "apiKey": NEWSAPI_KEY,
    }

    try:
        response = requests.get(NEWSAPI_BASE, params=params, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [
            {
                "title": a.get("title", "No title"),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", "Unknown"),
            }
            for a in articles
            if a.get("title")
        ]
    except requests.RequestException as e:
        print(f"  [NewsAPI] Error fetching {topic}: {e}")
        return []


def _fetch_job_openings(max_articles: int) -> list[dict]:
    """Use NewsAPI everything endpoint for job-related news."""
    params = {
        "q": "job openings hiring",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_articles,
        "apiKey": NEWSAPI_KEY,
    }
    try:
        response = requests.get(
            "https://newsapi.org/v2/everything", params=params, timeout=10
        )
        response.raise_for_status()
        articles = response.json().get("articles", [])
        return [
            {
                "title": a.get("title", "No title"),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", "Unknown"),
            }
            for a in articles
            if a.get("title")
        ]
    except requests.RequestException as e:
        print(f"  [NewsAPI] Error fetching Job Openings: {e}")
        return []


def fetch_all_topics(topics: list[str]) -> dict[str, list[dict]]:
    """Fetch articles for all topics. Returns {topic: [articles]}."""
    result = {}
    for topic in topics:
        print(f"  Fetching: {topic}...")
        result[topic] = fetch_articles_for_topic(topic)
    return result
