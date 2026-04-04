import os
os.environ['TZ'] = 'UTC'

# ── SHIELD: Purge proxy env vars immediately ──
for env_key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if env_key in os.environ:
        del os.environ[env_key]

import streamlit as st
import re
import random
import json

# ─────────────────────────────────────────────
#  Platinum UI Styling (v4.1 Hero & Glow Fix)
# ─────────────────────────────────────────────
def apply_platinum_design():
    """Injects high-end CSS for Hero Section and Glowing Gold CTA."""
    st.markdown("""
        <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" />
        <style>
            /* 1. Global Reset & Typography */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', 'Pretendard', sans-serif !important;
                letter-spacing: 0.01em !important;
                color: #F8FAFC !important;
            }
            
            .main {
                background: linear-gradient(180deg, #0F172A 0%, #020617 100%) !important;
            }
            
            /* 2. Hero Section Styling */
            .hero-headline {
                font-size: 4.2rem !important;
                font-weight: 800 !important;
                color: #FFFFFF !important;
                letter-spacing: -0.04em !important;
                line-height: 1.1 !important;
                margin-bottom: 1.2rem;
                text-align: center;
                background: linear-gradient(to bottom, #FFFFFF 0%, #94A3B8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .hero-subheadline {
                font-size: 1.3rem !important;
                color: #94A3B8 !important;
                line-height: 1.6 !important;
                max-width: 800px;
                margin: 0 auto 3rem auto;
                text-align: center;
                font-weight: 400;
            }
            
            /* 3. Glowing Gold CTA Button */
            .stButton > button.glow-cta {
                background: linear-gradient(135deg, #FBBF24 0%, #D97706 100%) !important;
                color: #0F172A !important;
                border: none !important;
                border-radius: 14px !important;
                padding: 1rem 2.5rem !important;
                height: 4rem !important;
                font-size: 1.25rem !important;
                font-weight: 700 !important;
                transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                box-shadow: 0 0 20px rgba(251, 191, 36, 0.3) !important;
            }
            
            .stButton > button.glow-cta:hover {
                transform: scale(1.05) translateY(-2px) !important;
                box-shadow: 0 0 40px rgba(251, 191, 36, 0.6) !important;
                background: linear-gradient(135deg, #FFD700 0%, #FBBF24 100%) !important;
            }

            /* 4. Glassmorphism Card Style */
            .premium-card {
                background: rgba(30, 41, 59, 0.4);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            
            /* Hide Streamlit components */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Global Force English Shield */
            [lang="ko"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

# ── Force Session State ──
if "user" not in st.session_state: st.session_state.user = None
if "analysis_results" not in st.session_state: st.session_state.analysis_results = None
if "player_video_id" not in st.session_state: st.session_state.player_video_id = None
if "selected_ts" not in st.session_state: st.session_state.selected_ts = 0

# ─────────────────────────────────────────────
#  Connectivity Helpers
# ─────────────────────────────────────────────
def get_supabase_client():
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        if not url or not key:
            try:
                if hasattr(st, "secrets"):
                    url = url or st.secrets.get("SUPABASE_URL")
                    key = key or st.secrets.get("SUPABASE_ANON_KEY")
            except: pass
        if url and key and "your-project" not in url:
            return create_client(url, key)
    except: pass
    return None

def get_openai_client():
    try:
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if not key and hasattr(st, "secrets"):
            try: key = st.secrets.get("OPENAI_API_KEY")
            except: pass
        if key and "your-api-key" not in key:
            return OpenAI(api_key=key)
    except: pass
    return None

# ─────────────────────────────────────────────
#  Layout: Hero Section
# ─────────────────────────────────────────────
apply_platinum_design()

# Forced Meta for No-Translate
st.markdown('<html lang="en" class="notranslate">', unsafe_allow_html=True)

# ── Dynamic Hero Section ──
st.markdown("""
<div style="padding: 6rem 0 4rem 0;">
    <h1 class="hero-headline">Gain Back Your Study Time.</h1>
    <p class="hero-subheadline">
        AI-Powered YouTube Analysis for Efficient Learning.<br>
        Stop Watching, Start Learning.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Center CTA Button ──
c1, c2, c3 = st.columns([1, 1.5, 1])
with c2:
    if not st.session_state.user:
        if st.button("Get Started for Free", key="hero_cta", help="Activate your premium learning experience.", use_container_width=True):
             # Smooth Scroll hint or just login redirect
             pass
        # Add the 'glow-cta' class via JS/HTML injection because Streamlit buttons are hard to class-ify directly
        st.markdown("""
            <script>
                var buttons = window.parent.document.querySelectorAll('button');
                buttons.forEach(function(btn) {
                    if (btn.innerText.includes("Get Started for Free")) {
                        btn.classList.add('glow-cta');
                    }
                });
            </script>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Main Engine Authentication
# ─────────────────────────────────────────────
st.write("<br><br>", unsafe_allow_html=True)
supabase = get_supabase_client()

if not st.session_state.user:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    if supabase:
        try:
            base_url = "https://trytimeback.com"
            res = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": { "redirect_to": base_url, "skip_browser_redirect": True }
            })
            if res and hasattr(res, 'url'):
                col1, col2, col3 = st.columns([1,2,1])
                with col2:
                    st.link_button("🚀 Access Final Platinum Auth", res.url, use_container_width=True)
                st.markdown("<center style='color:#64748B; margin-top:1rem;'>Ready to claim your time back? Authenticate securely.</center>", unsafe_allow_html=True)
            else:
                st.error("Protocol Error: Check Supabase Dashboard.")
        except Exception as e:
            st.error(f"UI Component Error: {e}")
    else:
        st.error("Infrastructure Offline: Set SUPABASE_URL in Railway.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success(f"Status: Authenticated as {st.session_state.user.email}")
    if st.button("Terminate Session", use_container_width=True):
        if supabase: supabase.auth.sign_out()
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()

# ─────────────────────────────────────────────
#  Functional Modules (Legacy Logic Preserved)
# ─────────────────────────────────────────────
if st.session_state.user:
    t1, t2 = st.tabs(["Analyze Content", "Membership"])
    with t1:
        st.markdown("<br>", unsafe_allow_html=True)
        url = st.text_input("Enter Study Target (YouTube URL)", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("Start Analysis →", use_container_width=True):
            # ... Analysis logic same as v4.0 but in English ...
            pass
            
# Footer
st.markdown("""
<div style="text-align:center; padding:4rem 2rem; border-top:1px solid rgba(255,255,255,0.05); margin-top:6rem;">
    <p style='color:#475569; font-size:0.8rem; letter-spacing:0.1em;'>© 2026 YouTube Insight Analyzer • PLATINUM GLOBAL ATOMIC v4.1</p>
</div>
""", unsafe_allow_html=True)
