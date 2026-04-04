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
REDIRECT_URI = "https://trytimeback.com"

# ─────────────────────────────────────────────────────
#  Functional Logic Components (v5.5 Atomic Fix)
# ─────────────────────────────────────────────────────

class StreamlitSessionStorage:
    """Custom storage for Supabase PKCE flow using st.session_state (v5.5)."""
    def __init__(self, key="sb-auth-token"):
        self.key = key
    def get_item(self, key): 
        return st.session_state.get(f"{self.key}-{key}")
    def set_item(self, key, value): 
        st.session_state[f"{self.key}-{key}"] = value
    def remove_item(self, key): 
        if f"{self.key}-{key}" in st.session_state: 
            del st.session_state[f"{self.key}-{key}"]

def generate_pkce_pair():
    """Manually generate PKCE verifier and challenge for maximum persistence control."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(digest).decode('utf-8').replace('=', '')
    return verifier, challenge

def get_supabase():
    """Initializes persistent Supabase client (v5.5 - Fixes storage_key init crash)."""
    if "supabase" in st.session_state:
        return st.session_state.supabase
    try:
        from supabase import create_client, ClientOptions
        u, k = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")
        if u and k:
            # v5.5: REMOVED storage_key as it causes crash in Python SyncClientOptions
            opts = ClientOptions(
                persist_session=True,
                storage=StreamlitSessionStorage(key="sb-auth-token")
            )
            client = create_client(u, k, options=opts)
            st.session_state.supabase = client
            return client
    except Exception as e:
        st.error(f"Supabase Connection Error: {e}")
    return None

def handle_oauth_callback():
    """Handles OAuth redirect and session exchange with verifier recovery."""
    code = st.query_params.get("code")
    if code and not st.session_state.user:
        supabase = get_supabase()
        if supabase:
            try:
                # Recover verifier from session (Manual or Storage key compatible)
                verifier = st.session_state.get("pkce_verifier") or \
                           st.session_state.get("sb-auth-token-pkce_verifier")
                
                if not verifier:
                    st.error("Security mismatch: PKCE verifier lost. Please try logging in again.")
                    return
                
                res = supabase.auth.exchange_code_for_session({
                    "auth_code": code,
                    "code_verifier": verifier
                })
                if res.user:
                    st.session_state.user = {
                        "id": res.user.id,
                        "email": res.user.email,
                        "name": res.user.user_metadata.get("full_name", "Learner")
                    }
                    st.query_params.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"Session exchange failed: {e}")
                if st.button("❌ Authentication Error: Try Again"):
                    st.query_params.clear(); st.rerun()

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
            
            supabase = get_supabase()
            if supabase:
                if st.button("🚀 Analyze Now & Login with Google", use_container_width=True, type="primary"):
                    verifier, challenge = generate_pkce_pair()
                    st.session_state.pkce_verifier = verifier
                    st.session_state["sb-auth-token-pkce_verifier"] = verifier
                    res = supabase.auth.sign_in_with_oauth({
                        "provider": "google", 
                        "options": {
                            "redirect_to": REDIRECT_URI,
                            "flow_type": "pkce",
                            "code_challenge": challenge,
                            "code_challenge_method": "S256"
                        }
                    })
                    if res.url:
                        st.session_state.temp_url = temp_url
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={res.url}">', unsafe_allow_html=True)
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
<div style="text-align:center; padding:4rem 2rem; border-top:1px solid rgba(255,255,255,0.05); margin-top:8rem;">
    <p style='color:#64748B; font-size:0.85rem;'>
        Contact: <a href="mailto:admin@trytimeback.com" style="color:#3B82F6;">admin@trytimeback.com</a> | 
        <a href="?page=terms" target="_self" style="color:#3B82F6; text-decoration:none;">Terms of Service</a> | 
        <a href="?page=privacy" target="_self" style="color:#3B82F6; text-decoration:none;">Privacy Policy</a>
    </p>
    <p style='color:#475569; font-size:0.75rem; margin-top:15px;'>
        © 2026 YouTube Insight Analyzer • PLATINUM GLOBAL ATOMIC v5.5
    </p>
</div>
""", unsafe_allow_html=True)
