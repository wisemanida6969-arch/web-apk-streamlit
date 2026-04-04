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
#  Platinum UI Styling (v4.2 Hero & Value Prop)
# ─────────────────────────────────────────────
def apply_platinum_design():
    """Injects high-end CSS for Hero, Value Prop, and Glow Effects."""
    st.markdown("""
        <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
            }

            /* 4. Value Proposition Card Style */
            .value-card {
                background: rgba(30, 41, 59, 0.3);
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 24px;
                padding: 2.2rem;
                text-align: center;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                height: 100%;
            }
            
            .value-card:hover {
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(59, 130, 246, 0.3);
                transform: translateY(-8px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            }
            
            .value-icon {
                font-size: 2.5rem;
                margin-bottom: 1.5rem;
                background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .value-title {
                font-size: 1.25rem;
                font-weight: 700;
                color: #FFFFFF;
                margin-bottom: 0.8rem;
            }
            
            .value-desc {
                font-size: 0.95rem;
                color: #94A3B8;
                line-height: 1.5;
            }
            
            /* Hide Streamlit components */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
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

# Hero Section
st.markdown("""
<div style="padding: 6rem 0 3rem 0;">
    <h1 class="hero-headline">Gain Back Your Study Time.</h1>
    <p class="hero-subheadline">
        AI-Powered YouTube Analysis for Efficient Learning.<br>
        Stop Watching, Start Learning.
    </p>
</div>
""", unsafe_allow_html=True)

# Hero CTA
c1, c2, c3 = st.columns([1, 1.5, 1])
with c2:
    if not st.session_state.user:
        if st.button("Get Started for Free", key="hero_cta", use_container_width=True): pass
        st.markdown("""
            <script>
                var buttons = window.parent.document.querySelectorAll('button');
                buttons.forEach(function(btn) {
                    if (btn.innerText.includes("Get Started for Free")) { btn.classList.add('glow-cta'); }
                });
            </script>
        """, unsafe_allow_html=True)

st.write("<br><br><br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Layout: Value Proposition Section
# ─────────────────────────────────────────────
st.markdown("<h2 style='text-align:center; margin-bottom:4rem; font-size:2.5rem; letter-spacing:-0.03em;'>Why Trytimeback?</h2>", unsafe_allow_html=True)

v1, v2, v3 = st.columns(3)

with v1:
    st.markdown("""
    <div class="value-card">
        <i class="fa-solid fa-clock-rotate-left value-icon"></i>
        <div class="value-title">Time Efficiency</div>
        <div class="value-desc">1 Hour Video, 5 Minute Summary.<br>Gain a massive strategic advantage in your study schedule.</div>
    </div>
    """, unsafe_allow_html=True)

with v2:
    st.markdown("""
    <div class="value-card">
        <i class="fa-solid fa-brain value-icon"></i>
        <div class="value-title">Core Extraction</div>
        <div class="value-desc">AI Extracts Core Concepts & Formulas.<br>Zero fluff. Pure intelligence for rapid knowledge mastery.</div>
    </div>
    """, unsafe_allow_html=True)

with v3:
    st.markdown("""
    <div class="value-card">
        <i class="fa-solid fa-globe value-icon"></i>
        <div class="value-title">Global Learning</div>
        <div class="value-desc">Support Multiple Languages with High Accuracy.<br>Learn from the world's best lecturers in any language.</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Main Engine Authentication & Functional Modules
# ─────────────────────────────────────────────
st.write("<br><br><br><br>", unsafe_allow_html=True)
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
                st.link_button("🚀 Authenticate Your Learning Hub", res.url, use_container_width=True)
                st.markdown("<center style='color:#64748B; margin-top:1rem;'>Claims your time. Join the global top 1%.</center>", unsafe_allow_html=True)
        except Exception as e: st.error(f"UI Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# Handle OAuth Callback
if "code" in st.query_params and not st.session_state.user:
    try:
        res = supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
        if res and res.user:
            st.session_state.user = res.user
            st.query_params.clear()
            st.rerun()
    except: pass

# Footer
st.markdown("""
<div style="text-align:center; padding:4rem 2rem; border-top:1px solid rgba(255,255,255,0.05); margin-top:6rem;">
    <p style='color:#475569; font-size:0.85rem; margin-bottom:0.5rem;'>Legal Disclaimer: Trytimeback is an AI analysis tool for educational purposes. We do not own or store original video content.</p>
    <p style='color:#64748B; font-size:0.8rem; letter-spacing:0.1em; margin:0;'>© 2026 YouTube Insight Analyzer • PLATINUM GLOBAL ATOMIC v4.3</p>
</div>
""", unsafe_allow_html=True)
