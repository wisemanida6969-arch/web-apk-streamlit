import os
import streamlit as st
import re
import random
from youtube_transcript_api import YouTubeTranscriptApi
try:
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
except ImportError:
    from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
from openai import OpenAI
import json

from db import get_cached, save_to_cache, is_db_connected

# ─────────────────────────────────────────────
#  수험생 응원 시 목록
# ─────────────────────────────────────────────
POEMS = [
    {
        "text": "죽는 날까지 하늘을 우러러\n한 점 부끄럼이 없기를,\n잎새에 이는 바람에도\n나는 괴로워했다.\n\n오늘 밤에도 별이 바람에 스치운다.",
        "author": "윤동주, 「서시」",
    },
    {
        "text": "흔들리지 않고 피는 꽃이 어디 있으랴\n이 세상 그 어떤 아름다운 꽃들도\n다 흔들리면서 피었나니\n흔들리면서 줄기를 곧게 세웠나니.",
        "author": "도종환, 「흔들리며 피는 꽃」",
    },
    {
        "text": "광야에서\n까마득한 날에 하늘이 처음 열리고\n지금 눈 내리고\n매화 향기 홀로 아득하니\n내 여기 가난한 노래의 씨를 뿌려라.",
        "author": "이육사, 「광야」",
    },
    {
        "text": "별 헤는 밤\n계절이 지나가는 하늘에는\n가을로 가득 차 있습니다.\n나는 아무 걱정도 없이\n가을 속의 별들을 다 헤일 듯합니다.",
        "author": "윤동주, 「별 헤는 밤」",
    },
    {
        "text": "오늘 흘린 땀 한 방울이\n내일의 강이 된다.\n묵묵히 걸어온 네 발자국이\n어느 날 빛나는 길이 될 것이다.",
        "author": "수험생을 위한 시",
    },
    {
        "text": "산이 거기 있기 때문에 올라가듯\n문제가 여기 있기에 풀어 나간다.\n포기하지 않는 마음, 그것이\n이미 절반의 답이다.",
        "author": "수험생을 위한 시",
    },
    {
        "text": "청포도가 익어가는 시절\n이 마을 전설이 주저리주저리 열리고\n먼 데 하늘이 꿈꾸며 알알이 들어와 박혀,\n내가 바라는 손님은 고달픈 몸으로\n청포를 입고 찾아온다고 했으니,",
        "author": "이육사, 「청포도」",
    },
    {
        "text": "나는 나에게 작은 손을 내밀어\n눈물과 위안으로 잡는 최초의 악수.\n오늘도 무사히 버텨낸 나에게,\n잘했다고, 어깨를 두드려 주어라.",
        "author": "수험생을 위한 시",
    },
    {
        "text": "넓은 벌 동쪽 끝으로\n옛이야기 지줄대는 실개천이 휘돌아 나가고,\n그 곳이 차마 꿈엔들 잊힐 리야.\n\n지금 이 순간도, 네 이야기가 되고 있다.",
        "author": "정지용, 「향수」에서",
    },
    {
        "text": "하늘은 날마다 새롭고\n땅은 날마다 단단하다.\n어제보다 조금 더 나아진 오늘,\n그것으로 충분하다.",
        "author": "수험생을 위한 시",
    },
]

# ─────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="세월은간다 — YouTube 핵심 개념 분석기",
    page_icon="📜",
    layout="wide",
)

# ─────────────────────────────────────────────
#  Session state 초기화
# ─────────────────────────────────────────────
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "player_video_id" not in st.session_state:
    st.session_state.player_video_id = None
if "selected_ts" not in st.session_state:
    st.session_state.selected_ts = 0
if "selected_poem" not in st.session_state:
    st.session_state.selected_poem = None

# ─────────────────────────────────────────────
#  Custom CSS  — 세월은간다 브랜드 (베이지 + 먹색)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=Noto+Serif+KR:wght@300;400;500;600&display=swap');

/* ── 기본 타이포그래피 ── */
html, body, [class*="css"] {
    font-family: 'Noto Serif KR', 'Nanum Myeongjo', serif;
}

/* ── 배경 ── */
.stApp {
    background-color: #F7F3EC;
    background-image:
        radial-gradient(ellipse at 15% 40%, rgba(139,111,78,0.06) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 15%, rgba(44,32,19,0.04) 0%, transparent 55%);
    min-height: 100vh;
}

/* ── 상단 헤더 ── */
.hero-header {
    text-align: center;
    padding: 2.8rem 1rem 1.6rem;
    border-bottom: 1px solid #D9D0BE;
    margin-bottom: 2rem;
}
.hero-brand {
    font-family: 'Nanum Myeongjo', serif;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.28em;
    color: #8B7355;
    text-transform: uppercase;
    margin-bottom: 0.7rem;
}
.hero-header h1 {
    font-family: 'Nanum Myeongjo', serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #1C1810;
    letter-spacing: -0.01em;
    margin-bottom: 0.5rem;
    line-height: 1.3;
}
.hero-header p {
    color: #7A6B55;
    font-size: 0.97rem;
    letter-spacing: 0.03em;
}

/* ── 트렌디한 애니메이션 설정 ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}
.hero-header {
    animation: fadeInUp 0.8s ease-out forwards;
}

/* ── 메인 이미지 커스텀 테두리 ── */
[data-testid="stImage"] {
    display: flex;
    justify-content: center;
    margin-bottom: 2rem;
    animation: fadeInUp 0.6s ease-out forwards;
}
[data-testid="stImage"] img {
    border-radius: 20px !important;
    box-shadow: 0 12px 35px rgba(44,32,19,0.12) !important;
    max-height: 400px;
    object-fit: cover;
    width: 100%;
}

/* ── 유리 카드 → 트렌디 라운드 카드 ── */
.glass-card {
    background: #FFFDF8;
    border: 1px solid #D9D0BE;
    border-radius: 20px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.4rem;
    box-shadow: 0 8px 30px rgba(44,32,19,0.06);
    animation: fadeInUp 1s ease-out forwards;

}

/* ── 개념 카드 (소프트 UI) ── */
.concept-card {
    background: #FFFDF8;
    border: 1px solid #D9D0BE;
    border-left: 5px solid #2C2013;
    border-radius: 14px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1rem;
    transition: box-shadow 0.25s ease, border-left-color 0.25s ease;
}
.concept-card:hover {
    box-shadow: 0 4px 18px rgba(44,32,19,0.10);
}
.concept-number {
    font-size: 0.70rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: #8B7355;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}
.concept-title {
    font-family: 'Nanum Myeongjo', serif;
    font-size: 1.13rem;
    font-weight: 700;
    color: #1C1810;
    margin-bottom: 0.5rem;
    letter-spacing: -0.01em;
}
.concept-summary {
    font-size: 0.92rem;
    color: #5A4A38;
    line-height: 1.85;
}

/* ── 타임스탬프 배지 ── */
.timestamp-badge {
    display: inline-block;
    background: #F0EAE0;
    border: 1px solid #C8B89A;
    border-radius: 3px;
    padding: 0.18rem 0.55rem;
    font-size: 0.80rem;
    font-weight: 600;
    color: #4A3728;
    font-family: 'Courier New', monospace;
}

/* ── 구분선 ── */
hr { border-color: #D9D0BE !important; }

/* ── 섹션 제목 ── */
h2, h3 {
    font-family: 'Nanum Myeongjo', serif !important;
    color: #1C1810 !important;
    letter-spacing: -0.01em !important;
}

/* ── 입력창 (필 라운드) ── */
.stTextInput > div > div > input {
    background: #FFFDF8 !important;
    border: 1.5px solid #C8B89A !important;
    border-radius: 12px !important;
    color: #1C1810 !important;
    font-size: 0.95rem !important;
    font-family: 'Noto Serif KR', serif !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input::placeholder { color: #B0A090 !important; }
.stTextInput > div > div > input:focus {
    border-color: #4A3728 !important;
    box-shadow: 0 0 0 2px rgba(74,55,40,0.12) !important;
}
.stTextInput > label {
    color: #4A3728 !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
}

/* ── 버튼 (완전한 둥근 알약 형태) ── */
.stButton > button {
    background: #2C2013 !important;
    color: #F7F3EC !important;
    border: none !important;
    border-radius: 50px !important;
    font-family: 'Noto Serif KR', serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    padding: 0.7rem 2rem !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    box-shadow: 0 4px 14px rgba(44,32,19,0.2) !important;
    width: 100%;
}
.stButton > button:hover {
    background: #4A3728 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(44,32,19,0.3) !important;
}
.stButton > button:active {
    transform: translateY(1px) !important;
}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: #F0EAE0 !important;
    border-right: 1px solid #D9D0BE !important;
}
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    font-family: 'Courier New', monospace !important;
    font-size: 0.85rem !important;
    background: #FAF6EF !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li {
    color: #3D2E1E !important;
}

/* ── Alert / 알림 ── */
.stAlert {
    border-radius: 5px !important;
    background: #FFFDF8 !important;
    border: 1px solid #D9D0BE !important;
    color: #2C2013 !important;
}

/* ── Spinner ── */
.stSpinner > div { color: #4A3728 !important; }

/* ── 성공 메시지 ── */
[data-testid="stNotification"] {
    background: #F5F0E6 !important;
    border: 1px solid #C8B89A !important;
    color: #2C2013 !important;
    border-radius: 5px !important;
}

/* ── 스크롤바 ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #F0EAE0; }
::-webkit-scrollbar-thumb { background: #C8B89A; border-radius: 3px; }

/* ── 시 블록 ── */
.poem-section {
    margin-top: 3rem;
    padding: 0 0 2rem;
    text-align: center;
}
.poem-divider {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
}
.poem-divider-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, transparent, #C8B89A, transparent);
}
.poem-divider-icon {
    color: #8B7355;
    font-size: 1rem;
    letter-spacing: 0.2em;
}
.poem-card {
    display: inline-block;
    max-width: 560px;
    background: #FFFDF8;
    border: 1px solid #D9D0BE;
    border-top: 2px solid #2C2013;
    border-radius: 4px;
    padding: 2.2rem 2.8rem;
    box-shadow: 0 2px 16px rgba(44,32,19,0.06);
    position: relative;
}
.poem-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.22em;
    color: #8B7355;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}
.poem-text {
    font-family: 'Nanum Myeongjo', serif;
    font-size: 1.05rem;
    color: #1C1810;
    line-height: 2.3;
    white-space: pre-line;
    letter-spacing: 0.03em;
    text-align: center;
}
.poem-author {
    font-size: 0.82rem;
    color: #8B7355;
    margin-top: 1.4rem;
    letter-spacing: 0.07em;
    font-style: italic;
}
.poem-footer {
    margin-top: 2.5rem;
    font-size: 0.80rem;
    color: #B0A090;
    letter-spacing: 0.12em;
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
#  사이드바
# ─────────────────────────────────────────────
with st.sidebar:
    # 서비스 상태 표시
    db_status = "🟢 DB 연결됨" if is_db_connected() else "🟡 DB 미연결 (캐시 제외)"
    
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
    <span style="font-size:0.68rem;letter-spacing:0.16em;color:#8B7355;font-weight:700;">SERVICE STATUS</span><br>
    <span style="font-size:0.88rem;color:#2C2013;font-family:'Noto Serif KR',serif;">
        ✔ AI 서비스 운영 중<br>
        {db_status}
    </span>
</div>
""", unsafe_allow_html=True)
    else:
        st.error("⚠️ API 키가 서버에 설정되지 않았습니다.\n`.streamlit/secrets.toml`을 확인하세요.")
    st.markdown("---")
    st.markdown("""
**사용 방법**
1. YouTube 영상 URL 붙여넣기
2. **분석 시작** 클릭

**지원 언어**
- 한국어 자막 우선
- 없으면 영어 자막 사용

**사용 모델**
`gpt-4o`
    """)
    st.markdown("---")
    st.caption("세월은간다 · Powered by GPT-4o")


# ─────────────────────────────────────────────
#  Helper 함수들
# ─────────────────────────────────────────────

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
    """자막 가져오기 – v1.x 인스턴스 방식, 한국어→영어→기타 순"""
    ytt = YouTubeTranscriptApi()
    try:
        try:
            return ytt.fetch(video_id, languages=["ko"])
        except Exception:
            pass
        try:
            return ytt.fetch(video_id, languages=["en"])
        except Exception:
            pass
        return ytt.fetch(video_id)
    except Exception as e:
        err = str(e)
        if "disabled" in err.lower() or "no transcript" in err.lower():
            raise ValueError("이 영상에는 자막이 없거나 비활성화되어 있습니다.")
        raise ValueError(f"자막을 가져오는 중 오류가 발생했습니다: {e}")


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


def analyze_with_gpt(timed_text: str, api_key: str) -> list[dict]:
    """GPT-4o로 핵심 개념 3가지 + 타임스탬프 추출"""
    client = OpenAI(api_key=api_key)

    system_prompt = """당신은 동영상 자막을 분석하는 전문가입니다.
사용자가 타임스탬프가 포함된 자막 텍스트를 제공하면,
영상의 핵심 개념 3가지를 식별하고 각 개념이 처음 시작되는 타임스탬프를 찾아 반환합니다.

반드시 아래 JSON 형식으로만 응답하세요 (코드블록 없이 순수 JSON):
{
  "concepts": [
    {
      "number": 1,
      "title": "개념 제목 (한국어, 10자 이내)",
      "summary": "개념 설명 (한국어, 2~3문장)",
      "timestamp": "MM:SS 형식"
    }
  ]
}"""

    user_prompt = f"""다음은 YouTube 영상의 타임스탬프 자막입니다. 핵심 개념 3가지를 분석해주세요.

{timed_text[:12000]}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
    data = json.loads(raw)
    return data["concepts"]


# ─────────────────────────────────────────────
#  메인 UI
# ─────────────────────────────────────────────

# 트렌디한 헤더 이미지 삽입
import os
image_path = "hero_img.png"
if os.path.exists(image_path):
    st.image(image_path, use_container_width=True)

st.markdown("""
<div class="hero-header">
    <div class="hero-brand">세월은간다</div>
    <h1>📜 YouTube 핵심 개념 분석기</h1>
    <p>영상 자막을 AI로 분석해 핵심 개념 3가지와 타임스탬프를 추출합니다</p>
</div>
""", unsafe_allow_html=True)

# 입력 영역
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
url_input = st.text_input(
    "🔗 YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
)
analyze_btn = st.button("분석 시작 →", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  분석 실행
# ─────────────────────────────────────────────
if analyze_btn:
    if not api_key:
        st.error("⚠️ 서버에 API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
        st.stop()
    if not url_input.strip():
        st.error("⚠️ YouTube URL을 입력해주세요.")
        st.stop()
    video_id = extract_video_id(url_input.strip())
    if not video_id:
        st.error("⚠️ 유효한 YouTube URL이 아닙니다. 다시 확인해 주세요.")
        st.stop()

    # 1) 먼저 DB(캐시)에서 가져오기 시도
    cached_data = get_cached(video_id)
    if cached_data:
        st.success("⚡ DB에 저장된 분석 결과를 즉시 불러왔습니다.")
        concepts = cached_data["concepts"]
        timed_text = cached_data["timed_text"]
        total_entries = cached_data["total_entries"]
        duration = cached_data["duration"]
    else:
        # DB에 없으면 직접 처리:
        # ── 자막 가져오기 ────────────────────────────
        with st.spinner("자막을 불러오는 중..."):
            try:
                transcript = get_transcript(video_id)
            except ValueError as e:
                st.error(f"❌ {e}")
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

        # ── GPT 분석 ─────────────────────────────────
        with st.spinner("GPT-4o가 핵심 개념을 분석 중입니다..."):
            try:
                concepts = analyze_with_gpt(timed_text, api_key)
            except json.JSONDecodeError:
                st.error("❌ GPT 응답을 파싱하지 못했습니다. 다시 시도해 주세요.")
                st.stop()
            except Exception as e:
                st.error(f"❌ OpenAI API 오류: {e}")
                st.stop()
        
        # ── 결과 DB에 저장 ───────────────────────────
        if is_db_connected():
            save_to_cache(video_id, concepts, timed_text, total_entries, duration)
            st.info("💾 새로운 분석 결과를 DB에 저장했습니다.")

    # 결과 및 시를 session_state에 저장
    st.session_state.analysis_results = {
        "video_id": video_id,
        "concepts": concepts,
        "timed_text": timed_text,
        "total_entries": total_entries,
        "duration": duration,
    }
    st.session_state.player_video_id = video_id
    st.session_state.selected_ts = 0
    st.session_state.selected_poem = random.choice(POEMS)


# ─────────────────────────────────────────────
#  결과 표시
# ─────────────────────────────────────────────
if st.session_state.analysis_results:
    res        = st.session_state.analysis_results
    video_id   = res["video_id"]
    concepts   = res["concepts"]
    timed_text = res["timed_text"]

    st.success(
        f"✅ 자막 로드 완료 — 총 {res['total_entries']}개 구간 · "
        f"영상 길이 약 {res['duration']}"
    )
    st.markdown("---")
    st.markdown("## 💡 핵심 개념 분석 결과")

    col_left, col_right = st.columns([1, 1], gap="large")

    # ── 왼쪽: 개념 카드 + 재생 버튼 ─────────────────
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

            # 활성 카드 강조 (먹색 왼쪽 테두리 → 황토 계열)
            is_active = (
                st.session_state.player_video_id == video_id and (
                    (st.session_state.selected_ts == total_sec and total_sec > 0)
                    or (i == 0 and st.session_state.selected_ts == 0)
                )
            )
            left_border = "#8B6F4E" if is_active else "#2C2013"
            bg_color = "#FFF8EE" if is_active else "#FFFDF8"

            st.markdown(f"""
<div class="concept-card" style="border-left-color:{left_border}; background:{bg_color};">
    <div class="concept-number">핵심 개념 {c.get('number', i+1)}</div>
    <div class="concept-title">{c.get('title', '')}</div>
    <div class="concept-summary">{c.get('summary', '')}</div>
</div>
""", unsafe_allow_html=True)

            if st.button(
                f"▶  {ts_raw} 부터 재생",
                key=f"play_btn_{i}",
                use_container_width=True,
            ):
                st.session_state.selected_ts = total_sec
                st.session_state.player_video_id = video_id
                st.rerun()

    # ── 오른쪽: 유튜브 임베드 플레이어 ──────────────
    with col_right:
        st.markdown("### 📺 영상 플레이어")
        if st.session_state.player_video_id:
            pid = st.session_state.player_video_id
            pts = st.session_state.selected_ts
            embed_url = (
                f"https://www.youtube.com/embed/{pid}"
                f"?start={pts}&autoplay=1&rel=0&modestbranding=1"
            )
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
        else:
            st.markdown("""
<div style="
    background: #F5F0E6;
    border: 1px dashed #C8B89A;
    border-radius: 6px;
    padding: 4rem 1.5rem;
    text-align: center;
    color: #9A8870;
    margin-top: 0.5rem;
">
    <div style="font-size:2.2rem; margin-bottom:1rem; opacity:0.6;">📜</div>
    <div style="font-size:0.95rem; line-height:1.9; font-family:'Noto Serif KR',serif;">
        왼쪽 개념 카드 아래<br>
        <b style='color:#4A3728'>재생 버튼</b>을 누르면<br>
        해당 시간대부터 재생됩니다
    </div>
</div>
""", unsafe_allow_html=True)

    # ── 전체 자막 (접이식) ───────────────────────────
    st.markdown("---")
    with st.expander("📄 전체 자막 보기"):
        st.text_area("자막 원문 (타임스탬프 포함)", timed_text, height=300, disabled=True)

    # ─────────────────────────────────────────────
    #  수험생 응원 시
    # ─────────────────────────────────────────────
    if st.session_state.selected_poem:
        poem = st.session_state.selected_poem
        st.markdown(f"""
<div class="poem-section">
    <div class="poem-divider">
        <div class="poem-divider-line"></div>
        <div class="poem-divider-icon">✦ ✦ ✦</div>
        <div class="poem-divider-line"></div>
    </div>
    <div style="display:flex; justify-content:center;">
        <div class="poem-card">
            <div class="poem-label">오늘의 한 구절</div>
            <div class="poem-text">{poem['text']}</div>
            <div class="poem-author">— {poem['author']}</div>
        </div>
    </div>
    <div class="poem-footer">세월은간다 · 수험생 여러분을 응원합니다</div>
</div>
""", unsafe_allow_html=True)
