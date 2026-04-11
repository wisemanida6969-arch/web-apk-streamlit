"""Claude API wrapper for content generation."""
import re
import requests

from lib.config import ANTHROPIC_API_KEY, CLAUDE_MODEL


TONE_DESCRIPTIONS = {
    "friendly": "friendly and approachable, like chatting with a friend",
    "professional": "professional and authoritative, suitable for business readers",
    "casual": "casual and conversational, fun to read",
    "educational": "informative and educational, clearly explaining concepts",
    "persuasive": "persuasive and engaging, encouraging action",
}

LANGUAGE_INSTRUCTIONS = {
    "en": "Write in English.",
    "ko": "한국어로 작성해주세요. 자연스러운 한국어 표현을 사용하세요.",
    "ja": "日本語で書いてください。自然な日本語表現を使用してください。",
    "es": "Escribe en español. Usa expresiones naturales en español.",
    "auto": "Match the language of the topic.",
}


def generate_blog_post(
    topic: str,
    category: str = "",
    language: str = "en",
    tone: str = "friendly",
    word_count: int = 1000,
    custom_context: str = "",
) -> dict:
    """Generate a blog post using Claude. Returns {title, content, html}."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])
    tone_desc = TONE_DESCRIPTIONS.get(tone, TONE_DESCRIPTIONS["friendly"])

    prompt = f"""Write an SEO-optimized blog post about: "{topic}"

{lang_instruction}

Requirements:
- {word_count} words target length
- Tone: {tone_desc}
- Category: {category or "general"}
- Include a compelling title (can differ from the topic to be more clickable)
- Use <h2> and <h3> HTML subheadings
- Include practical tips, examples, and actionable advice
- Naturally include SEO keywords related to the topic
- Return ONLY valid HTML for the body (no <html>, <head>, <body> wrapper tags)
- Start with <h1>Title</h1>
- End with a call-to-action paragraph

{"Additional context: " + custom_context if custom_context else ""}

Format:
<h1>Your compelling title</h1>
<p>Engaging introduction...</p>
<h2>Main section</h2>
<p>Content...</p>
..."""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": max(2000, word_count * 3),
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    result = resp.json()

    html_content = result["content"][0]["text"]
    title = extract_title(html_content)
    token_count = result.get("usage", {}).get("output_tokens", 0)

    return {
        "title": title,
        "content": html_content,
        "token_count": token_count,
    }


def extract_title(html: str) -> str:
    """Pull title from first <h1> tag."""
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()
    return "Untitled Post"
