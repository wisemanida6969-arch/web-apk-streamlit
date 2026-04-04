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
import time
from urllib.request import urlopen

# ── Import functional libraries ──
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from openai import OpenAI
    import db
except Exception as e:
    st.error(f"Initialization Error: {e}")

# ─────────────────────────────────────────────
#  Platinum UI Styling (v4.7 Functional Hub)
# ─────────────────────────────────────────────
def apply_platinum_design():
    """Injects high-end CSS for Hero, Analysis results, and Source Attribution."""
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
            
            /* 2. Hero Component */
            .hero-headline {
                font-size: 3.8rem !important;
                font-weight: 800 !important;
                color: #FFFFFF !important;
                text-align: center;
                background: linear-gradient(to bottom, #FFFFFF 0%, #94A3B8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-top: 4rem;
            }
            
            /* 3. Glowing Card & Logic Containers */
            .premium-card {
                background: rgba(30, 41, 59, 0.4);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
                padding: 2.5rem;
                margin-top: 2rem;
                box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            }

            /* 4. Results Section: Concepts */
            .concept-card {
                background: rgba(59, 130, 246, 0.05);
                border-left: 4px solid #3B82F6;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 8px;
            }
            .concept-title { color: #3B82F6; font-weight: 700; font-size: 1.2rem; margin-bottom: 0.5rem; }
            .concept-desc { color: #CBD5E1; font-size: 1rem; line-height: 1.6; }

            /* 5. Source Attribution Section */
            .attribution-box {
                margin-top: 4rem;
                padding-top: 2rem;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            .source-info { color: #FFFFFF; font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; }
            .fair-use-disclaimer { color: #64748B; font-size: 0.8rem; line-height: 1.5; margin-bottom: 1.5rem; max-width: 600px; }

            /* 6. Buttons */
            .stButton > button.glow-cta {
                background: linear-gradient(135deg, #FBBF24 0%, #D97706 100%) !important;
                color: #0F172A !important;
                font-weight: 700 !important;
                box-shadow: 0 0 20px rgba(251, 191, 36, 0.3) !important;
            }

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# ── Analysis Helpers ──
def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_video_metadata(video_id):
    """Fallback metadata scraper using oembed."""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        with urlopen(url) as response:
            data = json.loads(response.read().decode())
            return {"title": data.get("title", "Unknown Video"), "author": data.get("author_name", "Unknown Creator")}
    except:
        return {"title": "YouTube Video", "author": "Creator"}

# ── Routing & State ──
if "user" not in st.session_state: st.session_state.user = None
if "results" not in st.session_state: st.session_state.results = None
page = st.query_params.get("page", "home")

# ── Functional Logic Components ──────────────────────
import base64
import hashlib
import secrets

def generate_pkce_pair():
    """Manually generate PKCE verifier and challenge for maximum persistence control."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(digest).decode('utf-8').replace('=', '')
    return verifier, challenge

def get_supabase():
    """Initializes persistent Supabase client."""
    if "supabase" in st.session_state:
        return st.session_state.supabase
    try:
        from supabase import create_client
        u, k = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_ANON_KEY")
        if u and k:
            client = create_client(u, k)
            st.session_state.supabase = client
            return client
    except Exception as e:
        st.error(f"Supabase Init Error: {e}")
    return None

def handle_oauth_callback():
    """Handles the redirect from Google OAuth and sets the session with manual PKCE verifier."""
    code = st.query_params.get("code")
    if code and not st.session_state.user:
        supabase = get_supabase()
        if supabase:
            try:
                # Retrieve the manually stored verifier from session state
                verifier = st.session_state.get("pkce_verifier")
                if not verifier:
                    st.error("Security mismatch: PKCE verifier lost. Please try logging in again.")
                    return
                
                # Explicitly pass the verifier to solve the 'non-empty' error once and for all
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

def analyze_video(video_url):
    vid = extract_video_id(video_url)
    if not vid: return st.error("Invalid YouTube URL.")
    
    with st.spinner("🚀 Extracting intelligence from the timeline..."):
        try:
            # 1. Transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(vid, languages=['ko', 'en'])
            full_text = " ".join([t['text'] for t in transcript_list])
            
            # 2. OpenAI
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
            
            # 3. Metadata
            meta = get_video_metadata(vid)
            
            st.session_state.results = {
                "video_id": vid,
                "concepts": raw_data.get("concepts", []),
                "meta": meta
            }
            st.rerun()
        except Exception as e:
            st.error(f"Analysis failed: {e}")

# ─────────────────────────────────────────────
#  Main Execution Logic
# ─────────────────────────────────────────────
apply_platinum_design()
handle_oauth_callback()

if page == "terms":
    # ... (ToS logic shared before) ...
    st.markdown("<h1>Terms of Service</h1>", unsafe_allow_html=True)
    if st.button("Back home"): st.query_params.clear(); st.rerun()
elif page == "privacy":
    st.markdown("<h1>Privacy Policy</h1>", unsafe_allow_html=True)
    if st.button("Back home"): st.query_params.clear(); st.rerun()
else:
    # ── HOME PAGE ──
    if not st.session_state.user:
        # 1. Hero Section
        st.markdown('<h1 class="hero-headline">Gain Back Your Study Time.</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#94A3B8; font-size:1.4rem; margin-bottom:3rem;">AI-Powered YouTube Analysis for Efficient Learning. Stop Watching, Start Learning.</p>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown('<div class="premium-card" style="margin-top:-2rem; margin-bottom:2rem;">', unsafe_allow_html=True)
            st.markdown("<p style='color:#3B82F6; font-weight:600; margin-bottom:0.8rem; text-align:center;'>Paste YouTube URL to Begin Intelligence Extraction</p>", unsafe_allow_html=True)
            temp_url = st.text_input("", placeholder="https://youtube.com/watch?v=...", label_visibility="collapsed", key="unauth_url")
            
            if temp_url:
                st.warning("⚠️ Login required to analyze this video!")
            
            supabase = get_supabase()
            if supabase:
                try:
                    # Unified High-Performance Auth Button
                    if st.button("🚀 Analyze Now & Login with Google", use_container_width=True, type="primary"):
                        # 1. Generate & Persist Manual PKCE Pair
                        verifier, challenge = generate_pkce_pair()
                        st.session_state.pkce_verifier = verifier
                        
                        # 2. Request Auth URL with manual challenge injection
                        res = supabase.auth.sign_in_with_oauth({
                            "provider": "google", 
                            "options": {
                                "redirect_to": "https://trytimeback.com",
                                "flow_type": "pkce",
                                "code_challenge": challenge,
                                "code_challenge_method": "S256"
                            }
                        })
                        
                        if res.url:
                            st.session_state.temp_url = temp_url
                            st.markdown(f'<meta http-equiv="refresh" content="0;url={res.url}">', unsafe_allow_html=True)
                            st.stop()
                        else:
                            st.error("Auth server error. Please check your connection.")
                            
                    st.markdown("<p style='text-align:center; font-size:0.85rem; color:#64748B; margin-top:1rem;'>Intelligence access requires Google authentication.</p>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Security Engine Error: {e}")
            else:
                st.warning("🔒 Auth Server Offline.")
            st.markdown('</div>', unsafe_allow_html=True)

        # 2. Value Propositions (Why Trytimeback?)
        st.markdown("<div style='margin-top:8rem; text-align:center;'><h2 style='color:#FFFFFF; font-size:2.5rem; font-weight:700;'>Why Trytimeback?</h2></div>", unsafe_allow_html=True)
        
        v1, v2, v3 = st.columns(3)
        with v1:
            st.markdown("""
            <div class="premium-card" style="padding:2rem; min-height:280px; transition: 0.3s ease-in-out;">
                <div style="color:#3B82F6; font-size:2.5rem; margin-bottom:1rem;"><i class="fas fa-bolt"></i></div>
                <h3 style="color:#FFFFFF; font-size:1.4rem; margin-bottom:1rem;">1 Hour Video, 5 Minute Summary</h3>
                <p style="color:#94A3B8; font-size:1rem; line-height:1.6;">Don't waste time on long intros. Get deep insights in seconds with our optimized AI extraction.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with v2:
            st.markdown("""
            <div class="premium-card" style="padding:2rem; min-height:280px;">
                <div style="color:#FBBF24; font-size:2.5rem; margin-bottom:1rem;"><i class="fas fa-brain"></i></div>
                <h3 style="color:#FFFFFF; font-size:1.4rem; margin-bottom:1rem;">AI Extracts Core Concepts</h3>
                <p style="color:#94A3B8; font-size:1rem; line-height:1.6;">Our engine identifies non-obvious patterns and formulas, acting as your personal study assistant.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with v3:
            st.markdown("""
            <div class="premium-card" style="padding:2rem; min-height:280px;">
                <div style="color:#10B981; font-size:2.5rem; margin-bottom:1rem;"><i class="fas fa-globe"></i></div>
                <h3 style="color:#FFFFFF; font-size:1.4rem; margin-bottom:1rem;">High Accuracy Global Learning</h3>
                <p style="color:#94A3B8; font-size:1rem; line-height:1.6;">Language is no barrier. We support and summarize lectures from across the world with precision.</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # ── LOGGED IN: ANALYSIS HUB ──
        st.markdown(f'<h1 class="hero-headline" style="font-size:2.8rem !important; margin-top:2rem;">Intelligence Dashboard</h1>', unsafe_allow_html=True)
        st.markdown(f'<p style="text-align:center; color:#94A3B8; font-size:1.1rem; margin-bottom:2rem;">Welcome back, <b>{st.session_state.user["name"]}</b>. What would you like to master today?</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("<p style='color:#3B82F6; font-weight:600; margin-bottom:0.5rem;'>YouTube Intelligence Extraction</p>", unsafe_allow_html=True)
        yt_url = st.text_input("", placeholder="Paste the YouTube URL here to extract concepts...", label_visibility="collapsed")
        c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
        with c_btn2:
            if st.button("🚀 Analyze Now", use_container_width=True, type="primary"):
                analyze_video(yt_url)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.results:
            # Report display logic ...
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown(f"<h2 style='color:#FFFFFF; font-size:1.8rem; margin-bottom:2rem;'>Intelligence Report</h2>", unsafe_allow_html=True)
            res = st.session_state.results
            for c in res.get("concepts", []):
                st.markdown(f"""
                <div class="concept-card">
                    <div class="concept-title">{c.get('title', 'Core Concept')}</div>
                    <div class="concept-desc">{c.get('description', '')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Source Attribution Section (v4.7)
            meta = res.get("meta", {})
            st.markdown(f"""
            <div class="attribution-box">
                <div class="source-info">Source: {meta.get('title')} by {meta.get('author')}</div>
                <div class="fair-use-disclaimer">
                    This summary is created for educational purposes under Fair Use. All rights to the original content remain with the copyright holder.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button(f"📺 Watch Original Video", f"https://youtube.com/watch?v={res['video_id']}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ──
st.markdown("""
<div style="text-align:center; padding:4rem 2rem; border-top:1px solid rgba(255,255,255,0.05); margin-top:8rem;">
    <p style='color:#475569; font-size:0.85rem; margin-bottom:0.7rem;'>
        Trytimeback is an AI analysis tool for educational purposes. We do not own or store original video content.
    </p>
    <p style='color:#64748B; font-size:0.85rem;'>
        Contact: <a href="mailto:admin@trytimeback.com" style="color:#3B82F6;">admin@trytimeback.com</a> | 
        <a href="?page=terms" target="_self" style="color:#3B82F6; text-decoration:none;">Terms of Service</a> | 
        <a href="?page=privacy" target="_self" style="color:#3B82F6; text-decoration:none;">Privacy Policy</a>
    </p>
    <p style='color:#475569; font-size:0.75rem; margin-top:15px;'>
        © 2026 YouTube Insight Analyzer • PLATINUM GLOBAL ATOMIC v5.2
    </p>
</div>
""", unsafe_allow_html=True)

