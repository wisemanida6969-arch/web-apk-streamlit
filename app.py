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

from db import get_cached, save_to_cache, is_db_connected, get_daily_usage, increment_daily_usage

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

if "locale" not in st.session_state:
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
#  Session state 초기화 & Supabase Auth 로직
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

supabase_url = st.secrets.get("SUPABASE_URL", "")
supabase_key = st.secrets.get("SUPABASE_ANON_KEY", "")
supabase = None

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)

    # OAuth Callback 가로채기
    if "code" in st.query_params:
        try:
            res = supabase.auth.exchange_code_for_session({"auth_code": st.query_params["code"]})
            st.session_state.user = res.user
        except Exception as e:
            st.error(f"Auth Error: {e}")
        finally:
            st.query_params.clear()
            st.rerun()

    # 이미 세션이 있는지 확인 (토큰 유효성 검사 등 필요하다면 추가)
    if not st.session_state.user:
        try:
            session = supabase.auth.get_session()
            if session:
                st.session_state.user = session.user
        except:
            pass

# ─────────────────────────────────────────────
#  Custom CSS  — 🌟 세월은간다 미니멀 다크 모드
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Noto+Serif+KR:wght@300;400;500;600&display=swap');

/* ── 기본 타이포그래피 ── */
html, body, [class*="css"] {
    font-family: 'Noto Serif KR', 'Nanum Myeongjo', serif;
    color: #E2E2E2;
}

/* ── 배경 ── */
.stApp {
    background-color: #0F0F13;
    background-image:
        radial-gradient(ellipse at 15% 40%, rgba(177,155,114,0.05) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 15%, rgba(60,60,75,0.15) 0%, transparent 55%);
    min-height: 100vh;
}

/* ── 상단 헤더 ── */
.hero-header {
    text-align: center;
    padding: 2.8rem 1rem 1.6rem;
    border-bottom: 1px solid #23232A;
    margin-bottom: 2rem;
}
.hero-brand {
    font-family: 'Nanum Myeongjo', serif;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.28em;
    color: #B19B72;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.hero-header h1 {
    font-family: 'Nanum Myeongjo', serif;
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

/* ── 트렌디한 애니메이션 설정 ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}
.hero-header, [data-testid="stImage"], .glass-card {
    animation: fadeInUp 0.8s ease-out forwards;
}

/* ── 메인 이미지 커스텀 테두리 ── */
[data-testid="stImage"] {
    display: flex;
    justify-content: center;
    margin-bottom: 2rem;
}
[data-testid="stImage"] img {
    border-radius: 20px !important;
    box-shadow: 0 12px 35px rgba(0,0,0,0.4) !important;
    max-height: 400px;
    object-fit: cover;
    width: 100%;
}

/* ── 유리 카드 → 다크 마이크로 카드 ── */
.glass-card {
    background: rgba(26, 26, 33, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid #32323D;
    border-radius: 20px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.4rem;
    box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}

/* ── 개념 카드 ── */
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
    font-family: 'Nanum Myeongjo', serif;
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

/* ── 타임스탬프 배지 ── */
.timestamp-badge {
    display: inline-block;
    background: #23232A;
    border: 1px solid #3B3B46;
    border-radius: 3px;
    padding: 0.18rem 0.55rem;
    font-size: 0.80rem;
    font-weight: 600;
    color: #D2D2D7;
    font-family: 'Courier New', monospace;
}

/* ── 구분선 ── */
hr { border-color: #32323D !important; }

/* ── 섹션 제목 ── */
h2, h3 {
    font-family: 'Nanum Myeongjo', serif !important;
    color: #FFFFFF !important;
    letter-spacing: -0.01em !important;
}

/* ── 입력창 (필 라운드) ── */
.stTextInput > div > div > input {
    background: #131318 !important;
    border: 1.5px solid #32323D !important;
    border-radius: 12px !important;
    color: #FFFFFF !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input::placeholder { color: #6E6E7A !important; }
.stTextInput > div > div > input:focus {
    border-color: #B19B72 !important;
    box-shadow: 0 0 0 2px rgba(177,155,114,0.15) !important;
}
.stTextInput > label {
    color: #A0A0A9 !important;
    font-weight: 500 !important;
}

/* ── 버튼 (골드 아웃라인/솔리드 믹스) ── */
.stButton > button {
    background: #2A2A33 !important;
    color: #FFFFFF !important;
    border: 1px solid #4F4F5C !important;
    border-radius: 50px !important;
    font-family: 'Noto Serif KR', serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 0.7rem 2rem !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    width: 100%;
}
.stButton > button:hover {
    background: #B19B72 !important;
    color: #0F0F13 !important;
    border-color: #B19B72 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(177,155,114,0.3) !important;
}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: #14141A !important;
    border-right: 1px solid #23232A !important;
}
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: #1C1C23 !important;
}
section[data-testid="stSidebar"] * {
    color: #D2D2D7 !important;
}

/* ── Alert / 알림 ── */
.stAlert {
    background: #1A1A21 !important;
    border: 1px solid #32323D !important;
    color: #E2E2E2 !important;
}

/* ── 성공 메시지 ── */
[data-testid="stNotification"] {
    background: #23232A !important;
    border: 1px solid #3B3B46 !important;
    color: #FFFFFF !important;
}

/* ── 스피너 ── */
.stSpinner > div { color: #B19B72 !important; }

/* ── 시 블록 ── */
.poem-section { margin-top: 3rem; padding: 0 0 2rem; text-align: center; }
.poem-divider { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
.poem-divider-line { flex: 1; height: 1px; background: linear-gradient(to right, transparent, #3B3B46, transparent); }
.poem-divider-icon { color: #8B7355; font-size: 1rem; }
.poem-card {
    display: inline-block; max-width: 560px;
    background: #1A1A21; border: 1px solid #32323D;
    border-top: 2px solid #B19B72; border-radius: 4px; padding: 2.2rem 2.8rem;
}
.poem-label { font-size: 0.68rem; color: #B19B72;text-transform: uppercase; margin-bottom: 1.2rem; }
.poem-text { font-family: 'Nanum Myeongjo', serif; font-size: 1.05rem; color: #FFFFFF; line-height: 2.3; white-space: pre-line; text-align: center; }
.poem-author { font-size: 0.82rem; color: #A0A0A9; margin-top: 1.4rem; font-style: italic; }
.poem-footer { margin-top: 2.5rem; font-size: 0.80rem; color: #6E6E7A; }

/* ── Markdown 텍스트 (명시적 하얀색 보호) ── */
.stMarkdown p, .stMarkdown div, .stMarkdown span { color: #E2E2E2 !important; }

/* ── 커스텀 탭 모바일 최적화 ── */
div[data-testid="stTabs"] {
    margin-bottom: 2rem;
}
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    flex: 1;
    background: #1A1A21 !important;
    border: 1px solid #32323D !important;
    border-radius: 8px !important;
    margin: 0 4px !important;
    padding: 0.8rem 0 !important;
    color: #A0A0A9 !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background: #23232A !important;
    color: #FFFFFF !important;
    border-color: #B19B72 !important;
    box-shadow: 0 4px 15px rgba(177,155,114,0.1) !important;
}
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] { display: none !important; }

/* ── Pricing 카테고리 ── */
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
    font-family: 'Nanum Myeongjo', serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 0.8rem;
}
.pricing-price {
    font-size: 2.5rem;
    font-weight: 800;
    color: #E2E2E2;
    margin-bottom: 1rem;
    font-family: 'Courier New', monospace;
}
.price-mo {
    font-size: 1rem;
    color: #6E6E7A;
    font-weight: 500;
}
.pricing-desc {
    font-size: 1rem;
    color: #A0A0A9;
    margin-bottom: 2rem;
    line-height: 1.5;
}

/* ── 기출문제 카드 ── */
.exam-section-header {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin: 2rem 0 1.2rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid #32323D;
}
.exam-section-title {
    font-family: 'Nanum Myeongjo', serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #FFFFFF;
}
.exam-keyword-chip {
    display: inline-block;
    background: #23232A;
    border: 1px solid #3B3B46;
    border-radius: 20px;
    padding: 0.2rem 0.65rem;
    font-size: 0.78rem;
    color: #B19B72;
    font-weight: 600;
    margin: 0.2rem 0.2rem 0.2rem 0;
}
.exam-card {
    background: #1A1A21;
    border: 1px solid #32323D;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    position: relative;
    transition: border-color 0.2s ease;
}
.exam-card:hover { border-color: #4F4F5C; }
.exam-source-badge {
    display: inline-block;
    background: rgba(177,155,114,0.12);
    border: 1px solid #B19B72;
    border-radius: 4px;
    padding: 0.18rem 0.55rem;
    font-size: 0.75rem;
    font-weight: 700;
    color: #B19B72;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
}
.exam-question-text {
    font-size: 0.97rem;
    color: #E2E2E2;
    line-height: 1.7;
    margin-bottom: 0.8rem;
}
.exam-choices {
    list-style: none;
    padding: 0;
    margin: 0 0 0.8rem;
}
.exam-choices li {
    padding: 0.35rem 0.6rem;
    border-radius: 6px;
    font-size: 0.9rem;
    color: #A0A0A9;
    margin-bottom: 0.3rem;
    border: 1px solid #2A2A33;
}
.exam-choices li.correct {
    border-color: #22C55E;
    background: rgba(34,197,94,0.08);
    color: #86EFAC;
    font-weight: 600;
}
.exam-type-ox {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 700;
    color: #6E6E7A;
    margin-bottom: 0.5rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  서버사이드 API 키 로드 (사용자에게 노출 안 됨)
#  우선순위: st.secrets → 환경변수 OPENAI_API_KEY
# ─────────────────────────────────────────────
api_key: str = (
    st.secrets.get("OPENAI_API_KEY", "")
    or os.environ.get("OPENAI_API_KEY", "")
)


# ─────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    language = st.selectbox(
        "Language / 언어 / Idioma",
        ["en", "ko", "es"],
        index=["en", "ko", "es"].index(st.session_state.locale),
        format_func=lambda x: {"en": "English", "ko": "한국어", "es": "Español"}[x],
        key="locale_selector"
    )
    if language != st.session_state.locale:
        st.session_state.locale = language
        st.rerun()
        
    st.markdown("---")

    # Service status
    db_status = _("sidebar_db_conn") if is_db_connected() else _("sidebar_db_disconn")
    
    if api_key:
        st.markdown(f"""
<div style="
    background:#F5F0E6;
    border:1px solid #C8B89A;
    border-left:3px solid #2C2013;
    border-radius:4px;
    padding:0.7rem 1rem;
    margin-bottom:1rem;
">
    <span style="font-size:0.68rem;letter-spacing:0.16em;color:#8B7355;font-weight:700;">{_("sidebar_status_title")}</span><br>
    <span style="font-size:0.88rem;color:#2C2013;font-family:'Noto Serif KR',serif;">
        {_("sidebar_service_active")}<br>
        {db_status}
    </span>
</div>
""", unsafe_allow_html=True)
    else:
        st.error(_("sidebar_key_err"))
        
    st.markdown("---")
    st.markdown(_("sidebar_how_to"))
    st.markdown("")
    st.markdown(_("sidebar_languages"))
    st.markdown("")
    st.markdown(_("sidebar_model"))
    st.markdown("---")
    st.caption("Seworeunganda · Powered by GPT-4o")


# ─────────────────────────────────────────────
#  Helper 함수들
# ─────────────────────────────────────────────

def get_youtube_metadata(video_id: str) -> dict:
    """YouTube oEmbed API를 사용하여 채널명과 URL 추출"""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {"channel_name": data.get("author_name", "YouTube Channel"), "channel_url": data.get("author_url", "")}
    except Exception:
        return {"channel_name": "YouTube Channel", "channel_url": f"https://www.youtube.com/watch?v={video_id}"}


def render_youtube_player(video_id: str, start_time: int, end_time: int = None):
    """
    유튜브 공식 IFrame API를 사용한 영상 플레이어 렌더링.
    원본 영상의 조회수와 광고가 유지되도록 공식 임베드 URL(embed)을 이용함.
    영상 하단에 원본 채널명과 유튜브로 이동하는 버튼 자동 생성.
    """
    metadata = get_youtube_metadata(video_id)
    channel_name = metadata.get("channel_name", "YouTube Channel")
    
    embed_url = f"https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=1&rel=0&modestbranding=1"
    if end_time:
        embed_url += f"&end={end_time}"

    # 영상 플레이어 (IFrame)
    st.markdown(f"""
    <div style="
        position: relative;
        padding-bottom: 56.25%;
        height: 0;
        overflow: hidden;
        border-radius: 6px;
        border: 1px solid #D9D0BE;
        box-shadow: 0 4px 20px rgba(44,32,19,0.12);
        margin-top: 0.5rem;
    ">
        <iframe
            src="{embed_url}"
            style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;"
            allow="autoplay; encrypted-media; picture-in-picture"
            allowfullscreen
        ></iframe>
    </div>
    """, unsafe_allow_html=True)
    
    # 하단 채널명 및 이동 버튼
    youtube_link = f"https://www.youtube.com/watch?v={video_id}&t={start_time}s"
    st.markdown(f"""
    <div style="display:flex; justify-content: space-between; align-items: center; margin-top: 0.8rem; padding: 0.6rem 1rem; background: #FFFDF8; border-radius: 8px; border: 1px solid #EBE4D6;">
        <div style="font-weight: 600; color: #4A3728; font-family: 'Noto Serif KR', serif; display:flex; align-items:center; gap:0.5rem; font-size: 0.95rem;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#8B7355"><path d="M21.582 6.186a2.532 2.532 0 0 0-1.784-1.784C18.225 4 12 4 12 4s-6.225 0-7.798.402a2.532 2.532 0 0 0-1.784 1.784C2 7.76 2 12 2 12s0 4.24.418 5.814a2.532 2.532 0 0 0 1.784 1.784C5.775 20 12 20 12 20s6.225 0 7.798-.402a2.532 2.532 0 0 0 1.784-1.784C22 16.24 22 12 22 12s0-4.24-.418-5.814zM9.99 15.474v-6.948l6.16 3.474-6.16 3.474z"/></svg>
            <span>{channel_name}</span>
        </div>
        <a href="{youtube_link}" target="_blank" style="text-decoration: none; font-size: 0.85rem; font-weight: 600; color: #DC2626; background: #FEE2E2; padding: 0.4rem 0.9rem; border-radius: 5px; transition: all 0.2s;">
            {_("btn_youtube_watch")}
        </a>
    </div>
    """, unsafe_allow_html=True)




def extract_video_id(url: str) -> str | None:
    """YouTube URL에서 video ID 추출"""
    patterns = [
        r"(?:v=)([A-Za-z0-9_\-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_\-]{11})",
        r"(?:shorts/)([A-Za-z0-9_\-]{11})",
        r"(?:embed/)([A-Za-z0-9_\-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def seconds_to_mmss(seconds: float) -> str:
    """초를 MM:SS 또는 HH:MM:SS 형식으로 변환"""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def get_transcript(video_id: str):
    """Fetch transcript dynamically based on UI locale"""
    ytt = YouTubeTranscriptApi()
    locale = st.session_state.locale
    try:
        try:
            return ytt.fetch(video_id, languages=[locale])
        except Exception:
            pass
        if locale != "en":
            try:
                return ytt.fetch(video_id, languages=["en"])
            except Exception:
                pass
        return ytt.fetch(video_id)
    except Exception as e:
        err = str(e)
        if "disabled" in err.lower() or "no transcript" in err.lower():
            raise ValueError(_("err_no_subtitles"))
        raise ValueError(f"{_('err_fetch_subtitles')}{e}")


def build_timed_text(transcript) -> str:
    """자막 항목을 [MM:SS] 텍스트 형식으로 병합 (v1.x 객체 및 dict 모두 지원)"""
    lines = []
    for entry in transcript:
        if hasattr(entry, "start"):
            start = entry.start
            text = entry.text
        else:
            start = entry["start"]
            text = entry["text"]
        ts = seconds_to_mmss(start)
        text = text.replace("\n", " ").strip()
        lines.append(f"[{ts}] {text}")
    return "\n".join(lines)


def fetch_exam_questions(keywords: list[str], max_results: int = 3) -> list[dict]:
    """Supabase에서 테스트 통과서 기출문제를 검색합니다."""
    if not supabase or not keywords:
        return []
    try:
        # keywords 배열에 하나라도 포함되는 행 검색 (overlaps)
        res = (
            supabase.table("exam_questions")
            .select("id, question_type, question_text, source, year, answer, choices, explanation, keywords")
            .overlaps("keywords", keywords)
            .limit(max_results)
            .execute()
        )
        return res.data if res.data else []
    except Exception as e:
        # Supabase 연결 실패 또는 테이블 없음 → 조용히 무시하고 빈 리스트 반환
        return []


def analyze_with_gpt(timed_text: str, api_key: str) -> dict:
    """Extract 3 core concepts + timestamps + keywords using GPT-4o"""
    client = OpenAI(api_key=api_key)

    title_inst = _("gpt_concept_title_instruction")
    summary_inst = _("gpt_concept_summary_instruction")

    system_prompt = f"""You are an expert at analyzing video transcripts.
When the user provides a captioned text with timestamps, identify 3 key concepts from the video and find the timestamp when each concept first begins.
Also extract up to 10 precise search keywords (e.g. proper nouns, historical terms, key vocabulary) from the entire transcript.

You must respond ONLY with the following JSON format (no codeblocks, pure JSON):
{{
  "keywords": ["keyword1", "keyword2", "..."],
  "concepts": [
    {{
      "number": 1,
      "title": "{title_inst}",
      "summary": "{summary_inst}",
      "timestamp": "MM:SS format"
    }}
  ]
}}"""

    user_prompt = f"""Here is the timestamped transcript of a YouTube video. Please analyze 3 core concepts and extract keywords.

{timed_text[:12000]}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1200,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    data = json.loads(raw)
    return {
        "concepts": data.get("concepts", []),
        "keywords": data.get("keywords", []),
    }


# ─────────────────────────────────────────────
#  Main UI
# ─────────────────────────────────────────────

# Insert trendy header image
image_path = "hero_img.png"
if os.path.exists(image_path):
    st.image(image_path, use_container_width=True)

st.markdown(f"""
<div class="hero-header">
    <div class="hero-brand">Seworeunganda</div>
    <h1>{_("app_title")}</h1>
    <p>{_("app_desc")}</p>
</div>
""", unsafe_allow_html=True)

# ── Auth Block ────────────────────────────────────────────────────────────
st.markdown('<div class="glass-card" style="text-align:center; padding:1.5rem;">', unsafe_allow_html=True)
if not st.session_state.user:
    st.markdown(f"<p style='color:#B19B72; font-weight:600; margin-bottom:1rem;'>{_('msg_login_prompt')}</p>", unsafe_allow_html=True)
    if supabase:
        try:
            res = supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {"redirect_to": "http://localhost:8501", "skip_browser_redirect": True}
            })
            st.link_button(f"\U0001f310 {_('btn_login_google')}", res.url, use_container_width=True)
        except Exception:
            st.error("Supabase config error.")
else:
    u = st.session_state.user
    email = u.email if hasattr(u, "email") else ""
    avatar_url = u.user_metadata.get("avatar_url", "") if hasattr(u, "user_metadata") else ""
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        if avatar_url:
            st.markdown(f"<img src='{avatar_url}' style='border-radius:50%; width:60px; height:60px; border:2px solid #B19B72; margin-bottom:0.5rem;'/>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#E2E2E2; font-weight:500;'>{email}</p>", unsafe_allow_html=True)
        if st.button(_("btn_logout"), use_container_width=True):
            if supabase:
                supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  Tabs: Analyzer | Pricing
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs([_("tab_home"), _("tab_pricing")])


# ══════════════════════════════════════════════
#  TAB 1 — Analyzer (Home)
# ══════════════════════════════════════════════
with tab1:

    # Input Area
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    url_input = st.text_input(_("input_url_label"), placeholder="https://www.youtube.com/watch?v=...")
    analyze_btn = st.button(_("btn_start_analysis"), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    @st.experimental_dialog("\U0001f680 Upgrade to Pro")
    def show_upgrade_paywall():
        st.markdown("""
            <div style="text-align:center; padding:1rem 0;">
                <p style="color:#B19B72; font-weight:700; margin-bottom:1rem; font-size:1.1rem;">Daily Free Limit Reached (3/3)</p>
                <p style="color:#A0A0A9; line-height:1.6; margin-bottom:1.5rem;">
                    You've used up your 3 free summaries for today.<br>
                    Upgrade to a Pro plan for unlimited access to GPT-4o YouTube analysis!
                </p>
            </div>
        """, unsafe_allow_html=True)
        st.link_button(_("btn_upgrade_now"), "https://stripe.com/", use_container_width=True)

    if analyze_btn:
        if not st.session_state.user:
            st.error(_("err_login_required"))
            st.stop()

        user_id = st.session_state.user.id
        if get_daily_usage(user_id) >= 3:
            show_upgrade_paywall()
            st.stop()

        if not api_key:
            st.error(_("sidebar_key_err"))
            st.stop()
        if not url_input.strip():
            st.error(_("err_no_url"))
            st.stop()
        video_id = extract_video_id(url_input.strip())
        if not video_id:
            st.error(_("err_invalid_url"))
            st.stop()

        locale_video_id = f"{video_id}_{st.session_state.locale}"
        cached_data = get_cached(locale_video_id)
        if cached_data:
            st.success(_("msg_db_loaded"))
            concepts = cached_data["concepts"]
            timed_text = cached_data["timed_text"]
            total_entries = cached_data["total_entries"]
            duration = cached_data["duration"]
            gpt_keywords = cached_data.get("keywords", [])
        else:
            with st.spinner(_("msg_loading_subtitles")):
                try:
                    transcript = get_transcript(video_id)
                except ValueError as e:
                    st.error(f"\u274c {e}")
                    st.stop()

            timed_text = build_timed_text(transcript)
            total_entries = len(transcript)
            last = transcript[-1]
            if hasattr(last, "start"):
                last_start = last.start
                last_dur = getattr(last, "duration", 0) or 0
            else:
                last_start = last["start"]
                last_dur = last.get("duration", 0)
            duration = seconds_to_mmss(last_start + last_dur)

            with st.spinner(_("msg_analyzing")):
                try:
                    gpt_result = analyze_with_gpt(timed_text, api_key)
                    concepts = gpt_result["concepts"]
                    gpt_keywords = gpt_result["keywords"]
                except json.JSONDecodeError:
                    st.error(_("err_parse_gpt"))
                    st.stop()
                except Exception as e:
                    st.error(f"{_('err_openai')}{e}")
                    st.stop()

            if is_db_connected():
                save_to_cache(locale_video_id, concepts, timed_text, total_entries, duration)
                increment_daily_usage(user_id)
                st.info(_("msg_saved_db"))

        st.session_state.analysis_results = {
            "video_id": video_id,
            "concepts": concepts,
            "keywords": gpt_keywords,
            "timed_text": timed_text,
            "total_entries": total_entries,
            "duration": duration,
        }
        st.session_state.player_video_id = video_id
        st.session_state.selected_ts = 0
        quotes = lang_data.get("quotes", [])
        st.session_state.selected_poem = random.choice(quotes) if quotes else None

    if st.session_state.analysis_results:
        res = st.session_state.analysis_results
        video_id   = res["video_id"]
        concepts   = res["concepts"]
        timed_text = res["timed_text"]

        st.success(_("res_transcript_loaded", entries=res["total_entries"], duration=res["duration"]))
        st.markdown("---")
        st.markdown(_("res_title"))

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            for i, c in enumerate(concepts):
                ts_raw = c.get("timestamp", "00:00")
                parts = ts_raw.split(":")
                if len(parts) == 2:
                    total_sec = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    total_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    total_sec = 0

                is_active = (
                    st.session_state.player_video_id == video_id and (
                        (st.session_state.selected_ts == total_sec and total_sec > 0)
                        or (i == 0 and st.session_state.selected_ts == 0)
                    )
                )
                left_border = "#B19B72" if is_active else "#4F4F5C"
                bg_color = "#252530" if is_active else "#1A1A21"

                st.markdown(f"""
<div class="concept-card" style="border-left-color:{left_border}; background:{bg_color};">
    <div class="concept-number">{_("res_concept_prefix")}{c.get("number", i+1)}</div>
    <div class="concept-title">{c.get("title", "")}</div>
    <div class="concept-summary">{c.get("summary", "")}</div>
</div>
""", unsafe_allow_html=True)

                if st.button(_("btn_play_from", ts=ts_raw), key=f"play_btn_{i}", use_container_width=True):
                    st.session_state.selected_ts = total_sec
                    st.session_state.player_video_id = video_id
                    st.rerun()

        with col_right:
            st.markdown(_("player_title"))
            if st.session_state.player_video_id:
                render_youtube_player(st.session_state.player_video_id, st.session_state.selected_ts, end_time=None)
            else:
                st.markdown(f"""
<div style="background:#1A1A21; border:1px dashed #4F4F5C; border-radius:6px;
    padding:4rem 1.5rem; text-align:center; color:#6E6E7A; margin-top:0.5rem;">
    <div style="font-size:2.2rem; margin-bottom:1rem; opacity:0.6;">\U0001f4dc</div>
    <div style="font-size:0.95rem; line-height:1.9; font-family:'Noto Serif KR',serif;">
        {_("player_placeholder")}
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("---")
        with st.expander(_("expander_full_transcript")):
            st.text_area(_("label_raw_transcript"), timed_text, height=300, disabled=True)

        # ─────────────────────────────────────────────
        #  실제 시험 확인하기 — 기출문제 검색
        # ─────────────────────────────────────────────
        exam_keywords = res.get("keywords", [])
        if exam_keywords:
            exam_questions = fetch_exam_questions(exam_keywords)

            if exam_questions:
                # 키워드 충 표시
                chips_html = "".join(
                    f'<span class="exam-keyword-chip"># {kw}</span>'
                    for kw in exam_keywords[:6]
                )
                st.markdown(f"""
<div class="exam-section-header">
    <span style="font-size:1.3rem;">📚</span>
    <span class="exam-section-title">실제 시험 확인하기</span>
</div>
<div style="margin-bottom:1.2rem;">{chips_html}</div>
""", unsafe_allow_html=True)

                for qi, q in enumerate(exam_questions):
                    qtype = q.get("question_type", "multiple")
                    qtext = q.get("question_text", "")
                    source = q.get("source", "")
                    answer = q.get("answer", "")
                    choices = q.get("choices") or {}
                    explanation = q.get("explanation", "")

                    # 정답 보기 토글 키
                    ans_key = f"show_answer_{video_id}_{qi}"
                    if ans_key not in st.session_state:
                        st.session_state[ans_key] = False

                    # 커스텀 CSS로 HTML 렌더링
                    if qtype == "ox":
                        type_badge = '<span class="exam-type-ox">■ OX형</span>'
                        ans_html = ""
                        if st.session_state[ans_key]:
                            color = "#22C55E" if answer == "O" else "#EF4444"
                            ans_html = f'<div style="margin-top:0.5rem; font-size:1rem; font-weight:800; color:{color};">\uc815\ub2f5: {answer}'
                            if explanation:
                                ans_html += f'<span style="font-size:0.85rem; color:#A0A0A9; font-weight:400;"> &mdash; {explanation}</span>'
                            ans_html += "</div>"
                        st.markdown(f"""
<div class="exam-card">
    <div class="exam-source-badge">{source}</div>
    {type_badge}
    <div class="exam-question-text">{qtext}</div>
    {ans_html}
</div>
""", unsafe_allow_html=True)

                    else:  # multiple
                        type_badge = '<span class="exam-type-ox">■ 4지선다형</span>'
                        choices_html = "<ul class='exam-choices'>"
                        for num, text in (choices.items() if isinstance(choices, dict) else {}):
                            is_correct = st.session_state[ans_key] and str(num) == str(answer)
                            cls = " correct" if is_correct else ""
                            mark = " &#9654;" if is_correct else ""
                            choices_html += f"<li class='exam-choice{cls}'>​{num}\ub825 {text}{mark}</li>"
                        choices_html += "</ul>"

                        exp_html = ""
                        if st.session_state[ans_key] and explanation:
                            exp_html = f'<div style="font-size:0.85rem; color:#A0A0A9; margin-top:0.4rem; padding:0.5rem 0.7rem; background:#23232A; border-radius:6px;">💡 {explanation}</div>'

                        st.markdown(f"""
<div class="exam-card">
    <div class="exam-source-badge">{source}</div>
    {type_badge}
    <div class="exam-question-text">{qtext}</div>
    {choices_html}
    {exp_html}
</div>
""", unsafe_allow_html=True)

                    # 정답 보기 / 숨기기 토글 버튼
                    btn_label = "🔍정답 숨기기" if st.session_state[ans_key] else "\u2753 \uc815\ub2f5 \ubcf4\uae30"
                    if st.button(btn_label, key=f"ans_btn_{video_id}_{qi}", use_container_width=False):
                        st.session_state[ans_key] = not st.session_state[ans_key]
                        st.rerun()


        if st.session_state.selected_poem:
            poem = st.session_state.selected_poem
            st.markdown(f"""
<div class="poem-section">
    <div class="poem-divider">
        <div class="poem-divider-line"></div>
        <div class="poem-divider-icon">\u2726 \u2726 \u2726</div>
        <div class="poem-divider-line"></div>
    </div>
    <div style="display:flex; justify-content:center;">
        <div class="poem-card">
            <div class="poem-label">{_("quote_title")}</div>
            <div class="poem-text">{poem["text"]}</div>
            <div class="poem-author">\u2014 {poem["author"]}</div>
        </div>
    </div>
    <div class="poem-footer">{_("quote_footer")}</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  TAB 2 — Pricing
# ══════════════════════════════════════════════
with tab2:
    st.markdown(f"""
<div style="text-align:center; padding:2rem 0 1.5rem;">
    <h2 style="font-family:'Nanum Myeongjo',serif; font-size:1.8rem; color:#FFFFFF; margin-bottom:0.4rem;">{_("pricing_title")}</h2>
    <p style="color:#6E6E7A; font-size:0.95rem;">Seworeunganda \u00b7 GPT-4o YouTube Analyzer</p>
</div>
""", unsafe_allow_html=True)

    # Free
    st.markdown(f"""
<div class="pricing-card">
    <div class="pricing-title">{_("pricing_free_title")}</div>
    <div class="pricing-price">{_("pricing_free_price")}</div>
    <div class="pricing-desc">{_("pricing_free_desc")}</div>
    <ul style="list-style:none; padding:0; margin:0 0 1.8rem; color:#A0A0A9; font-size:0.95rem; text-align:left;">
        <li style="padding:0.4rem 0; border-bottom:1px solid #32323D;">\u2713 &nbsp; 3 AI summaries per day</li>
        <li style="padding:0.4rem 0; border-bottom:1px solid #32323D;">\u2713 &nbsp; Core Concept Extraction</li>
        <li style="padding:0.4rem 0; color:#4F4F5C;">\u2717 &nbsp; Quiz Feature</li>
        <li style="padding:0.4rem 0; color:#4F4F5C;">\u2717 &nbsp; Unlimited Usage</li>
    </ul>
    <span style="display:block; background:#2A2A33; color:#6E6E7A;
        border:1px solid #4F4F5C; border-radius:50px; padding:0.75rem;
        font-weight:600; font-size:0.95rem;">Current Plan</span>
</div>
""", unsafe_allow_html=True)

    # Monthly
    st.markdown(f"""
<div class="pricing-card">
    <div class="pricing-title">{_("pricing_monthly_title")}</div>
    <div class="pricing-price">{_("pricing_monthly_price")}</div>
    <div class="pricing-desc">{_("pricing_monthly_desc")}</div>
    <ul style="list-style:none; padding:0; margin:0 0 1.8rem; color:#C0C0C8; font-size:0.95rem; text-align:left;">
        <li style="padding:0.4rem 0; border-bottom:1px solid #32323D;">\u2713 &nbsp; Unlimited AI summaries</li>
        <li style="padding:0.4rem 0; border-bottom:1px solid #32323D;">\u2713 &nbsp; Core Concept Extraction</li>
        <li style="padding:0.4rem 0; border-bottom:1px solid #32323D;">\u2713 &nbsp; Quiz Feature</li>
        <li style="padding:0.4rem 0; color:#4F4F5C;">\u2717 &nbsp; Best price (save 40%)</li>
    </ul>
    <a href="https://stripe.com/" style="display:block; background:#2A2A33; color:#FFFFFF;
        border:1px solid #B19B72; border-radius:50px; padding:0.75rem;
        text-decoration:none; font-weight:600; font-size:0.95rem; text-align:center;">
        {_("btn_upgrade_now")}
    </a>
</div>
""", unsafe_allow_html=True)

    # Yearly — Best Value
    st.markdown(f"""
<div class="pricing-card best-value">
    <div class="pricing-badge">\u2b50 {_("pricing_best_value")} \u2014 40% OFF</div>
    <div class="pricing-title">{_("pricing_yearly_title")}</div>
    <div class="pricing-price">{_("pricing_yearly_price")}</div>
    <div class="pricing-desc" style="color:#B19B72; font-weight:600;">{_("pricing_yearly_desc")}</div>
    <ul style="list-style:none; padding:0; margin:0 0 1.8rem; color:#C0C0C8; font-size:0.95rem; text-align:left;">
        <li style="padding:0.4rem 0; border-bottom:1px solid #3B3B46;">\u2713 &nbsp; Unlimited AI summaries</li>
        <li style="padding:0.4rem 0; border-bottom:1px solid #3B3B46;">\u2713 &nbsp; Core Concept Extraction</li>
        <li style="padding:0.4rem 0; border-bottom:1px solid #3B3B46;">\u2713 &nbsp; Quiz Feature</li>
        <li style="padding:0.4rem 0; color:#B19B72; font-weight:600;">\u2713 &nbsp; Save 40% vs monthly</li>
    </ul>
    <a href="https://stripe.com/" style="display:block;
        background:linear-gradient(90deg, #D4AF37, #B19B72); color:#0F0F13;
        border:none; border-radius:50px; padding:0.75rem;
        text-decoration:none; font-weight:800; font-size:0.95rem; text-align:center;
        box-shadow:0 6px 20px rgba(177,155,114,0.4);">
        {_("btn_upgrade_now")}
    </a>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  Terms of Service & Footer
# ─────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)

with st.expander(_("tos_title")):
    st.markdown(_("tos_content"))

st.markdown("""
<div style="text-align:center; padding-top:2rem; padding-bottom:2rem; color:#6E6E7A;
    font-size:0.85rem; letter-spacing:0.05em; font-family:'Noto Serif KR',serif;
    border-top:1px solid #23232A; margin-top:1rem;">
    \u00a9 2026 Seworeunganda. All rights reserved.
</div>
""", unsafe_allow_html=True)
