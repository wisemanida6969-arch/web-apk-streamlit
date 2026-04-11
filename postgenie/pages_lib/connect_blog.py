"""Blog connection page."""
import streamlit as st
from urllib.parse import urlencode
import requests

from lib.config import (
    BLOGGER_CLIENT_ID,
    BLOGGER_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)
from lib.supabase_client import db


def get_blogger_auth_url() -> str:
    """OAuth URL for Blogger access (with offline access for refresh token)."""
    params = {
        "client_id": BLOGGER_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/blogger",
        "access_type": "offline",
        "prompt": "consent",
        "state": "blogger_connect",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_blogger_code(code: str) -> dict:
    """Exchange code for access + refresh token."""
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": BLOGGER_CLIENT_ID,
            "client_secret": BLOGGER_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI,
        },
    )
    resp.raise_for_status()
    return resp.json()


def list_user_blogs(access_token: str) -> list:
    """Fetch list of blogs owned by the user."""
    resp = requests.get(
        "https://www.googleapis.com/blogger/v3/users/self/blogs",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


def render(user: dict):
    st.markdown("#### 🔗 Connect Your Blog")
    st.caption("Connect Blogger, WordPress, or other blogs to start auto-publishing.")

    # ─── Existing Connections ───
    existing = db.get_user_blogs(user["id"]) if user.get("id") else []
    if existing:
        st.markdown("##### Connected Blogs")
        for blog in existing:
            col1, col2, col3 = st.columns([4, 3, 1])
            col1.write(f"**{blog.get('blog_name') or blog.get('blog_id')}**")
            col2.caption(f"Platform: {blog['platform']}")
            with col3:
                if st.button("Remove", key=f"del_{blog['id']}"):
                    db.delete_blog_connection(blog["id"], user["id"])
                    st.rerun()
        st.divider()

    # ─── Add New Connection ───
    st.markdown("##### Add New Blog")

    platform = st.selectbox(
        "Platform",
        ["blogger", "wordpress"],
        format_func=lambda x: {"blogger": "Google Blogger", "wordpress": "WordPress (self-hosted)"}[x],
    )

    if platform == "blogger":
        st.info("Click below to authorize PostGenie to post to your Blogger account.")

        # Handle OAuth callback
        params = st.query_params
        if params.get("code") and params.get("state") == "blogger_connect":
            code = params.get("code")
            try:
                token_data = exchange_blogger_code(code)
                access_token = token_data["access_token"]
                refresh_token = token_data.get("refresh_token", "")

                if not refresh_token:
                    st.error("No refresh token received. Try revoking access in your Google account and reconnecting.")
                    st.query_params.clear()
                    return

                blogs = list_user_blogs(access_token)
                if not blogs:
                    st.error("No Blogger blogs found on your account.")
                    st.query_params.clear()
                    return

                st.session_state["_pending_blogger_blogs"] = blogs
                st.session_state["_pending_blogger_refresh"] = refresh_token
                st.session_state["_pending_blogger_access"] = access_token
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Blogger connection failed: {e}")
                st.query_params.clear()

        # Show pending blog selection
        if st.session_state.get("_pending_blogger_blogs"):
            blogs = st.session_state["_pending_blogger_blogs"]
            st.success(f"Found {len(blogs)} blog(s)!")
            blog_choice = st.selectbox(
                "Which blog to connect?",
                options=blogs,
                format_func=lambda b: f"{b['name']} ({b['url']})",
            )
            if st.button("Connect This Blog"):
                db.add_blog_connection(
                    user_id=user["id"],
                    platform="blogger",
                    blog_id=blog_choice["id"],
                    blog_name=blog_choice["name"],
                    blog_url=blog_choice["url"],
                    refresh_token=st.session_state["_pending_blogger_refresh"],
                    access_token=st.session_state["_pending_blogger_access"],
                )
                del st.session_state["_pending_blogger_blogs"]
                del st.session_state["_pending_blogger_refresh"]
                del st.session_state["_pending_blogger_access"]
                st.success("Blog connected!")
                st.rerun()
        else:
            auth_url = get_blogger_auth_url()
            st.markdown(
                f'<a href="{auth_url}" target="_self" class="google-btn">Authorize Blogger</a>',
                unsafe_allow_html=True,
            )

    elif platform == "wordpress":
        st.info("Enter your WordPress site details. Use an **Application Password** (not your login password).")
        with st.form("wp_form"):
            site_url = st.text_input("Site URL", placeholder="https://yourblog.com")
            username = st.text_input("WordPress Username")
            app_password = st.text_input("Application Password", type="password",
                                          help="Create one at: Users → Profile → Application Passwords")
            blog_name = st.text_input("Display Name (optional)")

            if st.form_submit_button("Connect WordPress"):
                if not site_url or not username or not app_password:
                    st.error("All fields required")
                else:
                    db.add_blog_connection(
                        user_id=user["id"],
                        platform="wordpress",
                        blog_id=site_url,
                        blog_name=blog_name or site_url,
                        blog_url=site_url,
                        wp_site_url=site_url,
                        wp_username=username,
                        wp_app_password=app_password,
                    )
                    st.success("WordPress connected!")
                    st.rerun()
