"""Posting schedules page."""
from datetime import datetime, timedelta

import streamlit as st

from lib.supabase_client import db
from lib.topics import CATEGORY_FEEDS


def render(user: dict):
    st.markdown("#### 📅 Posting Schedules")
    st.caption("Configure what to post and when. Each schedule generates one post per run.")

    blogs = db.get_user_blogs(user["id"]) if user.get("id") else []
    if not blogs:
        st.warning("Connect a blog first before creating a schedule.")
        return

    # ─── Existing Schedules ───
    schedules = db.get_user_schedules(user["id"])
    if schedules:
        st.markdown("##### Active Schedules")
        for s in schedules:
            blog = next((b for b in blogs if b["id"] == s["blog_connection_id"]), None)
            blog_name = blog.get("blog_name") or "Unknown" if blog else "Deleted blog"

            with st.expander(f"📌 {s['name']} → {blog_name}"):
                st.write(f"**Frequency:** {s['frequency']}")
                st.write(f"**Language:** {s['language']}")
                st.write(f"**Categories:** {', '.join(s.get('categories', []))}")
                if s.get("next_run_at"):
                    st.write(f"**Next run:** {s['next_run_at']}")

                col1, col2 = st.columns(2)
                with col1:
                    enabled = st.toggle("Enabled", value=s.get("enabled", True), key=f"en_{s['id']}")
                    if enabled != s.get("enabled"):
                        db.toggle_schedule(s["id"], enabled)
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"del_s_{s['id']}"):
                        db.delete_schedule(s["id"], user["id"])
                        st.rerun()
        st.divider()

    # ─── Create New Schedule ───
    st.markdown("##### Create New Schedule")

    with st.form("new_schedule"):
        name = st.text_input("Schedule Name", placeholder="e.g., Daily Tech News")

        blog_choice = st.selectbox(
            "Target Blog",
            options=blogs,
            format_func=lambda b: b.get("blog_name") or b.get("blog_id", "Unknown"),
        )

        language = st.selectbox(
            "Content Language",
            ["en", "ko", "ja", "es"],
            format_func=lambda x: {
                "en": "🇺🇸 English",
                "ko": "🇰🇷 한국어",
                "ja": "🇯🇵 日本語",
                "es": "🇪🇸 Español",
            }[x],
        )

        # Filter categories by language
        available_cats = {
            k: v for k, v in CATEGORY_FEEDS.items() if v["language"] == language
        }
        if not available_cats:
            available_cats = CATEGORY_FEEDS

        category_keys = st.multiselect(
            "Content Categories",
            options=list(available_cats.keys()),
            format_func=lambda k: available_cats[k]["name"],
            default=list(available_cats.keys())[:2] if available_cats else [],
        )

        custom_topics = st.text_area(
            "Custom Topics (optional, one per line)",
            placeholder="How to save money on groceries\nBest AI tools for writers\n...",
            help="If provided, these topics will be used instead of trending news.",
        )

        frequency = st.selectbox(
            "Posting Frequency",
            ["daily", "twice_daily", "weekly"],
            format_func=lambda x: {
                "daily": "Daily (1 post/day)",
                "twice_daily": "Twice Daily (2 posts/day)",
                "weekly": "Weekly (1 post/week)",
            }[x],
        )

        tone = st.selectbox(
            "Writing Tone",
            ["friendly", "professional", "casual", "educational", "persuasive"],
        )

        word_count = st.slider("Target Word Count", 500, 2000, 1000, step=100)

        if st.form_submit_button("Create Schedule"):
            if not name or not category_keys:
                st.error("Name and at least one category required")
            else:
                # Set first run to 1 minute from now so it runs soon
                next_run = (datetime.utcnow() + timedelta(minutes=1)).isoformat() + "Z"
                db.create_schedule(
                    user_id=user["id"],
                    blog_connection_id=blog_choice["id"],
                    name=name,
                    categories=category_keys,
                    language=language,
                    frequency=frequency,
                    tone=tone,
                    word_count=word_count,
                    custom_topics=custom_topics,
                    next_run_at=next_run,
                )
                st.success("Schedule created! It will run within the next hour.")
                st.rerun()
