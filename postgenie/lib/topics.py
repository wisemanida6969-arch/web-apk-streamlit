"""Topic fetching via Google News RSS."""
import random
import re
import xml.etree.ElementTree as ET
import requests


CATEGORY_FEEDS = {
    # English
    "en_trending": {
        "name": "Trending News",
        "rss": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "language": "en",
    },
    "en_tech": {
        "name": "Technology",
        "rss": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
        "language": "en",
    },
    "en_business": {
        "name": "Business",
        "rss": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
        "language": "en",
    },
    "en_entertainment": {
        "name": "Entertainment",
        "rss": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en",
        "language": "en",
    },
    "en_health": {
        "name": "Health",
        "rss": "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=en-US&gl=US&ceid=US:en",
        "language": "en",
    },
    # Korean
    "ko_trending": {
        "name": "한국 트렌딩",
        "rss": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
        "language": "ko",
    },
    "ko_food": {
        "name": "TV 맛집/먹방",
        "rss": "https://news.google.com/rss/search?q=맛집+OR+백종원+OR+먹방&hl=ko&gl=KR&ceid=KR:ko",
        "language": "ko",
    },
    "ko_entertainment": {
        "name": "K-POP/연예",
        "rss": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=ko&gl=KR&ceid=KR:ko",
        "language": "ko",
    },
    "ko_lifestyle": {
        "name": "생활/꿀팁",
        "rss": "https://news.google.com/rss/search?q=꿀팁+OR+화제+OR+이슈&hl=ko&gl=KR&ceid=KR:ko",
        "language": "ko",
    },
}


def fetch_trending_topic(category: str) -> dict | None:
    """Fetch a random top trending topic from the category's RSS feed."""
    feed_info = CATEGORY_FEEDS.get(category)
    if not feed_info:
        return None

    try:
        resp = requests.get(
            feed_info["rss"],
            headers={"User-Agent": "Mozilla/5.0 (PostGenie Bot)"},
            timeout=20,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        if not items:
            return None

        # Pick from top 10 to avoid repetition
        top_items = items[:10]
        item = random.choice(top_items)
        title = (item.findtext("title") or "").strip()
        description = re.sub(r"<[^>]+>", "", (item.findtext("description") or ""))[:500]

        return {
            "title": title,
            "description": description,
            "category": feed_info["name"],
            "language": feed_info["language"],
        }
    except Exception as e:
        print(f"[Topics] Fetch error for {category}: {e}")
        return None


def get_category_info(category_key: str) -> dict:
    return CATEGORY_FEEDS.get(category_key, {})


def list_categories_by_language(language: str) -> list:
    """List category keys for a given language."""
    if language == "auto":
        return list(CATEGORY_FEEDS.keys())
    return [k for k, v in CATEGORY_FEEDS.items() if v["language"] == language]
