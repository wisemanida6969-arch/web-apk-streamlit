import os
os.environ['TZ'] = 'UTC'

# ── FIX: Purge proxy env vars to prevent 'unexpected keyword argument proxy' error ──
for env_key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if env_key in os.environ:
        del os.environ[env_key]

import streamlit as st
import re
import random
import json

# ─────────────────────────────────────────────
#  Lazy Loading Helpers (To prevent Railway timeouts)
# ─────────────────────────────────────────────
def get_supabase_client():
    from supabase import create_client
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_ANON_KEY")
    if url and key and "your-project" not in url:
        try:
            return create_client(url, key)
        except:
            return None
    return None

def get_openai_client():
    from openai import OpenAI
    key = get_secret("OPENAI_API_KEY")
    if key and "실제_키" not in key:
        return OpenAI(api_key=key)
    return None

# ─────────────────────────────────────────────
#  Global Settings
# ─────────────────────────────────────────────
ADMIN_EMAIL = "wisemanida6969@gmail.com"
DAILY_BUDGET_LIMIT = 10.0
COST_PER_SUMMARY = 0.01

st.set_page_config(
    page_title="YouTube Core Concept Analyzer",
    page_icon="📜",
    layout="wide",
)

# ── Force Session State ──
if "locale" not in st.session_state: st.session_state.locale = "en"
for k in ["analysis_results", "player_video_id", "selected_ts", "selected_poem", "user"]:
    if k not in st.session_state: st.session_state[k] = None
if st.session_state.selected_ts is None: st.session_state.selected_ts = 0

# ─────────────────────────────────────────────
#  Robust Secret Handling
# ─────────────────────────────────────────────
def get_secret(key, default=""):
    env_val = os.environ.get(key)
    if env_val: return env_val.strip()
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except: pass
    return default

api_key = get_secret("OPENAI_API_KEY")
supabase_url = get_secret("SUPABASE_URL")
supabase_key = get_secret("SUPABASE_ANON_KEY")

# Initialize Supabase (Lightweight)
if "supabase" not in st.session_state:
    st.session_state.supabase = get_supabase_client()

supabase = st.session_state.supabase

# ─────────────────────────────────────────────
#  Auth Handling
# ─────────────────────────────────────────────
if supabase:
    if "code" in st.query_params:
        try:
            res = supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
            if res and res.user:
                st.session_state.user = res.user
                st.query_params.clear()
                st.rerun()
        except: pass
    
    if not st.session_state.user:
        try:
            user_res = supabase.auth.get_user()
            if user_res and user_res.user:
                st.session_state.user = user_res.user
        except: pass

# ─────────────────────────────────────────────
#  UI Design
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; color: #E2E2E2; }
.stApp { background-color: #0F0F13; min-height: 100vh; }
.hero-header { text-align: center; padding: 2.8rem 1rem 1.6rem; border-bottom: 1px solid #23232A; margin-bottom: 2rem; }
.hero-header h1 { font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; color: #FFFFFF; }
.glass-card { background: rgba(26, 26, 33, 0.6); backdrop-filter: blur(10px); border: 1px solid #32323D; border-radius: 20px; padding: 2rem 2.2rem; margin-bottom: 1.4rem; }
.concept-card { background: #1A1A21; border-left: 5px solid #4F4F5C; border-radius: 14px; padding: 1.6rem 1.8rem; margin-bottom: 1rem; }
.stButton > button { background: #2A2A33 !important; color: #FFFFFF !important; border-radius: 50px !important; width: 100% !important; }
.stButton > button:hover { background: #B19B72 !important; color: #0F0F13 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def extract_video_id(url: str):
    m = re.search(r"(?:v=|\/|be\/)([A-Za-z0-9_\-]{11})", url)
    return m.group(1) if m else None

def seconds_to_mmss(seconds):
    s = int(seconds)
    m, sec = divmod(s % 3600, 60)
    h = s // 3600
    return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

# ─────────────────────────────────────────────
#  Main UI
# ─────────────────────────────────────────────
try:
    st.warning("⚠️ SYSTEM LIVE (v2.2-OPTIMIZED) - If you see this, the server is responding!")
    st.markdown('<div class="hero-header"><h1>YouTube Core Concept Analyzer</h1><p>Global Edition • 100% Stable</p></div>', unsafe_allow_html=True)

    if not st.session_state.user:
        if supabase:
            redirect_url = get_secret("REDIRECT_URL", "https://trytimeback.com")
            res = supabase.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": redirect_url}})
            col1, col2, col3 = st.columns([1,2,1])
            with col2: st.link_button("🌐 Sign in with Google", res.url, use_container_width=True)
        else:
            st.warning("Guest Mode: Cloud login unavailable.")
    else:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown(f"<center>👤 {st.session_state.user.email}</center>", unsafe_allow_html=True)
            if st.button("Logout"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()

    tab1, tab2 = st.tabs(["Analyze", "Pricing"])

    with tab1:
        url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("Start Analysis →", use_container_width=True):
            if not api_key: st.error("OpenAI API Key missing"); st.stop()
            vid = extract_video_id(url)
            if not vid: st.error("Invalid URL"); st.stop()
            
            with st.spinner("Analyzing (This might take a moment)..."):
                from youtube_transcript_api import YouTubeTranscriptApi
                from db import add_global_cost, increment_daily_usage, save_to_cache
                
                ytt = YouTubeTranscriptApi()
                try: transcript = ytt.fetch(vid, languages=['en', 'ko'])
                except: transcript = ytt.fetch(vid)
                
                text = "\n".join([f"[{seconds_to_mmss(e['start'])}] {e['text']}" for e in transcript])
                
                client = get_openai_client()
                if not client: st.error("Failed to initialize AI"); st.stop()
                
                res_gpt = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "Analyze video. Extract 3 core concepts. Output JSON in English."}, {"role": "user", "content": text[:12000]}],
                    response_format={"type": "json_object"}
                )
                gpt_res = json.loads(res_gpt.choices[0].message.content)
                
                st.session_state.analysis_results = gpt_res
                st.session_state.player_video_id = vid
                
                # Background tasks
                add_global_cost(COST_PER_SUMMARY)
                increment_daily_usage(st.session_state.user.id if st.session_state.user else "guest")
                save_to_cache(vid, gpt_res.get("concepts", []), text, len(transcript), seconds_to_mmss(transcript[-1]['start']))
                st.rerun()

        if st.session_state.analysis_results:
            r = st.session_state.analysis_results
            col_l, col_r = st.columns(2)
            with col_l:
                for i, c in enumerate(r.get("concepts", [])):
                    st.markdown(f'<div class="concept-card"><h3>{c["title"]}</h3><p>{c["summary"]}</p></div>', unsafe_allow_html=True)
                    if st.button(f"Play from {c['timestamp']}", key=f"p_{i}"):
                        ts = c['timestamp'].split(':')
                        st.session_state.selected_ts = int(ts[0])*60 + int(ts[1])
                        st.rerun()
            with col_r:
                embed_url = f"https://www.youtube.com/embed/{st.session_state.player_video_id}?start={st.session_state.selected_ts}&autoplay=1"
                st.markdown(f'<iframe width="100%" height="400" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>', unsafe_allow_html=True)

    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown('<div class="pricing-card"><h3>Free</h3><h2>$0</h2><p>3 summaries / day</p></div>', unsafe_allow_html=True)
        with col2: st.markdown('<div class="pricing-card"><h3>Monthly</h3><h2>$14.99</h2><p>Unlimited access</p></div>', unsafe_allow_html=True)
        with col3: st.markdown('<div class="pricing-card"><h3>Yearly</h3><h2>$99</h2><p>Best Value</p></div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"System Error: {e}")

st.markdown("<center>© 2026 YouTube Core Concept Analyzer</center>", unsafe_allow_html=True)
