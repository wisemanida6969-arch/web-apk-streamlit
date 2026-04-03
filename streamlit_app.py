import os
os.environ['TZ'] = 'UTC'

import streamlit as st
import re
import random
import json
from youtube_transcript_api import YouTubeTranscriptApi
try:
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
except ImportError:
    from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
from openai import OpenAI
from supabase import create_client, Client

from db import (
    get_cached, save_to_cache, is_db_connected, 
    get_daily_usage, increment_daily_usage,
    get_global_daily_cost, add_global_cost
)

# ─────────────────────────────────────────────
#  Global Settings & Roles
# ─────────────────────────────────────────────
ADMIN_EMAIL = "wisemanida6969@gmail.com"
DAILY_BUDGET_LIMIT = 10.0  # Daily total cost limit in USD
COST_PER_SUMMARY = 0.01    # Estimated cost per GPT-4o call

# ─────────────────────────────────────────────
#  i18n & Locale Loading
# ─────────────────────────────────────────────
def load_locale(lang):
    path = os.path.join("locales", f"{lang}.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

# Force English only
if "locale" not in st.session_state or st.session_state.locale != "en":
    st.session_state.locale = "en"

lang_data = load_locale("en")

def _(key, **kwargs):
    text = lang_data.get(key, key)
    # Hardcoded Fallbacks for crucial UI
    if key == "app_title": return "YouTube Core Concept Analyzer"
    if key == "btn_login_google": return "Sign in with Google"
    
    for k, v in kwargs.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text

# ─────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Core Concept Analyzer",
    page_icon="📜",
    layout="wide",
)

# ─────────────────────────────────────────────
#  Session State Initialization
# ─────────────────────────────────────────────
for key in ["analysis_results", "player_video_id", "selected_ts", "selected_poem", "user"]:
    if key not in st.session_state:
        st.session_state[key] = None
if st.session_state.selected_ts is None:
    st.session_state.selected_ts = 0

# Safe key retriever
def get_secret(key, default=""):
    try:
        env_val = os.environ.get(key)
        if env_val: return env_val.strip()
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except:
        pass
    return default

# Initialize Config
supabase_url = get_secret("SUPABASE_URL")
supabase_key = get_secret("SUPABASE_ANON_KEY")
api_key = get_secret("OPENAI_API_KEY")
supabase = None

# Validation helper (Strict)
def is_configured(val, placeholder="your-project-id"):
    if not val: return False
    if placeholder in val: return False
    if "sb_publishable_" in val: return False # Stripe key error detected
    if len(val) < 20: return False # Keys are usually longer
    return True

# Supabase Initialization
if is_configured(supabase_url) and is_configured(supabase_key, "anon_user"):
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # OAuth Callback
        if "code" in st.query_params:
            try:
                res = supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
                if res and res.user:
                    st.session_state.user = res.user
                    st.query_params.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"Authentication Handshake Failed: {e}")
                if st.button("Try Again"): st.rerun()

        # Session Persistence
        if not st.session_state.user:
            try:
                user_res = supabase.auth.get_user()
                if user_res and user_res.user:
                    st.session_state.user = user_res.user
            except:
                pass
    except Exception as e:
        st.warning(f"Supabase Connection Failed: {e}")
else:
    supabase = None

# ─────────────────────────────────────────────
#  Custom CSS (Always English)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; color: #E2E2E2; }
.stApp { background-color: #0F0F13; min-height: 100vh; }
.hero-header { text-align: center; padding: 2.8rem 1rem 1.6rem; border-bottom: 1px solid #23232A; margin-bottom: 2rem; }
.hero-header h1 { font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; color: #FFFFFF; }
.concept-card { background: #1A1A21; border-left: 5px solid #4F4F5C; border-radius: 14px; padding: 1.6rem 1.8rem; margin-bottom: 1rem; }
.concept-title { font-size: 1.13rem; font-weight: 700; color: #FFFFFF; }
.pricing-card { background: #1A1A21; border-radius: 16px; padding: 2.2rem 1.8rem; text-align: center; }
.pricing-card.best-value { border: 2px solid #B19B72; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Sidebar Diagnostics
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ System Settings")
    with st.expander("🔍 Debug Info", expanded=True):
        def mask_key(val):
            if not val: return "❌ Missing"
            if "sb_publishable_" in val: return "❌ WRONG KEY (Stripe detected!)"
            if len(val) < 20: return "⚠️ Invalid Format"
            return f"✅ {val[:6]}...{val[-4:]}"
        
        st.write(f"**OpenAI:** {mask_key(api_key)}")
        st.write(f"**Supabase URL:** {mask_key(supabase_url)}")
        st.write(f"**Supabase Anon:** {mask_key(supabase_key)}")
        if st.button("Sync Now"): st.rerun()

    if is_configured(api_key) and supabase:
        st.success("✅ System Ready")
    else:
        st.error("⚠️ Components Not Configured")

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

def analyze_with_gpt(timed_text, api_key):
    client = OpenAI(api_key=api_key)
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "Analyze video and respond ONLY in JSON. English only."}, {"role": "user", "content": timed_text[:12000]}],
        response_format={"type": "json_object"}
    )
    return json.loads(res.choices[0].message.content)

# ─────────────────────────────────────────────
#  Main UI
# ─────────────────────────────────────────────
try:
    st.markdown(f'<div class="hero-header"><h1>{_("app_title")} (v2.0)</h1><p>{_("app_desc")}</p></div>', unsafe_allow_html=True)

    if not st.session_state.user:
        if supabase:
            try:
                redirect_url = get_secret("REDIRECT_URL", "https://trytimeback.com")
                res = supabase.auth.sign_in_with_oauth({"provider": "google", "options": {"redirect_to": redirect_url}})
                col1, col2, col3 = st.columns([1,2,1])
                with col2: st.link_button(f"🌐 {_('btn_login_google')}", res.url, use_container_width=True)
            except:
                st.error("Google Auth failed. Check dashboard settings.")
        else:
            if "sb_publishable_" in str(supabase_key):
                st.error("🚨 ERROR: You entered a STRIPE key instead of a SUPABASE key. Please visit Supabase Dashboard -> Settings -> API -> anon public key.")
            else:
                st.warning("Login currently unavailable.")
    else:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown(f"<center>👤 {st.session_state.user.email}</center>", unsafe_allow_html=True)
            if st.button(_("btn_logout")):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()

    tab1, tab2 = st.tabs([_("tab_home"), _("tab_pricing")])

    with tab1:
        url_input = st.text_input("Enter YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("Start Analysis →", use_container_width=True):
            if not is_configured(api_key): st.error("API Key missing"); st.stop()
            if supabase and not st.session_state.user: st.error("Login required"); st.stop()
            vid = extract_video_id(url_input)
            if not vid: st.error("Invalid URL"); st.stop()
            
            with st.spinner("Analyzing..."):
                ytt = YouTubeTranscriptApi()
                transcript = ytt.fetch(vid, languages=['en'])
                text = "\n".join([f"[{seconds_to_mmss(e['start'])}] {e['text']}" for e in transcript])
                gpt_res = analyze_with_gpt(text, api_key)
                st.session_state.analysis_results = gpt_res
                st.session_state.player_video_id = vid
                st.rerun()

        if st.session_state.analysis_results:
            res = st.session_state.analysis_results
            col_l, col_r = st.columns(2)
            with col_l:
                for i, c in enumerate(res.get("concepts", [])):
                    st.markdown(f'<div class="concept-card"><div class="concept-title">{c["title"]}</div><p>{c["summary"]}</p></div>', unsafe_allow_html=True)
                    if st.button(f"Play from {c['timestamp']}", key=f"btn_{i}"):
                        ts = c['timestamp'].split(':')
                        st.session_state.selected_ts = int(ts[0])*60 + int(ts[1])
                        st.rerun()
            with col_r:
                embed_url = f"https://www.youtube.com/embed/{st.session_state.player_video_id}?start={st.session_state.selected_ts}&autoplay=1"
                st.markdown(f'<iframe width="100%" height="400" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>', unsafe_allow_html=True)

    with tab2:
        col_f, col_m, col_y = st.columns(3)
        with col_f: st.markdown('<div class="pricing-card"><h3>Free</h3><h2>$0</h2><p>3 daily summaries</p></div>', unsafe_allow_html=True)
        with col_m: st.markdown('<div class="pricing-card"><h3>Monthly</h3><h2>$14.99</h2><p>Unlimited access</p></div>', unsafe_allow_html=True)
        with col_y: st.markdown('<div class="pricing-card best-value"><h3>Yearly</h3><h2>$99</h2><p>Best value</p></div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Unexpected Error: {e}")
    if st.button("Click to Restart App"):
        st.session_state.clear()
        st.rerun()

st.markdown("<center>© 2026 YouTube Core Concept Analyzer</center>", unsafe_allow_html=True)
