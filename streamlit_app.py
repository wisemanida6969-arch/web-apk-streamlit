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
        if key and "실제_키" not in key:
            return OpenAI(api_key=key)
    except: pass
    return None

# ─────────────────────────────────────────────
#  Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Core Concept Analyzer",
    page_icon="📜",
    layout="wide",
)

# ── Force Session State ──
if "user" not in st.session_state: st.session_state.user = None
if "analysis_results" not in st.session_state: st.session_state.analysis_results = None
if "player_video_id" not in st.session_state: st.session_state.player_video_id = None
if "selected_ts" not in st.session_state: st.session_state.selected_ts = 0

# ─────────────────────────────────────────────
#  Logic Section: OAuth Callback Handling (Improved v3.2.1)
# ─────────────────────────────────────────────
supabase = get_supabase_client()

if supabase:
    # 1. Capture code from URL
    if "code" in st.query_params:
        with st.spinner("🔏 Verifying Google Session..."):
            auth_code = st.query_params["code"]
            try:
                res = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
                if res and res.user:
                    st.session_state.user = res.user
                    st.query_params.clear()
                    st.toast(f"Welcome back, {res.user.email}!", icon="👋")
                    st.rerun()
                else:
                    st.error("Authentication failed: Code exchange did not return a user.")
            except Exception as e:
                st.error(f"Login failed: {e}")

    # 2. Persistence Check
    if not st.session_state.user:
        try:
            user_res = supabase.auth.get_user()
            if user_res and user_res.user:
                st.session_state.user = user_res.user
        except: pass

# ── UI Header ──
st.warning("⚠️ GLOBAL VERSION (v3.2.1) - LOGIN FEEDBACK ENABLED")
st.markdown('<div style="text-align:center; padding:1.5rem 0; border-bottom:1px solid #23232A; margin-bottom:2rem;">'
            '<h1 style="font-size:2rem; color:white; margin-bottom:0.4rem;">YouTube Core Concept Analyzer</h1>'
            '<p style="color:#B19B72; font-weight: 500;">Premium Insight Engine</p></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Authentication UI
# ─────────────────────────────────────────────
st.markdown('<div style="background:rgba(26,26,33,0.5); padding:2rem; border-radius:16px; border:1px solid #32323D; text-align:center; margin-bottom:2rem;">', unsafe_allow_html=True)

if not st.session_state.user:
    if supabase:
        try:
            # Base URL auto-detection fallback
            base_url = "https://trytimeback.com"
            res = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": base_url,
                    "skip_browser_redirect": False
                }
            })
            if res and hasattr(res, 'url'):
                st.link_button("🚀 Sign in with Google Account", res.url, use_container_width=True)
                st.markdown("<small style='color:#A0A0A9;'>Access your custom dashboard and unlimited summaries.</small>", unsafe_allow_html=True)
            else:
                st.error("Initialization failed. Please refresh.")
        except Exception as e:
            st.error(f"UI Error: {e}")
    else:
        st.error("🔑 API CONFIG MISSING. Sign-in disabled.")
else:
    st.markdown(f"👤 Account: **{st.session_state.user.email}**", unsafe_allow_html=True)
    if st.button("Logout from System", use_container_width=True):
        if supabase: supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Main Functional Tabs
# ─────────────────────────────────────────────
t1, t2 = st.tabs(["Analyze Video", "Pricing Plans"])

with t1:
    url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    if st.button("Start Analysis →", use_container_width=True):
        if not url: st.error("Please enter a URL"); st.stop()
        if not st.session_state.user: st.error("Please sign in to analyze."); st.stop()
        
        vid_match = re.search(r"(?:v=|\/|be\/)([A-Za-z0-9_\-]{11})", url)
        vid = vid_match.group(1) if vid_match else None
        if not vid: st.error("Invalid URL format"); st.stop()
        
        client = get_openai_client()
        if not client: st.error("AI Service Offline"); st.stop()
        
        with st.spinner("Extracting insights..."):
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                ytt = YouTubeTranscriptApi()
                try: trans = ytt.fetch(vid, languages=['en', 'ko'])
                except: trans = ytt.fetch(vid)
                
                text = "\n".join([f"[{int(e['start']//60):02d}:{int(e['start']%60):02d}] {e['text']}" for e in trans])
                
                res_gpt = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "Extract 3 core concepts in English. Format: JSON."}, {"role": "user", "content": text[:10000]}],
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
                st.error(f"Processing Error: {e}")

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
    st.markdown("<center><h3>Plans & Billing</h3></center>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.info("**Free Tier**\n\n$0/mo")
    with c2: st.success("**Pro Tier**\n\n$14.99/mo")
    with c3: st.warning("**Enterprise**\n\n$99/yr")

st.markdown("<center style='color:#6E6E7A; padding:2rem; font-size:0.8rem;'>© 2026 YouTube Core Concept Analyzer • v3.2.1 Stable Build</center>", unsafe_allow_html=True)
