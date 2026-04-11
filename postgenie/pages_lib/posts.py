"""Generated posts history page."""
import streamlit as st

from lib.supabase_client import db


def render(user: dict):
    st.markdown("#### 📝 Generated Posts")
    st.caption("History of all posts PostGenie has generated for you.")

    posts = db.get_user_posts(user["id"], limit=100) if user.get("id") else []

    if not posts:
        st.info("No posts yet. Create a schedule to start generating content!")
        return

    # Filter tabs
    tab1, tab2, tab3 = st.tabs([
        f"✅ Published ({sum(1 for p in posts if p['status'] == 'published')})",
        f"⏳ Pending ({sum(1 for p in posts if p['status'] == 'pending')})",
        f"❌ Failed ({sum(1 for p in posts if p['status'] == 'failed')})",
    ])

    def render_post_list(filtered):
        if not filtered:
            st.caption("No posts in this category.")
            return
        for post in filtered:
            with st.expander(f"**{post['title']}** — {post['created_at'][:10]}"):
                if post.get("blog_post_url"):
                    st.markdown(f"🔗 [View on Blog]({post['blog_post_url']})")
                st.caption(f"Category: {post.get('category', 'N/A')} · Language: {post.get('language', 'N/A')}")
                if post.get("token_count"):
                    st.caption(f"Tokens used: {post['token_count']}")
                if post.get("error_message"):
                    st.error(post["error_message"])
                with st.expander("View Content"):
                    st.markdown(post["content"], unsafe_allow_html=True)

    with tab1:
        render_post_list([p for p in posts if p["status"] == "published"])
    with tab2:
        render_post_list([p for p in posts if p["status"] == "pending"])
    with tab3:
        render_post_list([p for p in posts if p["status"] == "failed"])
