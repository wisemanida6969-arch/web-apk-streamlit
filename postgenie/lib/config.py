"""PostGenie configuration loader."""
import os

# Streamlit is optional — worker runs without it
try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False


def get_secret(key: str, default: str = "") -> str:
    """Read secret from Streamlit secrets (if available) or env var."""
    if _HAS_STREAMLIT:
        try:
            return st.secrets.get(key, os.environ.get(key, default))
        except Exception:
            pass
    return os.environ.get(key, default)


# ─── Supabase ───
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = get_secret("SUPABASE_SERVICE_KEY")

# ─── Google OAuth (for login) ───
GOOGLE_CLIENT_ID = get_secret("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = get_secret("GOOGLE_REDIRECT_URI", "http://localhost:8501/")

# ─── Blogger OAuth (for blog connection - same or different credentials) ───
BLOGGER_CLIENT_ID = get_secret("BLOGGER_CLIENT_ID", GOOGLE_CLIENT_ID)
BLOGGER_CLIENT_SECRET = get_secret("BLOGGER_CLIENT_SECRET", GOOGLE_CLIENT_SECRET)

# ─── Claude API ───
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
CLAUDE_MODEL = get_secret("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

# ─── Paddle ───
PADDLE_VENDOR_ID = get_secret("PADDLE_VENDOR_ID")
PADDLE_API_KEY = get_secret("PADDLE_API_KEY")

# Paddle Price IDs (to be created in Paddle dashboard)
PADDLE_PRICE_BASIC_MONTHLY = get_secret("PADDLE_PRICE_BASIC_MONTHLY", "")
PADDLE_PRICE_PRO_MONTHLY = get_secret("PADDLE_PRICE_PRO_MONTHLY", "")
PADDLE_PRICE_AGENCY_MONTHLY = get_secret("PADDLE_PRICE_AGENCY_MONTHLY", "")

# ─── Plan Limits ───
PLAN_LIMITS = {
    "free": {"blogs": 1, "posts_per_week": 1, "schedules": 1},
    "basic": {"blogs": 1, "posts_per_day": 1, "schedules": 1},
    "pro": {"blogs": 3, "posts_per_day": 3, "schedules": 3},
    "agency": {"blogs": 10, "posts_per_day": 30, "schedules": 10},
    "admin": {"blogs": 9999, "posts_per_day": 9999, "schedules": 9999},
}

# ─── Admin Emails (comma-separated, full access) ───
ADMIN_EMAILS = [
    e.strip().lower()
    for e in get_secret("ADMIN_EMAILS", "wisemanida6969@gmail.com").split(",")
    if e.strip()
]


def is_admin(email: str) -> bool:
    """Check if the given email has admin privileges."""
    return (email or "").strip().lower() in ADMIN_EMAILS
