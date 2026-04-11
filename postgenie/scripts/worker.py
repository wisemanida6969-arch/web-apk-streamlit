"""
PostGenie Cron Worker
Runs hourly (or more frequently) to process due schedules.
For each schedule that's due, it:
1. Picks a topic from the configured categories
2. Generates a blog post via Claude
3. Publishes to the connected blog
4. Updates DB with result

Run via GitHub Actions or Render Cron Job.
"""
import os
import sys
import random
from datetime import datetime, timedelta

# Allow imports from parent directory when run from scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.supabase_client import db
from lib.topics import fetch_trending_topic, CATEGORY_FEEDS
from lib.claude import generate_blog_post
from lib.publishers import publish_post


FREQUENCY_MAP = {
    "daily": timedelta(days=1),
    "twice_daily": timedelta(hours=12),
    "weekly": timedelta(days=7),
}


def calculate_next_run(frequency: str) -> str:
    """Return ISO timestamp for the next scheduled run."""
    delta = FREQUENCY_MAP.get(frequency, timedelta(days=1))
    next_run = datetime.utcnow() + delta
    return next_run.isoformat() + "Z"


def process_schedule(schedule: dict):
    """Process one due schedule: generate and publish a post."""
    schedule_id = schedule["id"]
    user_id = schedule["user_id"]
    blog_connection_id = schedule["blog_connection_id"]

    print(f"[{schedule_id}] Processing schedule: {schedule.get('name', 'unnamed')}")

    try:
        # 1) Get blog connection
        blogs = db.get_user_blogs(user_id)
        blog_connection = next(
            (b for b in blogs if b["id"] == blog_connection_id), None
        )
        if not blog_connection:
            raise Exception(f"Blog connection {blog_connection_id} not found")

        # 2) Pick a category
        categories = schedule.get("categories", [])
        if not categories:
            raise Exception("No categories configured")
        category_key = random.choice(categories)

        # 3) Fetch a trending topic (unless using custom topics)
        custom_topics = (schedule.get("custom_topics") or "").strip()
        if custom_topics:
            # Pick from user-defined topics
            topic_list = [t.strip() for t in custom_topics.split("\n") if t.strip()]
            topic = random.choice(topic_list) if topic_list else category_key
            topic_info = {"title": topic, "description": "", "category": category_key}
        else:
            topic_info = fetch_trending_topic(category_key)
            if not topic_info:
                raise Exception(f"No trending topics available for {category_key}")

        print(f"       Topic: {topic_info['title']}")

        # 4) Generate blog post with Claude
        language = schedule.get("language", "en")
        tone = schedule.get("tone", "friendly")
        word_count = schedule.get("word_count", 1000)

        post = generate_blog_post(
            topic=topic_info["title"],
            category=topic_info.get("category", ""),
            language=language,
            tone=tone,
            word_count=word_count,
            custom_context=topic_info.get("description", ""),
        )
        print(f"       Generated: {post['title']} ({post['token_count']} tokens)")

        # 5) Save post to DB (pending status)
        post_record = db.create_post(
            schedule_id=schedule_id,
            user_id=user_id,
            title=post["title"],
            content=post["content"],
            category=category_key,
            language=language,
            token_count=post["token_count"],
        )

        # 6) Publish to blog
        result = publish_post(
            blog_connection=blog_connection,
            title=post["title"],
            content=post["content"],
            labels=schedule.get("categories", []),
        )
        print(f"       Published: {result['blog_post_url']}")

        # 7) Update post status
        db.update_post_published(
            post_id=post_record["id"],
            blog_post_id=result["blog_post_id"],
            blog_post_url=result["blog_post_url"],
        )

        # 8) Track usage
        db.increment_usage(user_id, tokens=post["token_count"])

        # 9) Schedule next run
        next_run = calculate_next_run(schedule.get("frequency", "daily"))
        db.update_schedule_run(schedule_id, next_run)

        print(f"[{schedule_id}] ✅ Done. Next run: {next_run}")

    except Exception as e:
        print(f"[{schedule_id}] ❌ Failed: {e}")
        # Record failure
        try:
            if 'post_record' in locals():
                db.update_post_failed(post_record["id"], str(e))
        except Exception:
            pass


def main():
    print("=" * 60)
    print(f"PostGenie Worker — {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    try:
        due = db.get_due_schedules()
    except Exception as e:
        print(f"Failed to fetch due schedules: {e}")
        return

    if not due:
        print("No schedules due. Exiting.")
        return

    print(f"Found {len(due)} due schedules.")
    for schedule in due:
        try:
            process_schedule(schedule)
        except Exception as e:
            print(f"Uncaught error processing schedule: {e}")

    print("=" * 60)
    print("Worker done.")


if __name__ == "__main__":
    main()
