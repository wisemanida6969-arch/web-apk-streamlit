"""
Trytimeback Auto Blog Publisher v2
- Fetches trending topics from Google News RSS (Korean)
- Categories: Korean trending news, TV restaurants, entertainment, AI/study
- Generates SEO blog posts with Claude API
- Publishes to Blogger automatically
- Runs twice daily via GitHub Actions (9 AM & 6 PM KST)
"""

import os
import random
import re
import xml.etree.ElementTree as ET
import requests

# ─── Config from environment ───
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"].replace("\n", "").replace("\r", "").strip()
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"].replace("\n", "").replace("\r", "").strip()
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"].replace("\n", "").replace("\r", "").strip()
GOOGLE_REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"].replace("\n", "").replace("\r", "").strip()
BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "3305767414653621134").replace("\n", "").replace("\r", "").strip()

# ─── Content Categories ───
CATEGORIES = {
    "korean_trending": {
        "name": "한국 트렌딩 뉴스",
        "rss": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
        "language": "ko",
        "labels": ["뉴스", "트렌드", "이슈"],
    },
    "korean_entertainment": {
        "name": "한국 연예/K-POP",
        "rss": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=ko&gl=KR&ceid=KR:ko",
        "language": "ko",
        "labels": ["연예", "K-POP", "드라마"],
    },
    "tv_food": {
        "name": "TV 맛집/먹방",
        "rss": "https://news.google.com/rss/search?q=맛집+OR+생활의달인+OR+백종원+OR+먹방&hl=ko&gl=KR&ceid=KR:ko",
        "language": "ko",
        "labels": ["맛집", "먹방", "TV", "생활정보"],
    },
    "korean_lifestyle": {
        "name": "생활 이슈/화제",
        "rss": "https://news.google.com/rss/search?q=화제+OR+이슈+OR+꿀팁&hl=ko&gl=KR&ceid=KR:ko",
        "language": "ko",
        "labels": ["이슈", "화제", "꿀팁", "생활"],
    },
    "ai_study_en": {
        "name": "AI Study Tools (English)",
        "rss": None,  # Uses predefined topics
        "language": "en",
        "labels": ["AI", "YouTube", "Study Tips", "Trytimeback", "Productivity"],
        "topics": [
            "How to Summarize a YouTube Lecture in 60 Seconds with AI",
            "5 Best AI Tools for Students to Save Study Time in 2026",
            "Why Every Student Needs an AI YouTube Summarizer",
            "How to Turn a 2-Hour Lecture into 5-Minute Notes",
            "AI-Powered Study Hacks: Summarize Any YouTube Video Instantly",
            "The Future of Online Learning: AI Video Summarizers",
            "How AI Changes the Way Students Learn from YouTube",
            "Save 10 Hours a Week: AI YouTube Summary Tools Compared",
            "From YouTube to PDF: How AI Creates Perfect Study Notes",
            "Why Manual Note-Taking is Dead: AI Lecture Summarizers",
        ],
    },
}


def fetch_trending_topic(rss_url):
    """Fetch top news item from Google News RSS."""
    resp = requests.get(
        rss_url,
        headers={"User-Agent": "Mozilla/5.0"},
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
    title = item.findtext("title", "").strip()
    description = item.findtext("description", "").strip()
    # Strip HTML tags from description
    description = re.sub(r"<[^>]+>", "", description)
    return {"title": title, "description": description[:500]}


def get_google_access_token():
    """Exchange refresh token for a new access token."""
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": GOOGLE_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def generate_korean_post(topic_info, category_name):
    """Generate Korean blog post about trending topic."""
    topic = topic_info["title"]
    context = topic_info["description"]

    prompt = f"""다음 한국 뉴스/이슈를 바탕으로 SEO에 최적화된 한국어 블로그 글을 작성해주세요.

주제: {topic}
배경 정보: {context}
카테고리: {category_name}

요구사항:
- 800-1200자 분량의 한국어 블로그 글
- 흥미롭고 클릭하고 싶은 제목 (원래 주제보다 더 매력적으로)
- <h2>, <h3> 부제목 사용
- 친근하고 정보성 있는 말투
- 구체적인 내용과 예시 포함
- SEO를 위한 관련 키워드 자연스럽게 포함
- 독자들이 더 알고 싶어할만한 실용적 정보 제공
- 결론 부분에 요약과 함께 "더 많은 꿀팁과 요약 정보가 필요하다면 <a href='https://trytimeback.com'>Trytimeback</a>에서 AI가 자동으로 유튜브 영상을 요약해드립니다" 같은 자연스러운 마무리
- HTML로 반환 (body 내용만, <html>, <head>, <body> 태그 제외)
- <h1> 태그로 제목 시작

형식:
<h1>매력적인 제목</h1>
<p>도입부...</p>
<h2>본문 섹션...</h2>
<p>내용...</p>
..."""

    return call_claude(prompt)


def generate_english_post(topic):
    """Generate English SEO blog post."""
    prompt = f"""Write an SEO-optimized blog post about: "{topic}"

Requirements:
- Write in English
- 800-1200 words
- Include a compelling title (different from the topic if needed)
- Use H2 and H3 subheadings with <h2> and <h3> HTML tags
- Write in a friendly, informative tone
- Include practical tips and examples
- Naturally mention "Trytimeback" (trytimeback.com) as a recommended AI YouTube summarizer tool (2-3 times, not pushy)
- End with a call-to-action to try Trytimeback
- Return ONLY valid HTML for the body (no <html>, <head>, <body> tags)
- Start with the title as <h1> tag

Format:
<h1>Title Here</h1>
<p>Introduction...</p>
<h2>Section...</h2>
<p>Content...</p>
...
<p><strong>Ready to save hours of study time?</strong> Try <a href="https://trytimeback.com">Trytimeback</a> — your AI-powered YouTube lecture summarizer.</p>"""

    return call_claude(prompt)


def call_claude(prompt):
    """Call Claude API and return the response text."""
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 2500,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def extract_title(html_content):
    """Extract title from <h1> tag."""
    match = re.search(r"<h1>(.*?)</h1>", html_content, re.DOTALL)
    if match:
        # Strip any nested HTML
        title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        return title
    return "오늘의 트렌드"


def publish_to_blogger(title, content, labels, access_token):
    """Publish a post to Blogger."""
    resp = requests.post(
        f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "kind": "blogger#post",
            "blog": {"id": BLOGGER_BLOG_ID},
            "title": title,
            "content": content,
            "labels": labels,
        },
    )
    resp.raise_for_status()
    return resp.json()


def main():
    print("=== Trytimeback Auto Blog Publisher v2 ===")

    # 1) Pick a random category (weighted toward Korean content for local SEO)
    # Korean categories get higher weight
    category_weights = [
        ("korean_trending", 3),
        ("korean_entertainment", 2),
        ("tv_food", 3),
        ("korean_lifestyle", 2),
        ("ai_study_en", 2),
    ]
    categories_flat = []
    for cat, weight in category_weights:
        categories_flat.extend([cat] * weight)
    category_key = random.choice(categories_flat)
    category = CATEGORIES[category_key]
    print(f"[1/4] Category: {category['name']}")

    # 2) Fetch topic or pick from predefined list
    if category["rss"]:
        print(f"[2/4] Fetching trending topic from Google News RSS...")
        topic_info = fetch_trending_topic(category["rss"])
        if not topic_info:
            print("       No topics found, falling back to ai_study_en")
            category = CATEGORIES["ai_study_en"]
            category_key = "ai_study_en"
            topic = random.choice(category["topics"])
            topic_info = None
        else:
            print(f"       Topic: {topic_info['title']}")
    else:
        topic = random.choice(category["topics"])
        print(f"[2/4] Topic: {topic}")
        topic_info = None

    # 3) Generate content
    print("[3/4] Generating blog post with Claude...")
    if category["language"] == "ko" and topic_info:
        html_content = generate_korean_post(topic_info, category["name"])
    else:
        html_content = generate_english_post(topic)

    title = extract_title(html_content)
    print(f"       Title: {title}")
    print(f"       Length: {len(html_content)} chars")

    # 4) Publish to Blogger
    print("[4/4] Publishing to Blogger...")
    access_token = get_google_access_token()
    result = publish_to_blogger(title, html_content, category["labels"], access_token)
    print(f"       Published! URL: {result.get('url', 'N/A')}")
    print("=== Done! ===")


if __name__ == "__main__":
    main()
