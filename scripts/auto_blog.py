"""
Trytimeback Auto Blog Publisher
- Generates SEO blog posts using Claude API
- Publishes to Blogger automatically
- Runs daily via GitHub Actions
"""

import os
import json
import random
import requests

# ─── Config from environment (remove all whitespace/newlines) ───
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"].replace("\n", "").replace("\r", "").strip()
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"].replace("\n", "").replace("\r", "").strip()
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"].replace("\n", "").replace("\r", "").strip()
GOOGLE_REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"].replace("\n", "").replace("\r", "").strip()
BLOGGER_BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "3305767414653621134").replace("\n", "").replace("\r", "").strip()

# ─── Blog topics related to Trytimeback ───
TOPICS = [
    "How to Summarize a YouTube Lecture in 60 Seconds with AI",
    "5 Best AI Tools for Students to Save Study Time in 2026",
    "Why Every Student Needs an AI YouTube Summarizer",
    "How to Turn a 2-Hour Lecture into 5-Minute Notes",
    "AI-Powered Study Hacks: Summarize Any YouTube Video Instantly",
    "The Future of Online Learning: AI Video Summarizers",
    "How to Extract Key Points from YouTube Lectures Automatically",
    "Save 10 Hours a Week: AI YouTube Summary Tools Compared",
    "From YouTube to PDF: How AI Creates Perfect Study Notes",
    "Why Manual Note-Taking is Dead: AI Lecture Summarizers",
    "How to Use AI to Ace Your Online Courses",
    "Top 5 Productivity Tools for University Students in 2026",
    "AI Study Assistant: Turn YouTube Videos into Flashcards",
    "How International Students Use AI to Overcome Language Barriers",
    "The Complete Guide to AI-Powered Video Learning",
    "How to Prepare for Exams Using AI Video Summaries",
    "YouTube Learning Revolution: AI Tools That Change Everything",
    "Best Chrome Extensions for YouTube Learning in 2026",
    "How Professionals Use AI to Learn New Skills from YouTube",
    "AI Note-Taking: Why Smart Students Don't Watch Full Lectures",
    "How to Build a Personal Knowledge Base from YouTube Content",
    "The Science Behind AI Video Summarization Technology",
    "Remote Learning Tips: AI Tools Every Student Should Know",
    "How to Learn Programming from YouTube 10x Faster with AI",
    "AI-Powered PDF Notes: The Ultimate Study Companion",
    "How Medical Students Use AI to Summarize Lecture Videos",
    "YouTube Study Playlist? Let AI Do the Heavy Lifting",
    "The Best Free AI Tools for Online Learners in 2026",
    "How to Summarize TED Talks and Keynotes with AI",
    "From Passive Watching to Active Learning: AI Video Tools",
]


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


def generate_blog_post(topic):
    """Generate a blog post using Claude API."""
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": f"""Write an SEO-optimized blog post about: "{topic}"

Requirements:
- Write in English
- 800-1200 words
- Include a compelling title (different from the topic if needed)
- Use H2 and H3 subheadings with <h2> and <h3> HTML tags
- Write in a friendly, informative tone
- Include practical tips and examples
- Naturally mention "Trytimeback" (trytimeback.com) as a recommended AI YouTube summarizer tool (mention it 2-3 times, not too pushy)
- End with a call-to-action to try Trytimeback
- Return ONLY valid HTML for the body (no <html>, <head>, <body> tags)
- Start with the title as <h1> tag

Format:
<h1>Title Here</h1>
<p>Introduction...</p>
<h2>Section...</h2>
<p>Content...</p>
...
<p><strong>Ready to save hours of study time?</strong> Try <a href="https://trytimeback.com">Trytimeback</a> — your AI-powered YouTube lecture summarizer.</p>""",
                }
            ],
        },
    )
    resp.raise_for_status()
    content = resp.json()["content"][0]["text"]
    return content


def extract_title(html_content):
    """Extract title from <h1> tag."""
    import re
    match = re.search(r"<h1>(.*?)</h1>", html_content)
    if match:
        return match.group(1)
    return "AI YouTube Summarizer Tips"


def publish_to_blogger(title, content, access_token):
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
            "labels": ["AI", "YouTube", "Study Tips", "Trytimeback", "Productivity"],
        },
    )
    resp.raise_for_status()
    return resp.json()


def main():
    print("=== Trytimeback Auto Blog Publisher ===")

    # 1) Pick a random topic
    topic = random.choice(TOPICS)
    print(f"[1/3] Topic: {topic}")

    # 2) Generate blog post with Claude
    print("[2/3] Generating blog post with Claude...")
    html_content = generate_blog_post(topic)
    title = extract_title(html_content)
    print(f"       Title: {title}")
    print(f"       Length: {len(html_content)} chars")

    # 3) Publish to Blogger
    print("[3/3] Publishing to Blogger...")
    access_token = get_google_access_token()
    result = publish_to_blogger(title, html_content, access_token)
    print(f"       Published! URL: {result.get('url', 'N/A')}")
    print("=== Done! ===")


if __name__ == "__main__":
    main()
