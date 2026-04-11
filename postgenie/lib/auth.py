"""Google OAuth authentication for PostGenie."""
import requests
import streamlit as st
from urllib.parse import urlencode

from lib.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    is_admin,
)
from lib.supabase_client import db


def get_login_url() -> str:
    """Generate Google OAuth login URL."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token."""
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI,
        },
    )
    resp.raise_for_status()
    return resp.json()


def get_user_info(access_token: str) -> dict:
    """Fetch user profile from Google."""
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


def handle_oauth_callback():
    """Handle OAuth redirect and create/update user in DB.

    This handles BOTH login callbacks AND Blogger connection callbacks.
    Blogger connection uses state='blogger_connect' and also gets the refresh token.
    """
    if st.session_state.get("login_error"):
        st.error(st.session_state.pop("login_error"))

    params = st.query_params
    code = params.get("code")
    state = params.get("state", "")

    if not code:
        return

    # Skip if already handled in a previous run
    if st.session_state.get("_oauth_processed") == code:
        return

    try:
        token_data = exchange_code_for_token(code)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token", "")

        user_info = get_user_info(access_token)

        # Upsert user in Supabase (works for both login and blogger connect)
        user = db.upsert_user(
            email=user_info["email"],
            name=user_info.get("name", ""),
            picture=user_info.get("picture", ""),
        )

        # Auto-promote admin emails to 'admin' plan (best-effort)
        if is_admin(user.get("email", "")) and user.get("plan") != "admin":
            try:
                db.update_user_plan(user["id"], "admin")
                user["plan"] = "admin"
            except Exception as promo_err:
                # DB constraint may not yet allow 'admin' plan
                # (run migrations/001_add_admin_plan.sql in Supabase)
                print(f"[auth] Admin promotion skipped: {promo_err}")

        st.session_state["logged_in"] = True
        st.session_state["user"] = user
        st.session_state["_oauth_processed"] = code

        # If this was a Blogger connect flow, stash tokens for the connect_blog page
        if state == "blogger_connect" and refresh_token:
            st.session_state["_pending_blogger_refresh"] = refresh_token
            st.session_state["_pending_blogger_access"] = access_token
            st.session_state["_pending_page"] = "🔗 Connect Blog"

        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.session_state["login_error"] = f"Login failed: {e}"
        st.query_params.clear()
        st.rerun()


def logout():
    """Clear session and log out."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def require_auth():
    """Redirect to login if not authenticated. Returns user dict."""
    if not st.session_state.get("logged_in"):
        st.warning("Please sign in to continue.")
        st.stop()
    return st.session_state.get("user", {})
