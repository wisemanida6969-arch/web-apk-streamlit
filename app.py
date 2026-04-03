import os
os.environ['TZ'] = 'UTC'
 
import streamlit as st
import re
import random
import json
import urllib.request
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
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

# Force English as the default and only language for this globalized version
st.session_state.locale = "en"
lang_data = load_locale(st.session_state.locale)

def _(key, **kwargs):
    text = lang_data.get(key, key)
    for k, v in kwargs.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text

# ─────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title=_("page_title"),
    page_icon="📜",
    layout="wide",
)

# ─────────────────────────────────────────────
#  Session State Initialization & Supabase Auth
# ─────────────────────────────────────────────
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "player_video_id" not in st.session_state:
    st.session_state.player_video_id = None
if "selected_ts" not in st.session_state:
    st.session_state.selected_ts = 0
if "selected_poem" not in st.session_state:
    st.session_state.selected_poem = None
if "user" not in st.session_state:
    st.session_state.user = None

# Safe key retriever (works even if st.secrets file is missing)
def get_secret(key, default=""):
    try:
        # Check environment first (most reliable on server)
        env_val = os.environ.get(key)
        if env_val: return env_val.strip()
        # Check st.secrets only if it exists
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

# Validation helper
def is_configured(val, placeholder="your-project-id"):
    return bool(val) and placeholder not in val and "여기에" not in val

if is_configured(supabase_url) and is_configured(supabase_key, "anon_public"):
    try:
        supabase = create_client(supabase_url, supabase_key)

        # Intercept OAuth Callback
        if "code" in st.query_params:
            try:
                res = supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
                st.session_state.user = res.user
            except Exception as e:
                st.error(f"Auth Error: {e}")
            finally:
                st.query_params.clear()
                st.rerun()

        # Check for existing session
        if not st.session_state.user:
            try:
                session = supabase.auth.get_session()
                if session:
                    st.session_state.user = session.user
            except:
                pass
    except Exception as e:
        st.warning(f"Supabase Connection Failed: {e}")
else:
    supabase = None

# ─────────────────────────────────────────────
#  Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    color: #E2E2E2;
}

.stApp {
    background-color: #0F0F13;
    background-image:
        radial-gradient(ellipse at 15% 40%, rgba(177,155,114,0.05) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 15%, rgba(60,60,75,0.15) 0%, transparent 55%);
    min-height: 100vh;
}

.hero-header {
    text-align: center;
    padding: 2.8rem 1rem 1.6rem;
    border-bottom: 1px solid #23232A;
    margin-bottom: 2rem;
}
.hero-brand {
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.28em;
    color: #B19B72;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.hero-header h1 {
    font-family: 'Outfit', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.01em;
    margin-bottom: 0.5rem;
    line-height: 1.3;
}
.hero-header p {
    color: #A0A0A9;
    font-size: 0.97rem;
    letter-spacing: 0.03em;
}

.glass-card {
    background: rgba(26, 26, 33, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid #32323D;
    border-radius: 20px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.4rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}

.concept-card {
    background: #1A1A21;
    border: 1px solid #32323D;
    border-left: 5px solid #4F4F5C;
    border-radius: 14px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1rem;
    transition: all 0.25s ease;
}
.concept-card:hover {
    box-shadow: 0 4px 18px rgba(0,0,0,0.3);
    border-left-color: #B19B72;
}
.concept-number {
    font-size: 0.70rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: #B19B72;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}
.concept-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.13rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 0.5rem;
}
.concept-summary {
    font-size: 0.92rem;
    color: #C0C0C8;
    line-height: 1.85;
}

.pricing-card {
    background: #1A1A21;
    border: 1px solid #32323D;
    border-radius: 16px;
    padding: 2.2rem 1.8rem;
    margin-bottom: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
}
.pricing-card.best-value {
    background: linear-gradient(180deg, #23232A 0%, #1A1A21 100%);
    border: 2px solid #B19B72;
    box-shadow: 0 8px 30px rgba(177,155,114,0.15);
}
.pricing-badge {
    position: absolute;
    top: -12px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(90deg, #D4AF37, #B19B72);
    color: #0F0F13;
    font-size: 0.75rem;
    font-weight: 800;
    padding: 0.3rem 1rem;
    border-radius: 20px;
    letter-spacing: 0.1em;
    box-shadow: 0 4px 10px rgba(177,155,114,0.4);
    white-space: nowrap;
}
.pricing-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 0.8rem;
}
.pricing-price {
    font-size: 2.2rem;
    font-weight: 800;
    color: #E2E2E2;
    margin-bottom: 1rem;
}

.exam-card {
    background: #1A1A21;
    border: 1px solid #32323D;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.exam-source-badge {
    display: inline-block;
    background: rgba(177,155,114,0.12);
    border: 1px solid #B19B72;
    border-radius: 4px;
    padding: 0.18rem 0.55rem;
    font-size: 0.75rem;
    font-weight: 700;
    color: #B19B72;
    margin-bottom: 0.75rem;
}
.exam-choice {
    padding: 0.35rem 0.6rem;
    border-radius: 6px;
    font-size: 0.9rem;
    color: #A0A0A9;
    margin-bottom: 0.3rem;
    border: 1px solid #2A2A33;
}
.exam-choice.correct {
    border-color: #22C55E;
    background: rgba(34,197,94,0.08);
    color: #86EFAC;
}

.poem-card {
    background: #1A1A21; border: 1px solid #32323D;
    border-top: 2px solid #B19B72; border-radius: 4px; padding: 2.2rem 2.8rem;
    text-align: center;
}
.poem-text { font-family: 'Nanum Myeongjo', serif; font-size: 1.05rem; color: #FFFFFF; line-height: 2.3; white-space: pre-line; }

/* ── Streamlit UI Fixes ── */
.stTextInput > div > div > input {
    background: #131318 !important; border: 1.5px solid #32323D !important; border-radius: 12px !important; color: #FFFFFF !important;
}
.stButton > button {
    background: #2A2A33 !important; color: #FFFFFF !important; border: 1px solid #4F4F5C !important; border-radius: 50px !important; transition: all 0.3s ease !important; width: 100%;
}
.stButton > button:hover {
    background: #B19B72 !important; color: #0F0F13 !important; border-color: #B19B72 !important; transform: translateY(-2px) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Sidebar & Admin Dashboard
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"### ⚙️ {_('sidebar_settings')}")
    
    # System Diagnostics (Developer View)
    with st.expander("🔍 System Status", expanded=True):
        st.write("Checking if environment variables are loaded...")
        
        def mask_key(val):
            if not val or len(val) < 8: return "❌ Missing"
            # Explicit check for placeholder text
            if any(p in val for p in ["your-project-id", "실제_키", "여기에", "your-anon-key"]):
                return "⚠️ Placeholder Detected (Check Secrets)"
            return f"✅ {val[:6]}...{val[-4:]}"

        # Source detection
        def get_source(key_name):
            if os.environ.get(key_name): return "🌐 (Env Var)"
            try:
                if key_name in st.secrets: return "📁 (Secrets.toml)"
            except: pass
            return ""

        st.markdown(f"**OpenAI API:** {mask_key(api_key)} {get_source('OPENAI_API_KEY')}")
        st.markdown(f"**Supabase URL:** {mask_key(supabase_url)} {get_source('SUPABASE_URL')}")
        st.markdown(f"**Supabase Anon:** {mask_key(supabase_key)} {get_source('SUPABASE_ANON_KEY')}")
        
        if st.button("🔄 Sync Check"):
            st.rerun()

    st.markdown("---")
    if is_configured(api_key, "실제_키") and supabase:
        st.success(_("sidebar_service_active"))
    else:
        st.error(_("sidebar_key_err"))

    user_email = st.session_state.user.email if st.session_state.user else ""
    if user_email == ADMIN_EMAIL:
        current_cost = get_global_daily_cost()
        st.markdown(f"""
<div style="background:rgba(177,155,114,0.1); border:1px solid #B19B72; border-radius:10px; padding:1rem; margin-top:2rem;">
    <div style="font-size:0.7rem; color:#B19B72; font-weight:700; margin-bottom:0.5rem; letter-spacing:0.1em;">ADMIN DASHBOARD</div>
    <div style="font-size:1.2rem; font-weight:800; color:#FFFFFF;">${current_cost:.2f} / ${DAILY_BUDGET_LIMIT}</div>
    <div style="font-size:0.75rem; color:#A0A0A9; margin-top:0.4rem;">Today's Global Spend</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def extract_video_id(url: str) -> str | None:
    patterns = [r"v=([A-Za-z0-9_\-]{11})", r"youtu\.be/([A-Za-z0-9_\-]{11})", r"shorts/([A-Za-z0-9_\-]{11})"]
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return None

def seconds_to_mmss(seconds: float) -> str:
    s = int(seconds)
    m, sec = divmod(s % 3600, 60)
    h = s // 3600
    return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

def get_transcript(video_id: str):
    ytt = YouTubeTranscriptApi()
    try:
        return ytt.fetch(video_id, languages=[st.session_state.locale, "en"])
    except:
        return ytt.fetch(video_id)

def build_timed_text(transcript) -> str:
    lines = []
    for e in transcript:
        ts = seconds_to_mmss(e["start"])
        clean_text = e['text'].replace('\n',' ')
        lines.append(f"[{ts}] {clean_text}")
    return "\n".join(lines)

def analyze_with_gpt(timed_text: str, api_key: str) -> dict:
    client = OpenAI(api_key=api_key)
    system_prompt = """You are an expert video analyzer. Respond ONLY in pure JSON.
Forcing language: English only.
Structure: {"keywords": [], "concepts": [{"number":1, "title":"", "summary":"", "timestamp":"MM:SS"}]}"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": timed_text[:12000]}],
        temperature=0.3, response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def fetch_exam_questions(keywords: list[str]) -> list[dict]:
    if not supabase or not keywords: return []
    try:
        res = supabase.table("exam_questions").select("*").overlaps("keywords", keywords).limit(3).execute()
        return res.data or []
    except: return []

def render_youtube_player(video_id: str, start_time: int):
    embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1"
    st.markdown(f'<iframe width="100%" height="400" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Main UI
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
#  Main UI with Global Error Handler
# ─────────────────────────────────────────────
try:
    st.markdown(f"""
    <div class="hero-header">
        <h1>{_("app_title")}</h1>
        <p>{_("app_desc")}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="glass-card" style="text-align:center;">', unsafe_allow_html=True)
    if not st.session_state.user:
        if supabase:
            try:
                # IMPORTANT: redirect_to must match your settings in Supabase dashboard
                redirect_url = st.secrets.get("REDIRECT_URL", "https://trytimeback.com")
                res = supabase.auth.sign_in_with_oauth({
                    "provider": "google", 
                    "options": {"redirect_to": redirect_url}
                })
                st.link_button(f"🌐 {_('btn_login_google')}", res.url, use_container_width=True)
            except Exception as e:
                st.error(f"Login button error: {e}")
                st.info("Please check if your Supabase URL and Key are correct in secrets.toml")
        else:
            st.warning("Login is disabled (Supabase not configured)")
    else:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown(f"<p>{st.session_state.user.email}</p>", unsafe_allow_html=True)
            if st.button(_("btn_logout")):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs([_("tab_home"), _("tab_pricing")])

    with tab1:
        url_input = st.text_input(_("input_url_label"), placeholder="YouTube URL...")
        analyze_btn = st.button(_("btn_start_analysis"), use_container_width=True)

        def show_paywall():
            st.warning("Daily Limit Reached (3/3)")
            st.link_button("Upgrade Now", "https://stripe.com/", use_container_width=True)

        if analyze_btn:
            # Check OpenAI Key first
            if not is_configured(api_key, "실제_키"):
                st.error("OpenAI API Key is missing or invalid. Please set it in Railway Variables.")
                st.stop()

            # Optional Login: If Supabase is configured, require login. Otherwise, use Guest Mode (SQLite).
            if supabase and not st.session_state.user:
                st.error("Login required to use cloud features."); st.stop()
            
            vid = extract_video_id(url_input)
            if not vid: st.error("Invalid URL"); st.stop()
            
            is_admin = (st.session_state.user.email == ADMIN_EMAIL) if st.session_state.user else False
            cached = None
            if supabase:
                try:
                    res_c = supabase.table("video_summaries").select("*").eq("video_id", vid).maybe_single().execute()
                    cached = res_c.data
                except: pass
            
            # If not in cloud cache, check local cache (SQLite)
            if not cached:
                cached_local = get_cached(vid)
                if cached_local:
                    cached = cached_local
                    st.info("Loaded from Local Cache")
            
            if not cached and not is_admin:
                if get_global_daily_cost() >= DAILY_BUDGET_LIMIT: st.error("Budget exceeded"); st.stop()
                current_usage = get_daily_usage(st.session_state.user.id if st.session_state.user else "guest")
                if current_usage >= 3: show_paywall(); st.stop()

            if cached:
                st.success("Loaded from Global Cache")
                res_data = cached
            else:
                with st.spinner("Analyzing..."):
                    transcript = get_transcript(vid)
                    timed_text = build_timed_text(transcript)
                    gpt_res = analyze_with_gpt(timed_text, api_key)
                    res_data = {
                        "video_id": vid, "concepts": gpt_res["concepts"], "keywords": gpt_res["keywords"],
                        "timed_text": timed_text, "total_entries": len(transcript), "duration": seconds_to_mmss(transcript[-1]["start"])
                    }
                    add_global_cost(COST_PER_SUMMARY)
                    increment_daily_usage(st.session_state.user.id if st.session_state.user else "guest")
                    
                    # Save to Cloud if available
                    if supabase:
                        try:
                            supabase.table("video_summaries").upsert(res_data).execute()
                        except: pass
                    
                    # ALWAYS save to Local Cache (SQLite) for fallback
                    save_to_cache(
                        vid, res_data["concepts"], res_data["timed_text"], 
                        res_data["total_entries"], res_data["duration"]
                    )
            
            st.session_state.analysis_results = res_data
            st.session_state.player_video_id = vid
            st.session_state.selected_ts = 0
            quotes = lang_data.get("quotes", [])
            st.session_state.selected_poem = random.choice(quotes) if quotes else None

        if st.session_state.analysis_results:
            r = st.session_state.analysis_results
            col_l, col_r = st.columns(2)
            with col_l:
                for i, c in enumerate(r["concepts"]):
                    st.markdown(f"""<div class="concept-card"><div class="concept-number">CONCEPT {c['number']}</div><div class="concept-title">{c['title']}</div><div class="concept-summary">{c['summary']}</div></div>""", unsafe_allow_html=True)
                    if st.button(f"Play from {c['timestamp']}", key=f"p_{i}"):
                        ts = c['timestamp'].split(':')
                        st.session_state.selected_ts = int(ts[0])*60 + int(ts[1])
                        st.rerun()
            with col_r:
                render_youtube_player(r["video_id"], st.session_state.selected_ts)
            
            questions = fetch_exam_questions(r["keywords"])
            if questions:
                st.markdown("### 📚 Related Exam Questions")
                for q in questions:
                    st.markdown(f"""<div class="exam-card"><div class="exam-source-badge">{q['source']}</div><div>{q['question_text']}</div></div>""", unsafe_allow_html=True)
            
            if st.session_state.selected_poem:
                p = st.session_state.selected_poem
                st.markdown(f"""<div class="poem-card"><div class="poem-text">{p['text']}</div><div style="color:#A0A0A9;">— {p['author']}</div></div>""", unsafe_allow_html=True)

    with tab2:
        col_f, col_m, col_y = st.columns(3)
        with col_f:
            st.markdown(f"""
                <div class="pricing-card">
                    <div class="pricing-title">{_("pricing_free_title")}</div>
                    <div class="pricing-price">{_("pricing_free_price")}</div>
                    <div class="pricing-desc">{_("pricing_free_desc")}</div>
                </div>
            """, unsafe_allow_html=True)
        with col_m:
            st.markdown(f"""
                <div class="pricing-card">
                    <div class="pricing-title">{_("pricing_monthly_title")}</div>
                    <div class="pricing-price">{_("pricing_monthly_price")}</div>
                    <div class="pricing-desc">{_("pricing_monthly_desc")}</div>
                    <button style="background:#B19B72; color:#0F0F13; border:none; border-radius:50px; padding:0.5rem 1rem; width:100%; font-weight:700; cursor:pointer;">{_("btn_upgrade_now")}</button>
                </div>
            """, unsafe_allow_html=True)
        with col_y:
            st.markdown(f"""
                <div class="pricing-card best-value">
                    <div class="pricing-badge">{_("pricing_best_value")}</div>
                    <div class="pricing-title">{_("pricing_yearly_title")}</div>
                    <div class="pricing-price">{_("pricing_yearly_price")}</div>
                    <div class="pricing-desc">{_("pricing_yearly_desc")}</div>
                    <button style="background:#B19B72; color:#0F0F13; border:none; border-radius:50px; padding:0.5rem 1rem; width:100%; font-weight:700; cursor:pointer;">{_("btn_upgrade_now")}</button>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<p style='text-align:center; color:#6E6E7A; padding:2rem;'>© 2026 YouTube Core Concept Analyzer</p>", unsafe_allow_html=True)

except Exception as e:
    st.markdown(f"""
    <div class="glass-card" style="border-color: #ef4444; background: rgba(239, 68, 68, 0.05);">
        <h2 style="color: #ef4444; margin-top: 0;">{_("err_unexpected")}</h2>
        <p style="color: #A0A0A9;">{_("err_details")}<code>{str(e)}</code></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(_("btn_restart_app")):
        # Clear only relevant non-auth state to allow fresh start
        keys_to_clear = ["analysis_results", "player_video_id", "selected_ts", "selected_poem"]
        for k in keys_to_clear:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
