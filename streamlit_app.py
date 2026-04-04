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
#  Premium UI Styling (v4.0 Modern & Premium)
# ─────────────────────────────────────────────
def apply_premium_design():
    """Injects high-end CSS for a Modern & Premium look."""
    st.markdown("""
        <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" />
        <style>
            /* 1. Global Typography & Background */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', 'Pretendard', sans-serif !important;
                letter-spacing: 0.01em !important;
                color: #F8FAFC !important;
            }
            
            /* Deep Navy Background Overrides */
            .main {
                background: linear-gradient(180deg, #0F172A 0%, #111111 100%) !important;
            }
            
            /* 2. Glassmorphism Card Style */
            [data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
                /* background: rgba(30, 41, 59, 0.4); 
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 0.5rem; */
            }
            
            .premium-card {
                background: rgba(30, 41, 59, 0.4);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
                padding: 1.8rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            }
            
            .premium-card:hover {
                border: 1px solid rgba(59, 130, 246, 0.3);
                transform: translateY(-2px);
            }
            
            /* 3. Point Colors (Blue & Gold) */
            h1, h2, h3 {
                color: #FFFFFF !important;
                font-weight: 700 !important;
                letter-spacing: -0.02em !important;
            }
            
            .blue-accent { color: #3B82F6; font-weight: 600; }
            .gold-accent { color: #FBBF24; font-weight: 700; }
            
            /* 4. Refined Buttons */
            .stButton > button {
                background: linear-gradient(90deg, #3B82F6 0%, #2563EB 100%) !important;
                color: white !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 0.6rem 1.5rem !important;
                font-weight: 600 !important;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
                box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.3) !important;
            }
            
            .stButton > button:hover {
                transform: scale(1.02) !important;
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4) !important;
            }
            
            /* 5. Custom Tabs Styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2rem;
                background-color: transparent !important;
            }
            .stTabs [data-baseweb="tab"] {
                color: #94A3B8 !important;
                padding: 1rem 0 !important;
                font-weight: 500 !important;
            }
            .stTabs [aria-selected="true"] {
                color: #3B82F6 !important;
                border-bottom: 2px solid #3B82F6 !important;
            }

            /* Hide Streamlit components for a cleaner look */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

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
        if key and "your-api-key" not in key:
            return OpenAI(api_key=key)
    except: pass
    return None

# ─────────────────────────────────────────────
#  Main Execution
# ─────────────────────────────────────────────
apply_premium_design()

# ── Header Section ──
st.markdown("""
<div style="text-align:center; padding:3rem 0;">
    <h1 style="font-size:3rem; margin-bottom:0.5rem;">YouTube <span class="blue-accent">Insight</span> Analyzer</h1>
    <p style="color:#94A3B8; font-size:1.1rem; letter-spacing:0.05em;">AI-DRIVEN CORE CONCEPT EXTRACTION CENTER</p>
</div>
""", unsafe_allow_html=True)

# ── Force Session State ──
if "user" not in st.session_state: st.session_state.user = None
if "analysis_results" not in st.session_state: st.session_state.analysis_results = None
if "player_video_id" not in st.session_state: st.session_state.player_video_id = None
if "selected_ts" not in st.session_state: st.session_state.selected_ts = 0

supabase = get_supabase_client()

# ─────────────────────────────────────────────
#  Authentication UI
# ─────────────────────────────────────────────
st.markdown('<div class="premium-card">', unsafe_allow_html=True)

if not st.session_state.user:
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
                    st.link_button("🚀 Access via Google Premium Auth", res.url, use_container_width=True)
                st.markdown("<center style='color:#64748B; margin-top:1rem;'>Secure one-click access for global professionals.</center>", unsafe_allow_html=True)
            else:
                st.error("Protocol Error: Check Supabase Dashboard.")
        except Exception as e:
            st.error(f"UI Component Error: {e}")
    else:
        st.error("Infrastructure Offline: Set SUPABASE_URL in Railway.")
else:
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown(f"Verified Professional: <span class='blue-accent'>{st.session_state.user.email}</span>", unsafe_allow_html=True)
    with c2:
        if st.button("Terminate Session", use_container_width=True):
            if supabase: supabase.auth.sign_out()
            st.session_state.user = None
            st.query_params.clear()
            st.rerun()

# Handle OAuth Callback
if "code" in st.query_params and not st.session_state.user:
    try:
        with st.spinner("🔒 Establishing Secure Link..."):
            res = supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
            if res and res.user:
                st.session_state.user = res.user
                st.query_params.clear()
                st.rerun()
    except:
        st.info("Authentication context established. Please refresh if login doesn't complete.")

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Functional Modules
# ─────────────────────────────────────────────
t1, t2 = st.tabs(["[ 💡 Core Analysis ]", "[ 💎 Premium Plans ]"])

with t1:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        url = st.text_input("Enter Targeted YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("Execute Strategic Analysis →", use_container_width=True):
            if not url: st.error("Target URL required."); st.stop()
            if not st.session_state.user: st.error("Verification Required: Please sign in."); st.stop()
            
            vid_match = re.search(r"(?:v=|\/|be\/)([A-Za-z0-9_\-]{11})", url)
            vid = vid_match.group(1) if vid_match else None
            if not vid: st.error("Target identification failed: Invalid URL."); st.stop()
            
            client = get_openai_client()
            if not client: st.error("AI Neural Network Unavailable."); st.stop()
            
            with st.spinner("Synthesizing core concepts..."):
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi
                    ytt = YouTubeTranscriptApi()
                    try: trans = ytt.fetch(vid, languages=['en', 'ko'])
                    except: trans = ytt.fetch(vid)
                    
                    lines = []
                    for e in trans:
                        mm, ss = int(e['start'] // 60), int(e['start'] % 60)
                        lines.append(f"[{mm:02d}:{ss:02d}] {e['text']}")
                    text = "\n".join(lines)
                    
                    res_gpt = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "system", "content": "Analyze and extract 3 core concepts in English. Format: JSON."}, {"role": "user", "content": text[:10000]}],
                        response_format={"type": "json_object"}
                    )
                    gpt_data = json.loads(res_gpt.choices[0].message.content)
                    st.session_state.analysis_results = gpt_data
                    st.session_state.player_video_id = vid
                    st.rerun()
                except Exception as e:
                    st.error(f"Execution Error: {e}")

    if st.session_state.analysis_results:
        st.markdown("<br><hr style='border-color:rgba(255,255,255,0.05)'><br>", unsafe_allow_html=True)
        r = st.session_state.analysis_results
        col1, col2 = st.columns([1, 1.2])
        
        with col1:
            st.markdown("<h3 class='gold-accent'>Strategic Insights</h3>", unsafe_allow_html=True)
            for i, c in enumerate(r.get("concepts", [])):
                st.markdown(f"""
                <div class="premium-card" style="padding:1.2rem; margin-bottom:1rem; border-left:4px solid #FBBF24;">
                    <h4 style="margin-bottom:0.3rem;">{c.get("title", "Concept")}</h4>
                    <p style="color:#94A3B8; font-size:0.9rem; line-height:1.5;">{c.get("summary", "")}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"NAVIGATE TO {c.get('timestamp','00:00')}", key=f"btn_{i}"):
                    ts_str = c.get('timestamp','00:00').split(':')
                    st.session_state.selected_ts = int(ts_str[0])*60 + int(ts_str[1])
                    st.rerun()
        
        with col2:
            st.markdown("<h3 class='blue-accent'>Contextual Player</h3>", unsafe_allow_html=True)
            embed = f"https://www.youtube.com/embed/{st.session_state.player_video_id}?start={st.session_state.selected_ts}&autoplay=1"
            st.markdown(f"""
            <div style="border-radius:24px; overflow:hidden; border:1px solid rgba(255,255,255,0.1); box-shadow:0 20px 40px rgba(0,0,0,0.4);">
                <iframe width="100%" height="420" src="{embed}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            </div>
            """, unsafe_allow_html=True)

with t2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<center><h2 class='gold-accent'>Elevate Your Content Strategy</h2><p style='color:#94A3B8'>Choose the tier that matches your professional ambition.</p></center>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="premium-card">
            <h4 class='blue-accent'>BASIC</h4>
            <h2 style='margin:0.5rem 0;'>$0 <small style='font-size:1rem; color:#64748B;'>/ mo</small></h2>
            <ul style='color:#94A3B8; font-size:0.9rem; padding-left:1rem;'>
                <li>5 Daily Credits</li>
                <li>Standard Support</li>
                <li>Core Summaries</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="premium-card" style="border: 1px solid rgba(59, 130, 246, 0.4); box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);">
            <h4 class='gold-accent'>PROFESSIONAL</h4>
            <h2 style='margin:0.5rem 0;'>$14.99 <small style='font-size:1rem; color:#64748B;'>/ mo</small></h2>
            <ul style='color:#94A3B8; font-size:0.9rem; padding-left:1rem;'>
                <li>Unlimited Credits</li>
                <li>Prioritized Neural Processing</li>
                <li>Strategic Insight Cards</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="premium-card">
            <h4 style='color:#F8FAFC;'>ENTERPRISE</h4>
            <h2 style='margin:0.5rem 0;'>$99 <small style='font-size:1rem; color:#64748B;'>/ yr</small></h2>
            <ul style='color:#94A3B8; font-size:0.9rem; padding-left:1rem;'>
                <li>Multi-user Access</li>
                <li>Custom Neural Models</li>
                <li>Dedicated Account Manager</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; padding:4rem 2rem; border-top:1px solid rgba(255,255,255,0.05); margin-top:2rem;">
    <p style='color:#475569; font-size:0.8rem; letter-spacing:0.1em;'>© 2026 YouTube Insight Analyzer • GLOBAL RELEASE v4.0 PLATINUM</p>
</div>
""", unsafe_allow_html=True)
