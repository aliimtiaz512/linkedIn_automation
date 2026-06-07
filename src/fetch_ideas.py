import requests
import feedparser
from datetime import datetime, timedelta

RSS_FEEDS = [
    ("https://hn.algolia.com/api/v1/search", "hackernews"),
    ("https://venturebeat.com/category/ai/feed/", "rss"),
    ("https://www.artificialintelligence-news.com/feed/", "rss"),
    ("https://www.technologyreview.com/feed/", "rss"),
    ("https://feeds.feedburner.com/TechCrunch/", "rss"),
]

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "ml", "llm", "gpt",
    "neural", "deep learning", "automation", "data science", "model",
    "transformer", "nlp", "computer vision", "generative", "agent", "rag"
]


def _fetch_hackernews():
    """Fetch AI/ML stories from HackerNews via Algolia API."""
    since = int((datetime.now() - timedelta(hours=24)).timestamp())
    url = "https://hn.algolia.com/api/v1/search"
    params = {
        "tags": "story",
        "query": "AI machine learning LLM",
        "hitsPerPage": 15,
        "numericFilters": f"created_at_i>{since}",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        hits = resp.json().get("hits", [])
        ideas = []
        for hit in hits:
            title = hit.get("title", "")
            if title and any(kw in title.lower() for kw in AI_KEYWORDS):
                ideas.append({
                    "title": title,
                    "summary": "",
                    "source": "HackerNews",
                    "url": hit.get("url", ""),
                })
        return ideas
    except Exception as e:
        print(f"HackerNews fetch error: {e}")
        return []


def _fetch_rss(feed_url):
    """Fetch AI-relevant items from an RSS feed."""
    try:
        feed = feedparser.parse(feed_url)
        ideas = []
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            combined = (title + " " + summary).lower()
            if any(kw in combined for kw in AI_KEYWORDS):
                ideas.append({
                    "title": title,
                    "summary": summary[:300].strip() if summary else "",
                    "source": feed_url,
                    "url": entry.get("link", ""),
                })
        return ideas
    except Exception as e:
        print(f"RSS fetch error ({feed_url}): {e}")
        return []


def fetch_ideas(num_ideas=5):
    """Fetch recent AI/tech ideas from HackerNews and RSS feeds."""
    all_ideas = []

    all_ideas.extend(_fetch_hackernews())

    for url, feed_type in RSS_FEEDS[1:]:
        all_ideas.extend(_fetch_rss(url))

    # Deduplicate by title
    seen = set()
    unique = []
    for idea in all_ideas:
        key = idea["title"].lower()[:60]
        if key not in seen and idea["title"]:
            seen.add(key)
            unique.append(idea)

    result = unique[:num_ideas]
    print(f"Fetched {len(result)} unique AI/tech ideas")
    return result
