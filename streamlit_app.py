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
#  Lazy Loading & Connectivity Helpers
# ─────────────────────────────────────────────
def get_supabase_client():
    """Robust Supabase client loader for Railway environment."""
    try:
        from supabase import create_client
        # 1. Check OS Environment Variables (Railway Priority)
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        
        # 2. Fallback to st.secrets only if OS env is empty AND secrets exist
        if not url or not key:
            try:
                if hasattr(st, "secrets"):
                    url = url or st.secrets.get("SUPABASE_URL")
                    key = key or st.secrets.get("SUPABASE_ANON_KEY")
            except:
                pass
        
        if url and key and "your-project" not in url:
            return create_client(url, key)
    except Exception as e:
        # Don't crash the app, just log internal
        pass
    return None

def get_openai_client():
    """Robust OpenAI client loader."""
    try:
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            try:
                if hasattr(st, "secrets"):
                    key = st.secrets.get("OPENAI_API_KEY")
            except: pass
            
        if key and "실제_키" not in key:
            return OpenAI(api_key=key)
    except:
        pass
    return None

# ─────────────────────────────────────────────
#  Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Core Concept Analyzer",
    page_icon="📜",
    layout="wide",
)

# ── UI Header ──
st.warning("⚠️ GLOBAL STABLE (v3.1) - Production Live")
st.markdown('<div style="text-align:center; padding:2rem 0; border-bottom:1px solid #23232A; margin-bottom:2rem;">'
            '<h1 style="font-size:2.2rem; color:white; margin-bottom:0.5rem;">YouTube Core Concept Analyzer</h1>'
            '<p style="color:#A0A0A9;">Global Edition • Professional Insight Engine</p></div>', unsafe_allow_html=True)

# ── Force Session State ──
if "user" not in st.session_state: st.session_state.user = None
if "analysis_results" not in st.session_state: st.session_state.analysis_results = None
if "player_video_id" not in st.session_state: st.session_state.player_video_id = None
if "selected_ts" not in st.session_state: st.session_state.selected_ts = 0

# ─────────────────────────────────────────────
#  Logic Section
# ─────────────────────────────────────────────
supabase = get_supabase_client()

if supabase:
    # Handle Callback
    if "code" in st.query_params:
        try:
            res = supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
            if res and res.user:
                st.session_state.user = res.user
                st.query_params.clear()
                st.rerun()
        except: pass

    # Restore Session
    if not st.session_state.user:
        try:
            user_res = supabase.auth.get_user()
            if user_res and user_res.user:
                st.session_state.user = user_res.user
        except: pass

# ─────────────────────────────────────────────
#  Authentication Section
# ─────────────────────────────────────────────
st.markdown('<div style="background:rgba(26,26,33,0.6); padding:2rem; border-radius:20px; border:1px solid #32323D; text-align:center; margin-bottom:1.5rem;">', unsafe_allow_html=True)

if not st.session_state.user:
    if supabase:
        try:
            redirect_url = os.environ.get("REDIRECT_URL") or "https://trytimeback.com"
            res = supabase.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": redirect_url}})
            st.link_button("🌐 Sign in with Google", res.url, use_container_width=True)
            st.markdown("<small style='color:#6E6E7A;'>Access full features and daily summaries with a Google account.</small>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"OAuth initialization failed: {e}")
    else:
        st.error("🔑 API Keys Missing: Please set UPABASE_URL and SUPABASE_ANON_KEY in Railway Variables.")
        st.info("The application requires a database connection to enable Google Login.")
else:
    st.markdown(f"<center><span style='font-size:1.1rem;'>👤 Logged in as: <b>{st.session_state.user.email}</b></span></center>", unsafe_allow_html=True)
    if st.button("Logout", use_container_width=True):
        if supabase: supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Main Functional Tabs
# ─────────────────────────────────────────────
t1, t2 = st.tabs(["Analyze Video", "Pricing Plans"])

with t1:
    url = st.text_input("Enter YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    if st.button("Start Analysis →", use_container_width=True):
        if not url: st.error("Please enter a URL"); st.stop()
        if not st.session_state.user: st.error("Please sign in to analyze videos."); st.stop()
        
        vid_match = re.search(r"(?:v=|\/|be\/)([A-Za-z0-9_\-]{11})", url)
        vid = vid_match.group(1) if vid_match else None
        if not vid: st.error("Invalid YouTube URL"); st.stop()
        
        client = get_openai_client()
        if not client: st.error("AI Service Unavailable (Missing API Key)"); st.stop()
        
        with st.spinner("Analyzing..."):
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                ytt = YouTubeTranscriptApi()
                try: trans = ytt.fetch(vid, languages=['en', 'ko'])
                except: trans = ytt.fetch(vid)
                
                text = "\n".join([f"[{int(e['start']//60):02d}:{int(e['start']%60):02d}] {e['text']}" for e in trans])
                
                res_gpt = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "Extract 3 core concepts in English. JSON format."}, {"role": "user", "content": text[:10000]}],
                    response_format={"type": "json_object"}
                )
                gpt_data = json.loads(res_gpt.choices[0].message.content)
                st.session_state.analysis_results = gpt_data
                st.session_state.player_video_id = vid
                
                try:
                    from db import save_to_cache
                    save_to_cache(vid, gpt_data.get("concepts", []), text, len(trans), "00:00")
                except: pass
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    if st.session_state.analysis_results:
        r = st.session_state.analysis_results
        col1, col2 = st.columns(2)
        with col1:
            for i, c in enumerate(r.get("concepts", [])):
                st.markdown(f'<div style="background:#1A1A21; padding:1.2rem; border-radius:12px; border-left:4px solid #B19B72; margin-bottom:1rem;">'
                            f'<h4>{c.get("title", "Concept")}</h4><p style="font-size:0.9rem;">{c.get("summary", "")}</p></div>', unsafe_allow_html=True)
                if st.button(f"Jump to {c.get('timestamp','00:00')}", key=f"btn_{i}"):
                    ts_str = c.get('timestamp','00:00').split(':')
                    st.session_state.selected_ts = int(ts_str[0])*60 + int(ts_str[1])
                    st.rerun()
        with col2:
            embed = f"https://www.youtube.com/embed/{st.session_state.player_video_id}?start={st.session_state.selected_ts}&autoplay=1"
            st.markdown(f'<iframe width="100%" height="380" src="{embed}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen style="border-radius:12px;"></iframe>', unsafe_allow_html=True)

with t2:
    st.markdown("<center><h3>Pricing Plans</h3></center>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.info("**Free**\n\n$0/mo")
    with c2: st.success("**Pro**\n\n$14.99/mo")
    with c3: st.warning("**Yearly**\n\n$99/yr")

st.markdown("<center style='color:#6E6E7A; padding:2rem; font-size:0.8rem;'>© 2026 YouTube Core Concept Analyzer • Global v3.1 Stable</center>", unsafe_allow_html=True)
