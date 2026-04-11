"""
PostGenie — AI Blog Automation SaaS
Main Streamlit application entry point.
"""
import streamlit as st

from lib.auth import get_login_url, handle_oauth_callback, logout
from lib.supabase_client import db


# ─── Page Config ───
st.set_page_config(
    page_title="PostGenie — AI Blog Automation",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─── Global Styles ───
st.markdown("""
<style>
    .stApp {
        background: #0f172a;
        color: #e2e8f0;
    }
    .main-hero {
        text-align: center;
        padding: 60px 20px 40px;
    }
    .logo-text {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #8b5cf6, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
        margin-bottom: 8px;
    }
    .tagline {
        font-size: 1.2rem;
        color: #94a3b8;
        margin-bottom: 32px;
    }
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        max-width: 900px;
        margin: 40px auto;
    }
    .feature-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }
    .feature-icon {
        font-size: 2.2rem;
        margin-bottom: 12px;
    }
    .feature-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 8px;
    }
    .feature-desc {
        font-size: 0.85rem;
        color: #64748b;
        line-height: 1.6;
    }
    .google-btn {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        background: #ffffff;
        color: #1e293b;
        padding: 14px 36px;
        border-radius: 12px;
        text-decoration: none;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        margin: 20px 0;
    }
    .google-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(139,92,246,0.3);
    }
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
    }
    .stButton>button {
        background: linear-gradient(135deg, #8b5cf6, #3b82f6);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(139,92,246,0.4);
    }
</style>
""", unsafe_allow_html=True)


# ─── OAuth Callback Handler ───
handle_oauth_callback()


# ─── Not Logged In → Landing Page ───
if not st.session_state.get("logged_in"):
    login_url = get_login_url()

    # Hero header
    st.markdown("""
    <div class="main-hero">
        <div class="logo-text">✨ PostGenie</div>
        <div class="tagline">AI-Powered Blog Automation — Set it and forget it.</div>
    </div>
    """, unsafe_allow_html=True)

    # Sign in button — plain st.link_button (reliable, default styling)
    col_a, col_b, col_c = st.columns([1, 1.5, 1])
    with col_b:
        st.link_button(
            "Sign in with Google",
            login_url,
            use_container_width=True,
            type="primary",
        )

    # Features section
    st.markdown("""
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">AI-Written Content</div>
            <div class="feature-desc">Claude AI generates high-quality SEO blog posts tailored to your niche.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📅</div>
            <div class="feature-title">Auto-Scheduled</div>
            <div class="feature-desc">Set your schedule once. Posts go live daily without lifting a finger.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🌍</div>
            <div class="feature-title">Trending Topics</div>
            <div class="feature-desc">Auto-fetches trending news to keep your content fresh and relevant.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔗</div>
            <div class="feature-title">Multi-Platform</div>
            <div class="feature-desc">Publishes directly to Blogger, WordPress, and more.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pricing section
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; color:#f1f5f9;'>Simple Pricing</h2>", unsafe_allow_html=True)

    cols = st.columns(4)
    plans = [
        ("Free", "$0", ["1 blog", "1 post/week", "Basic topics"]),
        ("Basic", "$9/mo", ["1 blog", "1 post/day", "All categories"]),
        ("Pro", "$29/mo", ["3 blogs", "3 posts/day", "Custom topics"]),
        ("Agency", "$99/mo", ["10 blogs", "30 posts/day", "API access"]),
    ]
    for col, (name, price, features) in zip(cols, plans):
        with col:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-title">{name}</div>
                <div style="font-size:1.8rem; font-weight:900; color:#8b5cf6; margin:12px 0;">{price}</div>
                <div class="feature-desc">
                    {"<br>".join("✓ " + f for f in features)}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # User Guide + Contact footer
    st.markdown("""
    <div style="text-align:center; margin:40px 0 10px;">
        <a href="https://github.com/wisemanida6969-arch/web-apk-streamlit/raw/master/postgenie/docs/PostGenie_Guide.pdf"
           target="_blank"
           style="color:#94a3b8; font-size:0.9rem; text-decoration:none;
                  padding:10px 20px; border:1px solid rgba(255,255,255,0.15);
                  border-radius:8px; display:inline-block; margin:0 6px;">
            📘 사용 가이드 (한국어 PDF)
        </a>
        <a href="https://github.com/wisemanida6969-arch/web-apk-streamlit/raw/master/postgenie/docs/PostGenie_Guide_EN.pdf"
           target="_blank"
           style="color:#94a3b8; font-size:0.9rem; text-decoration:none;
                  padding:10px 20px; border:1px solid rgba(255,255,255,0.15);
                  border-radius:8px; display:inline-block; margin:0 6px;">
            📘 User Guide (English PDF)
        </a>
        <a href="mailto:admin@trytimeback.com"
           style="color:#94a3b8; font-size:0.9rem; text-decoration:none;
                  padding:10px 20px; border:1px solid rgba(255,255,255,0.15);
                  border-radius:8px; display:inline-block; margin:0 6px;">
            ✉️ 문의하기 / Contact
        </a>
    </div>
    <div style="text-align:center; margin:20px 0 10px; color:#64748b; font-size:0.8rem;">
        문의 / Support: <a href="mailto:admin@trytimeback.com" style="color:#8b5cf6; text-decoration:none;">admin@trytimeback.com</a>
    </div>
    <div style="text-align:center; margin:10px 0 30px; color:#475569; font-size:0.75rem;">
        © 2026 PostGenie. AI-Powered Blog Automation.
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ─── Logged In → Dashboard ───
user = st.session_state.get("user", {})

# Sidebar
with st.sidebar:
    if user.get("picture"):
        st.image(user["picture"], width=60)

    plan = user.get("plan", "free")
    name_suffix = " 👑" if plan == "admin" else ""
    st.markdown(f"**{user.get('name', 'User')}{name_suffix}**")
    st.caption(user.get("email", ""))

    if plan == "admin":
        st.success("👑 **ADMIN** — Unlimited access")
    else:
        st.caption(f"Plan: **{plan.title()}**")
    st.divider()

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "🔗 Connect Blog", "📅 Schedules", "📝 Posts", "💎 Upgrade"],
        label_visibility="collapsed",
    )

    st.divider()
    st.link_button(
        "📘 사용 가이드 (한국어)",
        "https://github.com/wisemanida6969-arch/web-apk-streamlit/raw/master/postgenie/docs/PostGenie_Guide.pdf",
        use_container_width=True,
    )
    st.link_button(
        "📘 User Guide (English)",
        "https://github.com/wisemanida6969-arch/web-apk-streamlit/raw/master/postgenie/docs/PostGenie_Guide_EN.pdf",
        use_container_width=True,
    )
    st.link_button(
        "✉️ 문의 / Contact",
        "mailto:admin@trytimeback.com",
        use_container_width=True,
    )
    if st.button("Sign Out", use_container_width=True):
        logout()

# Main content
st.markdown(f"### Welcome back, {user.get('name', 'there')}! 👋")

if page == "📊 Dashboard":
    st.markdown("#### Dashboard")

    col1, col2, col3 = st.columns(3)
    blogs = db.get_user_blogs(user["id"]) if user.get("id") else []
    schedules = db.get_user_schedules(user["id"]) if user.get("id") else []
    posts = db.get_user_posts(user["id"], limit=100) if user.get("id") else []

    col1.metric("Connected Blogs", len(blogs))
    col2.metric("Active Schedules", len([s for s in schedules if s.get("enabled")]))
    col3.metric("Posts Published", len([p for p in posts if p.get("status") == "published"]))

    st.markdown("#### Recent Posts")
    if posts:
        for post in posts[:10]:
            status_emoji = {"published": "✅", "pending": "⏳", "failed": "❌"}.get(post["status"], "•")
            st.markdown(f"{status_emoji} **{post['title']}** — _{post['created_at'][:10]}_")
    else:
        st.info("No posts yet. Connect a blog and create a schedule to get started!")

elif page == "🔗 Connect Blog":
    from pages_lib.connect_blog import render as render_connect
    render_connect(user)

elif page == "📅 Schedules":
    from pages_lib.schedules import render as render_schedules
    render_schedules(user)

elif page == "📝 Posts":
    from pages_lib.posts import render as render_posts
    render_posts(user)

elif page == "💎 Upgrade":
    from pages_lib.upgrade import render as render_upgrade
    render_upgrade(user)
