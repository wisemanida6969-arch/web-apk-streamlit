import os
os.environ['TZ'] = 'UTC'

# ── SHIELD: Purge proxy env vars ─────────────────────
for env_key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if env_key in os.environ:
        del os.environ[env_key]

import streamlit as st
import re
import random
import json
import time
import base64
import hashlib
import secrets
from urllib.request import urlopen

# ── Import functional libraries ──────────────────────
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from openai import OpenAI
    import db
except Exception as e:
    st.error(f"Initialization Error: {e}")

# ── Global Configuration ──────────────────────────────
REDIRECT_URI = "https://trytimeback.com/auth/callback"
STORAGE_KEY = "sb-trytimeback-auth"  # Standardized for localStorage compatibility

# ─────────────────────────────────────────────────────
#  Functional Logic Components (v5.5 Atomic Fix)
# ─────────────────────────────────────────────────────

class StreamlitSessionStorage:
    """Robust storage for Supabase session using st.session_state (v6.0)."""
    def __init__(self, key=STORAGE_KEY):
        self.key = key
    def get_item(self, key): 
        return st.session_state.get(f"{self.key}-{key}")
    def set_item(self, key, value): 
        st.session_state[f"{self.key}-{key}"] = value
    def remove_item(self, key): 
        if f"{self.key}-{key}" in st.session_state: 
            del st.session_state[f"{self.key}-{key}"]

# PKCE Generation removed (v6.0 Transition to Standard/Implicit Flow)

def get_supabase():
    """Initializes persistent Supabase client (v6.0 Standard Flow)."""
    if "supabase" in st.session_state:
        return st.session_state.supabase
    try:
        from supabase import create_client
        u, k = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")
        if u and k:
            # v6.3: Direct initialization for universal support.
            client = create_client(u, k)
            st.session_state.supabase = client
            return client
    except Exception as e:
        st.error(f"Supabase Connection Error: {e}")
    return None

def handle_oauth_callback():
    """Handles OAuth redirect and session exchange (v6.3 Robust Implicit Fix)."""
    # Tokens are passed as query params after the JS Bridge reloads the page
    st_access = st.query_params.get("st_access_token")
    st_refresh = st.query_params.get("st_refresh_token")
    
    if not st.session_state.user:
        supabase = get_supabase()
        if supabase:
            # First, check for existing persistent session in st.session_state
            try:
                user_res = supabase.auth.get_user()
                if user_res and user_res.user:
                    st.session_state.user = {
                        "id": user_res.user.id,
                        "email": user_res.user.email,
                        "name": user_res.user.user_metadata.get("full_name", "Learner")
                    }
                    st.query_params.clear(); st.rerun()
            except: pass

            # Handle Implicit Token (Redirected from JS Bridge / ?st_access_token=...)
            if st_access:
                try:
                    res = supabase.auth.set_session(st_access, st_refresh or "")
                    if res.user:
                        st.session_state.user = {
                            "id": res.user.id, "email": res.user.email,
                            "name": res.user.user_metadata.get("full_name", "Learner")
                        }
                        st.query_params.clear(); st.rerun()
                except Exception as e:
                    st.error(f"Session recovery error: {e}")

# ── Analysis Helpers ─────────────────────────────────

def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_video_metadata(video_id):
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        with urlopen(url) as response:
            data = json.loads(response.read().decode())
            return {"title": data.get("title", "YouTube Video"), "author": data.get("author_name", "Creator")}
    except:
        return {"title": "YouTube Video", "author": "Creator"}

def analyze_video(video_url):
    vid = extract_video_id(video_url)
    if not vid: return st.error("Invalid YouTube URL.")
    
    with st.spinner("🚀 Extracting intelligence from the timeline..."):
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(vid, languages=['ko', 'en'])
            full_text = " ".join([t['text'] for t in transcript_list])
            
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a master learning strategist. Extract 3 core concepts from the transcript. For each, give a TITLE and a 2-sentence DEEP EXPLANATION in English."},
                    {"role": "user", "content": f"Analyze this transcript: {full_text[:6000]}"}
                ],
                response_format={ "type": "json_object" }
            )
            raw_data = json.loads(response.choices[0].message.content)
            meta = get_video_metadata(vid)
            
            st.session_state.results = {
                "video_id": vid,
                "concepts": raw_data.get("concepts", []),
                "meta": meta
            }
            st.rerun()
        except Exception as e:
            st.error(f"Analysis failed: {e}")

# ─────────────────────────────────────────────────────
#  Platinum UI Styling (v5.5 Functional Hub)
# ─────────────────────────────────────────────────────

def apply_platinum_design():
    st.markdown("""
        <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
            html, body, [class*="css"] { font-family: 'Inter', 'Pretendard', sans-serif !important; color: #F8FAFC !important; }
            .main { background: linear-gradient(180deg, #0F172A 0%, #020617 100%) !important; }
            .hero-headline { font-size: 3.8rem !important; font-weight: 800 !important; color: #FFFFFF !important; text-align: center; background: linear-gradient(to bottom, #FFFFFF 0%, #94A3B8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 4rem; }
            .premium-card { background: rgba(30, 41, 59, 0.4); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 2.5rem; margin-top: 2rem; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
            .concept-card { background: rgba(59, 130, 246, 0.05); border-left: 4px solid #3B82F6; padding: 1.5rem; margin-bottom: 1.5rem; border-radius: 8px; }
            .concept-title { color: #3B82F6; font-weight: 700; font-size: 1.2rem; margin-bottom: 0.5rem; }
            .concept-desc { color: #CBD5E1; font-size: 1rem; line-height: 1.6; }
            .attribution-box { margin-top: 4rem; padding-top: 2rem; border-top: 1px solid rgba(255, 255, 255, 0.1); }
            .source-info { color: #FFFFFF; font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; }
            .fair-use-disclaimer { color: #64748B; font-size: 0.8rem; line-height: 1.5; margin-bottom: 1.5rem; max-width: 600px; }
            #MainMenu, footer, header {visibility: hidden;}
        </style>
        <script>
            // v6.3 Simple Implicit Bridge: Handle #fragment and localStorage
            (function() {
                const hash = window.location.hash;
                const urlParams = new URLSearchParams(window.location.search);
                
                // 1. If we have fragments (from Supabase redirect)
                if (hash && hash.includes("access_token")) {
                    const params = new URLSearchParams(hash.replace("#", "?"));
                    const access = params.get("access_token");
                    const refresh = params.get("refresh_token");
                    
                    if (access) {
                        // Persist to localStorage for stability
                        localStorage.setItem('sb-trytimeback-access', access);
                        if (refresh) localStorage.setItem('sb-trytimeback-refresh', refresh);
                        
                        // Redirect to main page without the fragment
                        window.location.href = window.location.origin + window.location.pathname + "?st_access_token=" + access;
                    }
                }
                
                // 2. Persistent Login Check: If Python doesn't have the token but localStorage does
                if (!urlParams.get("st_access_token") && localStorage.getItem('sb-trytimeback-access')) {
                    // Short-circuit: If we are on the main page, feed the token back to Python
                    const savedToken = localStorage.getItem('sb-trytimeback-access');
                    const savedRefresh = localStorage.getItem('sb-trytimeback-refresh') || '';
                    if (savedToken && window.location.search === '') {
                        window.location.href = window.location.origin + window.location.pathname + 
                            "?st_access_token=" + savedToken + "&st_refresh_token=" + savedRefresh;
                    }
                }
            })();
        </script>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
#  Main Application Execution
# ─────────────────────────────────────────────────────

if "user" not in st.session_state: st.session_state.user = None
if "results" not in st.session_state: st.session_state.results = None
page = st.query_params.get("page", "home")

apply_platinum_design()
handle_oauth_callback()

if page == "terms":
    st.markdown("<h1 style='text-align:center; color:#FFFFFF; margin-top:4rem;'>Terms of Service</h1>", unsafe_allow_html=True)
    st.markdown('<div class="premium-card"><h3>1. Nature of Service</h3><p>Trytimeback provides AI analysis of YouTube content.</p><h3>2. Intellectual Property</h3><p>Original rights remain with creators.</p></div>', unsafe_allow_html=True)
    if st.button("← Back to Home", use_container_width=True): st.query_params.clear(); st.rerun()

elif page == "privacy":
    st.markdown("<h1 style='text-align:center; color:#FFFFFF; margin-top:4rem;'>Privacy Policy</h1>", unsafe_allow_html=True)
    st.markdown('<div class="premium-card"><h3>1. Data Use</h3><p>We use Google OAuth for authentication only.</p><h3>2. Security</h3><p>Your data is protected by industry-standard encryption.</p></div>', unsafe_allow_html=True)
    if st.button("← Back to Home", use_container_width=True): st.query_params.clear(); st.rerun()

else:
    if not st.session_state.user:
        # ── HERO & UNAUTH SECTION ──
        st.markdown('<h1 class="hero-headline">Gain Back Your Study Time.</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#94A3B8; font-size:1.4rem; margin-bottom:3rem;">AI-Powered YouTube Analysis for Efficient Learning.</p>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown("<p style='color:#3B82F6; font-weight:600; margin-bottom:0.8rem; text-align:center;'>Paste YouTube URL to Begin</p>", unsafe_allow_html=True)
            temp_url = st.text_input("", placeholder="https://youtube.com/watch?v=...", label_visibility="collapsed", key="unauth_input")
            
            if temp_url: st.warning("⚠️ Login required to analyze this video!")
            
            u, k = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")
            if u and k:
                if st.button("🚀 Analyze Now & Login with Google", use_container_width=True, type="primary"):
                    # v6.3: HARD REMOVAL of SDK initiation to prevent PKCE enforcement.
                    # Manually construct Implicit Flow URL.
                    res_url = f"{u}/auth/v1/authorize?provider=google&redirect_to={REDIRECT_URI}"
                    st.session_state.temp_url = temp_url
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={res_url}">', unsafe_allow_html=True)
                    st.stop()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Props section
        st.markdown("<div style='margin-top:8rem; text-align:center;'><h2 style='color:#FFFFFF; font-size:2.5rem; font-weight:700;'>Why Trytimeback?</h2></div>", unsafe_allow_html=True)
        v1, v2, v3 = st.columns(3)
        with v1:
            st.markdown('<div class="premium-card" style="padding:2rem; min-height:280px;"><div style="color:#3B82F6; font-size:2.5rem; margin-bottom:1rem;"><i class="fas fa-bolt"></i></div><h3 style="color:#FFFFFF; font-size:1.4rem; margin-bottom:1rem;">1 Hour Video, 5 Min Summary</h3><p style="color:#94A3B8; font-size:1rem; line-height:1.6;">Don\'t waste time on long intros. Get deep insights in seconds with AI.</p></div>', unsafe_allow_html=True)
        with v2:
            st.markdown('<div class="premium-card" style="padding:2rem; min-height:280px;"><div style="color:#FBBF24; font-size:2.5rem; margin-bottom:1rem;"><i class="fas fa-brain"></i></div><h3 style="color:#FFFFFF; font-size:1.4rem; margin-bottom:1rem;">AI Core Concept Extraction</h3><p style="color:#94A3B8; font-size:1rem; line-height:1.6;">Identifying non-obvious patterns and acting as your study assistant.</p></div>', unsafe_allow_html=True)
        with v3:
            st.markdown('<div class="premium-card" style="padding:2rem; min-height:280px;"><div style="color:#10B981; font-size:2.5rem; margin-bottom:1rem;"><i class="fas fa-globe"></i></div><h3 style="color:#FFFFFF; font-size:1.4rem; margin-bottom:1rem;">High Accuracy Global Learning</h3><p style="color:#94A3B8; font-size:1rem; line-height:1.6;">Precise summaries from lectures across the world in any language.</p></div>', unsafe_allow_html=True)

    else:
        # ── AUTHENTICATED DASHBOARD ──
        st.markdown(f'<h1 class="hero-headline" style="font-size:2.8rem !important; margin-top:2rem;">Intelligence Dashboard</h1>', unsafe_allow_html=True)
        st.markdown(f'<p style="text-align:center; color:#94A3B8; font-size:1.1rem; margin-bottom:2rem;">Welcome back, <b>{st.session_state.user["name"]}</b>.</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        yt_url = st.text_input("", placeholder="Paste link here...", label_visibility="collapsed")
        if st.button("🚀 Analyze Now", use_container_width=True, type="primary"):
            analyze_video(yt_url)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.results:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            res = st.session_state.results
            for c in res.get("concepts", []):
                st.markdown(f'<div class="concept-card"><div class="concept-title">{c.get("title")}</div><div class="concept-desc">{c.get("description")}</div></div>', unsafe_allow_html=True)
            meta = res.get("meta", {})
            st.markdown(f'<div class="attribution-box"><div class="source-info">Source: {meta.get("title")} by {meta.get("author")}</div></div>', unsafe_allow_html=True)
            st.link_button(f"📺 Watch Original Video", f"https://youtube.com/watch?v={res['video_id']}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ── Global Footer ────────────────────────────────────
st.markdown(f"""
<div style="background-color: #0F172A; padding: 4rem 4rem 2rem 4rem; border-top: 1px solid rgba(255,255,255,0.08); margin-top: 8rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 2rem; margin-bottom: 3rem; width: 100%;">
        <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 500; text-align: left; flex: 1;">
            Copyright © 2026 <span style="color: #FFFFFF;">Trytimeback.</span> All rights reserved.
        </div>
        <div style="display: flex; gap: 2.5rem; flex-wrap: wrap;">
            <a href="mailto:admin@trytimeback.com" style="color: #64748B; text-decoration: none; font-size: 0.85rem; transition: color 0.3s; font-weight: 500;">
                <i class="fas fa-envelope" style="margin-right: 0.5rem;"></i>admin@trytimeback.com
            </a>
            <a href="?page=terms" target="_self" style="color: #64748B; text-decoration: none; font-size: 0.85rem; transition: color 0.3s; font-weight: 500;">
                <i class="fas fa-file-contract" style="margin-right: 0.5rem;"></i>Terms of Service
            </a>
            <a href="?page=privacy" target="_self" style="color: #64748B; text-decoration: none; font-size: 0.85rem; transition: color 0.3s; font-weight: 500;">
                <i class="fas fa-shield-halved" style="margin-right: 0.5rem;"></i>Privacy Policy
            </a>
        </div>
    </div>
    <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 2rem; text-align: center;">
        <p style="color: #475569; font-size: 0.75rem; line-height: 1.6; max-width: 800px; margin: 0 auto;">
            Trytimeback does not own the original video content. All rights belong to the creators. 
            This service is for educational purposes only.
        </p>
        <p style="margin-top: 1.5rem; color: #334155; font-size: 0.65rem; letter-spacing: 0.1rem; text-transform: uppercase;">
            GLOBAL STABLE v6.3 (IMPLICIT ENGINE)
        </p>
    </div>
</div>
<style>
    a:hover {{ color: #3B82F6 !important; }}
</style>
""", unsafe_allow_html=True)
