"""Google OAuth authentication for PostGenie."""
import requests
import streamlit as st
from urllib.parse import urlencode

from lib.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
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
    """Handle OAuth redirect and create/update user in DB."""
    if st.session_state.get("login_error"):
        st.error(st.session_state.pop("login_error"))

    params = st.query_params
    code = params.get("code")

    if code and not st.session_state.get("logged_in"):
        try:
            token_data = exchange_code_for_token(code)
            user_info = get_user_info(token_data["access_token"])

            # Upsert user in Supabase
            user = db.upsert_user(
                email=user_info["email"],
                name=user_info.get("name", ""),
                picture=user_info.get("picture", ""),
            )

            st.session_state["logged_in"] = True
            st.session_state["user"] = user
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
