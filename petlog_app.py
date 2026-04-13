"""
PetLog AI — 반려동물 AI 건강 일지 SaaS
Phase 1: Google 로그인 + 반려동물 프로필 등록 + 메인 대시보드
Phase 2: 매일 건강 체크 + 캘린더 보기 + 이상 증상 경고
"""
import streamlit as st
import sqlite3
import os
import calendar as pycal
import requests
from datetime import datetime, date, timedelta
from urllib.parse import urlencode
from pathlib import Path

# ══════════════════════════════════════
# Config
# ══════════════════════════════════════
APP_NAME = "PetLog AI"
APP_DOMAIN = "petlog.trytimeback.com"
APP_VERSION = "2026-04-13-phase1"

st.set_page_config(
    page_title=f"{APP_NAME} — 반려동물 AI 건강 일지",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def get_secret(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)


# ══════════════════════════════════════
# Database (SQLite)
# ══════════════════════════════════════
DB_PATH = Path(get_secret("PETLOG_DB_PATH", "petlog.db"))


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            picture TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT,
            age_years REAL,
            weight_kg REAL,
            emoji TEXT,
            created_at TEXT,
            FOREIGN KEY(user_email) REFERENCES users(email)
        );
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            log_date TEXT NOT NULL,
            appetite TEXT,
            activity TEXT,
            stool TEXT,
            notes TEXT,
            alert_level INTEGER DEFAULT 0,
            created_at TEXT,
            UNIQUE(pet_id, log_date),
            FOREIGN KEY(pet_id) REFERENCES pets(id)
        );
        """)
        conn.commit()


def upsert_user(email: str, name: str, picture: str):
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO users(email, name, picture, created_at)
               VALUES(?,?,?,?)
               ON CONFLICT(email) DO UPDATE SET name=excluded.name, picture=excluded.picture""",
            (email, name, picture, datetime.utcnow().isoformat()),
        )
        conn.commit()


def list_pets(email: str):
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pets WHERE user_email=? ORDER BY created_at DESC",
            (email,),
        ).fetchall()
        return [dict(r) for r in rows]


def add_pet(email: str, name: str, species: str, breed: str,
            age_years: float, weight_kg: float, emoji: str):
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO pets(user_email, name, species, breed, age_years, weight_kg, emoji, created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (email, name, species, breed, age_years, weight_kg, emoji,
             datetime.utcnow().isoformat()),
        )
        conn.commit()


def delete_pet(pet_id: int, email: str):
    with db_conn() as conn:
        conn.execute("DELETE FROM pets WHERE id=? AND user_email=?", (pet_id, email))
        conn.execute("DELETE FROM daily_logs WHERE pet_id=? AND user_email=?",
                     (pet_id, email))
        conn.commit()


def get_pet(pet_id: int, email: str):
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM pets WHERE id=? AND user_email=?",
            (pet_id, email),
        ).fetchone()
        return dict(row) if row else None


# ── 이상 증상 감지 ──
APPETITE_LEVELS = ["매우 좋음", "좋음", "보통", "적음", "없음"]
ACTIVITY_LEVELS = ["매우 활발", "활발", "보통", "낮음", "매우 낮음"]
STOOL_LEVELS = ["정상", "무름", "설사", "변비", "혈변"]
ALERT_KEYWORDS = [
    "구토", "토함", "피", "혈", "발작", "쓰러", "경련", "호흡",
    "숨참", "의식", "절뚝", "다리", "심하게", "심각", "응급",
]


def compute_alert_level(appetite: str, activity: str, stool: str, notes: str) -> int:
    """0=정상, 1=주의, 2=경고"""
    level = 0
    if appetite in ("적음",):
        level = max(level, 1)
    if appetite in ("없음",):
        level = max(level, 2)
    if activity in ("낮음",):
        level = max(level, 1)
    if activity in ("매우 낮음",):
        level = max(level, 2)
    if stool in ("무름", "변비"):
        level = max(level, 1)
    if stool in ("설사", "혈변"):
        level = max(level, 2)
    if notes:
        low = notes.lower()
        if any(k in low for k in ALERT_KEYWORDS):
            level = max(level, 2)
    return level


def upsert_daily_log(pet_id: int, email: str, log_date: str,
                     appetite: str, activity: str, stool: str,
                     notes: str, alert_level: int):
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO daily_logs
               (pet_id, user_email, log_date, appetite, activity, stool, notes,
                alert_level, created_at)
               VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(pet_id, log_date) DO UPDATE SET
                 appetite=excluded.appetite,
                 activity=excluded.activity,
                 stool=excluded.stool,
                 notes=excluded.notes,
                 alert_level=excluded.alert_level,
                 created_at=excluded.created_at""",
            (pet_id, email, log_date, appetite, activity, stool, notes,
             alert_level, datetime.utcnow().isoformat()),
        )
        conn.commit()


def get_log(pet_id: int, log_date: str):
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM daily_logs WHERE pet_id=? AND log_date=?",
            (pet_id, log_date),
        ).fetchone()
        return dict(row) if row else None


def get_logs_in_month(pet_id: int, year: int, month: int) -> dict:
    start = date(year, month, 1).isoformat()
    last_day = pycal.monthrange(year, month)[1]
    end = date(year, month, last_day).isoformat()
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM daily_logs
               WHERE pet_id=? AND log_date BETWEEN ? AND ?""",
            (pet_id, start, end),
        ).fetchall()
        return {r["log_date"]: dict(r) for r in rows}


def count_logs_today(email: str) -> int:
    today = date.today().isoformat()
    with db_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM daily_logs WHERE user_email=? AND log_date=?",
            (email, today),
        ).fetchone()
        return int(row["c"]) if row else 0


init_db()


# ══════════════════════════════════════
# Google OAuth
# ══════════════════════════════════════
GOOGLE_CLIENT_ID = get_secret("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = get_secret("PETLOG_REDIRECT_URI",
                          f"https://{APP_DOMAIN}/")


def get_google_login_url() -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
    )
    if resp.status_code != 200:
        raise Exception(f"Token exchange failed: {resp.status_code} — {resp.text}")
    return resp.json()


def get_user_info(access_token: str) -> dict:
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


def handle_oauth_callback():
    if st.session_state.get("login_error"):
        st.error(st.session_state.pop("login_error"))

    code = st.query_params.get("code")
    if code and not st.session_state.get("logged_in"):
        try:
            token = exchange_code_for_token(code)
            info = get_user_info(token["access_token"])
            email = info.get("email", "")
            name = info.get("name", "")
            picture = info.get("picture", "")
            upsert_user(email, name, picture)
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = {
                "email": email, "name": name, "picture": picture,
            }
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.session_state["login_error"] = f"로그인 실패: {e}"
            st.query_params.clear()
            st.rerun()


def logout():
    for k in ("logged_in", "user_info"):
        st.session_state.pop(k, None)
    st.rerun()


# ══════════════════════════════════════
# Global CSS — 따뜻한 파스텔톤
# ══════════════════════════════════════
st.markdown("""
<style>
    /* 전체 배경: 파스텔 크림 + 복숭아 */
    .stApp {
        background: linear-gradient(135deg, #FFF5EC 0%, #FFE8E8 50%, #FFF0F5 100%);
    }
    /* 메인 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 780px;
    }
    /* 헤딩 */
    h1, h2, h3 { color: #5B4A4A; font-family: 'Pretendard', sans-serif; }

    /* 카드 스타일 */
    .petlog-card {
        background: rgba(255, 255, 255, 0.85);
        border-radius: 22px;
        padding: 26px 28px;
        box-shadow: 0 6px 22px rgba(255, 180, 180, 0.18);
        border: 1px solid rgba(255, 200, 200, 0.45);
        margin-bottom: 18px;
    }
    .pet-card {
        background: linear-gradient(135deg, #FFF9F0 0%, #FFECEC 100%);
        border-radius: 20px;
        padding: 20px 22px;
        border: 2px solid #FFD6D6;
        box-shadow: 0 4px 14px rgba(255, 200, 200, 0.2);
        margin-bottom: 14px;
    }
    .pet-emoji { font-size: 2.8rem; margin-right: 10px; }
    .pet-name { font-size: 1.35rem; font-weight: 800; color: #6B4A4A; }
    .pet-meta { color: #9B7A7A; font-size: 0.92rem; margin-top: 4px; }

    /* 버튼 (primary) */
    div.stButton > button[kind="primary"],
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #FFB5A7, #FFA6C1);
        color: #fff;
        border: none;
        border-radius: 14px;
        padding: 12px 22px;
        font-weight: 700;
        font-size: 0.98rem;
        box-shadow: 0 4px 14px rgba(255, 166, 193, 0.35);
        transition: all 0.25s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 166, 193, 0.5);
    }
    /* 입력창 */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
        border: 1px solid #FFD6D6 !important;
        background: rgba(255,255,255,0.9) !important;
    }

    /* 히어로 */
    .hero {
        text-align: center;
        padding: 20px 10px 10px;
    }
    .hero-emoji { font-size: 4rem; margin-bottom: 8px; }
    .hero-title {
        font-size: 2.2rem; font-weight: 900;
        background: linear-gradient(135deg, #FF8FA3, #FFB085);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .hero-sub { color: #8B6F6F; font-size: 1.02rem; }

    /* Google 로그인 버튼 */
    .google-btn {
        display: inline-flex; align-items: center; justify-content: center; gap: 10px;
        background: #fff; color: #444; font-weight: 700;
        padding: 12px 26px; border-radius: 14px; text-decoration: none;
        border: 1.5px solid #FFD6D6;
        box-shadow: 0 4px 14px rgba(255, 200, 200, 0.3);
        transition: all 0.25s; font-size: 1rem;
    }
    .google-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 22px rgba(255, 166, 193, 0.4);
        border-color: #FFB5A7;
    }

    /* 상단 프로필 바 */
    .topbar {
        display: flex; justify-content: space-between; align-items: center;
        background: rgba(255,255,255,0.75); border-radius: 16px;
        padding: 10px 18px; margin-bottom: 22px;
        border: 1px solid rgba(255, 200, 200, 0.5);
    }
    .topbar-user { display: flex; align-items: center; gap: 10px; color: #6B4A4A; font-weight: 600; }
    .topbar-user img { width: 34px; height: 34px; border-radius: 50%; border: 2px solid #FFD6D6; }

    /* 스탯 박스 */
    .stat-row { display: flex; gap: 12px; margin-bottom: 18px; }
    .stat-box {
        flex: 1; background: rgba(255,255,255,0.85); border-radius: 16px;
        padding: 16px; text-align: center; border: 1px solid #FFE0E0;
    }
    .stat-num { font-size: 1.8rem; font-weight: 900; color: #FF8FA3; }
    .stat-lbl { font-size: 0.85rem; color: #9B7A7A; margin-top: 4px; }

    /* 캘린더 */
    .cal-wrap {
        background: rgba(255,255,255,0.85);
        border-radius: 18px;
        padding: 18px;
        border: 1px solid #FFE0E0;
        margin-bottom: 18px;
    }
    .cal-header {
        display:flex; justify-content:space-between; align-items:center;
        margin-bottom:14px;
    }
    .cal-month { font-size:1.2rem; font-weight:800; color:#6B4A4A; }
    .cal-grid {
        display:grid; grid-template-columns: repeat(7, 1fr); gap:6px;
    }
    .cal-dow {
        text-align:center; font-size:0.78rem; color:#B89898;
        padding:4px 0; font-weight:700;
    }
    .cal-day {
        aspect-ratio: 1 / 1;
        border-radius: 10px;
        background: rgba(255,240,235,0.5);
        display:flex; flex-direction:column; align-items:center; justify-content:center;
        font-size:0.82rem; color:#8B6F6F;
        border: 1px solid transparent;
        position: relative;
    }
    .cal-day.empty { background: transparent; }
    .cal-day.today { border-color: #FF8FA3; font-weight: 800; color: #FF8FA3; }
    .cal-day.ok { background: #DFF5E1; color: #4A8A5C; }
    .cal-day.warn { background: #FFF0C9; color: #A07A20; }
    .cal-day.alert { background: #FFD5D5; color: #B5484A; font-weight:700; }
    .cal-dot { font-size:0.72rem; margin-top:1px; }

    .legend-row { display:flex; gap:14px; justify-content:center; margin-top:12px; font-size:0.82rem; color:#8B6F6F;}
    .legend-dot { display:inline-block; width:12px; height:12px; border-radius:4px; margin-right:4px; vertical-align:middle; }

    /* 경고 배너 */
    .alert-banner {
        background: linear-gradient(135deg, #FFD5D5, #FFC0C0);
        border: 2px solid #FF9999;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 18px;
        color: #8B3A3A; font-weight: 700;
    }
    .warn-banner {
        background: linear-gradient(135deg, #FFF0C9, #FFE4A3);
        border: 2px solid #F1C873;
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 18px;
        color: #8A6A20; font-weight: 600;
    }

    /* 푸터 */
    .petlog-footer {
        text-align: center; color: #B89898; font-size: 0.85rem;
        margin-top: 40px; padding: 18px;
    }

    /* Streamlit 기본 요소 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════
# OAuth 콜백 처리
# ══════════════════════════════════════
handle_oauth_callback()


# ══════════════════════════════════════
# 로그인 페이지
# ══════════════════════════════════════
def render_login():
    st.markdown("""
    <div class="hero">
        <div class="hero-emoji">🐶🐱</div>
        <div class="hero-title">PetLog AI</div>
        <div class="hero-sub">우리 아이의 건강을 매일 기록하고<br>AI가 관리해주는 반려동물 건강 일지 🐾</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="petlog-card" style="text-align:center;">
        <div style="font-size:1.05rem; color:#6B4A4A; margin-bottom:14px; font-weight:700;">
            시작하려면 로그인해주세요
        </div>
    """, unsafe_allow_html=True)

    if GOOGLE_CLIENT_ID:
        login_url = get_google_login_url()
        st.markdown(
            f"""<div style="text-align:center;">
                <a href="{login_url}" target="_self" class="google-btn">
                    <svg width="20" height="20" viewBox="0 0 48 48">
                        <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.3 6.1 29.4 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.2-.1-2.4-.4-3.5z"/>
                        <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.3 6.1 29.4 4 24 4 16.3 4 9.7 8.4 6.3 14.7z"/>
                        <path fill="#4CAF50" d="M24 44c5.3 0 10.1-2 13.7-5.3l-6.3-5.3c-2 1.5-4.6 2.5-7.4 2.5-5.2 0-9.6-3.3-11.2-8l-6.5 5C9.5 39.5 16.2 44 24 44z"/>
                        <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.2 4.3-4 5.7l6.3 5.3C40.9 35.9 44 30.4 44 24c0-1.2-.1-2.4-.4-3.5z"/>
                    </svg>
                    Google로 시작하기
                </a>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.warning("⚠️ Google OAuth가 설정되지 않았습니다. `GOOGLE_CLIENT_ID` 시크릿을 설정해주세요.")
        with st.expander("🔧 개발 모드: 이메일로 바로 로그인"):
            dev_email = st.text_input("이메일", value="demo@petlog.ai")
            dev_name = st.text_input("이름", value="테스트 유저")
            if st.button("개발 모드 로그인", type="primary"):
                upsert_user(dev_email, dev_name, "")
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = {
                    "email": dev_email, "name": dev_name, "picture": "",
                }
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # 기능 미리보기
    st.markdown("""
    <div class="petlog-card">
        <div style="font-weight:800; color:#6B4A4A; font-size:1.1rem; margin-bottom:12px;">
            🐾 PetLog AI로 할 수 있는 일
        </div>
        <div style="color:#8B6F6F; line-height:2;">
            🐶 반려동물 프로필 등록 & 관리<br>
            📝 매일 건강 체크 입력 (식욕·활동량·대변)<br>
            📸 사진으로 AI 건강 분석 (준비 중)<br>
            📊 월별 건강 리포트 자동 생성 (준비 중)<br>
            🚨 이상 증상 감지 시 경고 알림 (준비 중)
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════
# 메인 대시보드
# ══════════════════════════════════════
SPECIES_EMOJI = {
    "강아지": "🐶",
    "고양이": "🐱",
    "토끼": "🐰",
    "햄스터": "🐹",
    "새": "🐦",
    "기타": "🐾",
}


def render_topbar(user):
    picture = user.get("picture") or ""
    img_tag = f'<img src="{picture}" alt="">' if picture else '<span style="font-size:1.5rem;">👤</span>'
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        <div class="topbar">
            <div class="topbar-user">
                {img_tag}
                <span>{user.get('name', '반려인')}님 🌸</span>
            </div>
            <div style="font-weight:800; color:#FF8FA3;">🐾 PetLog AI</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("로그아웃", key="logout_btn"):
            logout()


def render_pet_form(email: str):
    with st.form("pet_form", clear_on_submit=True):
        st.markdown("#### 🐾 새 반려동물 등록")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("이름 *", placeholder="예: 초코")
            species = st.selectbox("종류 *", list(SPECIES_EMOJI.keys()))
            breed = st.text_input("품종", placeholder="예: 말티즈")
        with c2:
            age = st.number_input("나이 (년)", min_value=0.0, max_value=40.0,
                                  value=1.0, step=0.5)
            weight = st.number_input("몸무게 (kg)", min_value=0.0, max_value=200.0,
                                     value=3.0, step=0.1)

        submitted = st.form_submit_button("🐶 등록하기", type="primary",
                                          use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("이름을 입력해주세요.")
            else:
                add_pet(email, name.strip(), species, breed.strip(),
                        float(age), float(weight), SPECIES_EMOJI.get(species, "🐾"))
                st.success(f"{SPECIES_EMOJI.get(species,'🐾')} {name} 등록 완료!")
                st.rerun()


def render_pet_list(pets, email: str):
    if not pets:
        st.markdown("""
        <div class="petlog-card" style="text-align:center; padding:40px 20px;">
            <div style="font-size:3rem; margin-bottom:8px;">🐾</div>
            <div style="color:#8B6F6F; font-size:1.05rem;">
                아직 등록된 반려동물이 없어요.<br>아래에서 첫 아이를 등록해주세요!
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("#### 💝 내 반려동물")
    today_str = date.today().isoformat()
    for pet in pets:
        c1, c2, c3 = st.columns([5, 2, 1])
        with c1:
            breed = pet.get("breed") or "-"
            today_log = get_log(pet["id"], today_str)
            badge = ""
            if today_log:
                lvl = today_log.get("alert_level", 0)
                if lvl == 0:
                    badge = '<span style="background:#DFF5E1;color:#4A8A5C;padding:3px 10px;border-radius:10px;font-size:0.75rem;font-weight:700;margin-left:8px;">✅ 오늘 기록됨</span>'
                elif lvl == 1:
                    badge = '<span style="background:#FFF0C9;color:#A07A20;padding:3px 10px;border-radius:10px;font-size:0.75rem;font-weight:700;margin-left:8px;">⚠️ 주의</span>'
                else:
                    badge = '<span style="background:#FFD5D5;color:#B5484A;padding:3px 10px;border-radius:10px;font-size:0.75rem;font-weight:800;margin-left:8px;">🚨 경고</span>'
            st.markdown(f"""
            <div class="pet-card">
                <div style="display:flex; align-items:center;">
                    <div class="pet-emoji">{pet['emoji']}</div>
                    <div>
                        <div class="pet-name">{pet['name']}{badge}</div>
                        <div class="pet-meta">
                            {pet['species']} · {breed} ·
                            {pet['age_years']:.1f}살 · {pet['weight_kg']:.1f}kg
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("📝 건강 기록", key=f"log_{pet['id']}", use_container_width=True):
                st.session_state["selected_pet_id"] = pet["id"]
                st.rerun()
        with c3:
            if st.button("🗑", key=f"del_{pet['id']}"):
                delete_pet(pet["id"], email)
                st.rerun()


def render_dashboard():
    user = st.session_state["user_info"]
    email = user["email"]

    render_topbar(user)

    pets = list_pets(email)

    # 헤더
    st.markdown(f"""
    <div class="hero" style="padding:0 0 12px;">
        <div class="hero-title" style="font-size:1.8rem;">
            안녕하세요, {user.get('name','반려인')}님! 🌸
        </div>
        <div class="hero-sub">오늘도 우리 아이들의 건강을 기록해볼까요?</div>
    </div>
    """, unsafe_allow_html=True)

    # 통계
    today_count = count_logs_today(email)
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box">
            <div class="stat-num">{len(pets)}</div>
            <div class="stat-lbl">🐾 등록된 아이</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">{today_count}</div>
            <div class="stat-lbl">📝 오늘 기록</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">0</div>
            <div class="stat-lbl">📸 사진 분석</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 반려동물 목록
    render_pet_list(pets, email)

    # 등록 폼
    with st.expander("➕ 반려동물 등록하기", expanded=(len(pets) == 0)):
        render_pet_form(email)

    # 준비 중 기능
    st.markdown("""
    <div class="petlog-card" style="background:rgba(255,240,230,0.6);">
        <div style="font-weight:800; color:#6B4A4A; margin-bottom:10px;">🚧 곧 만나요!</div>
        <div style="color:#9B7A7A; line-height:1.9;">
            📸 AI 사진 분석 · 📊 월별 리포트
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════
# 건강 기록 페이지
# ══════════════════════════════════════
def render_alert_banner(level: int, pet_name: str):
    if level == 2:
        st.markdown(f"""
        <div class="alert-banner">
            🚨 <b>{pet_name}의 이상 증상이 감지되었어요!</b><br>
            <span style="font-weight:500;">가까운 동물병원에 방문하거나 수의사와 상담을 권장드립니다.</span>
        </div>
        """, unsafe_allow_html=True)
    elif level == 1:
        st.markdown(f"""
        <div class="warn-banner">
            ⚠️ <b>{pet_name}의 상태를 주의 깊게 지켜봐주세요.</b>
            오늘 하루 컨디션을 더 자주 체크해주세요.
        </div>
        """, unsafe_allow_html=True)


def render_health_form(pet: dict, email: str):
    pet_id = pet["id"]
    sel_date = st.date_input(
        "📅 기록 날짜",
        value=date.today(),
        max_value=date.today(),
        key=f"date_{pet_id}",
    )
    date_str = sel_date.isoformat()
    existing = get_log(pet_id, date_str)

    if existing:
        st.info(f"📌 {date_str}에 이미 기록이 있어요. 아래에서 수정할 수 있습니다.")

    with st.form(f"health_form_{pet_id}"):
        st.markdown(f"#### 📝 {pet['emoji']} {pet['name']}의 오늘 건강 체크")

        c1, c2 = st.columns(2)
        with c1:
            appetite = st.select_slider(
                "🍽️ 식욕",
                options=APPETITE_LEVELS,
                value=existing["appetite"] if existing and existing.get("appetite") in APPETITE_LEVELS else "보통",
            )
            stool = st.select_slider(
                "💩 대변 상태",
                options=STOOL_LEVELS,
                value=existing["stool"] if existing and existing.get("stool") in STOOL_LEVELS else "정상",
            )
        with c2:
            activity = st.select_slider(
                "🏃 활동량",
                options=ACTIVITY_LEVELS,
                value=existing["activity"] if existing and existing.get("activity") in ACTIVITY_LEVELS else "보통",
            )

        notes = st.text_area(
            "✏️ 특이사항",
            value=existing.get("notes", "") if existing else "",
            placeholder="예: 왼쪽 다리를 조금 절뚝거려요 / 평소보다 조용해요 / 물을 많이 마셔요",
            height=100,
        )

        submitted = st.form_submit_button("💝 기록 저장하기", type="primary",
                                          use_container_width=True)
        if submitted:
            lvl = compute_alert_level(appetite, activity, stool, notes)
            upsert_daily_log(pet_id, email, date_str,
                             appetite, activity, stool, notes, lvl)
            if lvl == 2:
                st.error(f"🚨 이상 증상이 감지되었습니다. 병원 방문을 권장드려요!")
            elif lvl == 1:
                st.warning("⚠️ 조금 주의가 필요한 상태예요. 잘 지켜봐주세요.")
            else:
                st.success(f"✅ {pet['name']}의 {date_str} 기록이 저장되었어요! 🐾")
            st.rerun()


def render_calendar(pet: dict):
    pet_id = pet["id"]
    today = date.today()

    # 월 이동 상태
    cal_key = f"cal_{pet_id}"
    if cal_key not in st.session_state:
        st.session_state[cal_key] = (today.year, today.month)
    year, month = st.session_state[cal_key]

    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if st.button("◀", key=f"prev_{pet_id}"):
            y, m = year, month - 1
            if m < 1:
                y, m = y - 1, 12
            st.session_state[cal_key] = (y, m)
            st.rerun()
    with c2:
        st.markdown(
            f"<div style='text-align:center;font-weight:800;color:#6B4A4A;font-size:1.15rem;'>"
            f"📅 {year}년 {month}월</div>",
            unsafe_allow_html=True,
        )
    with c3:
        # 미래 이동 제한
        allow_next = not (year == today.year and month == today.month)
        if st.button("▶", key=f"next_{pet_id}", disabled=not allow_next):
            y, m = year, month + 1
            if m > 12:
                y, m = y + 1, 1
            st.session_state[cal_key] = (y, m)
            st.rerun()

    logs = get_logs_in_month(pet_id, year, month)

    # 캘린더 그리드 (월요일 시작)
    cal = pycal.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)

    dow_labels = ["월", "화", "수", "목", "금", "토", "일"]
    grid = '<div class="cal-grid">'
    for d in dow_labels:
        grid += f'<div class="cal-dow">{d}</div>'

    for week in weeks:
        for day in week:
            if day == 0:
                grid += '<div class="cal-day empty"></div>'
                continue
            d_iso = date(year, month, day).isoformat()
            cls = "cal-day"
            dot = ""
            log = logs.get(d_iso)
            if log:
                lvl = log.get("alert_level", 0)
                if lvl == 0:
                    cls += " ok"
                    dot = "✅"
                elif lvl == 1:
                    cls += " warn"
                    dot = "⚠️"
                else:
                    cls += " alert"
                    dot = "🚨"
            if d_iso == today.isoformat():
                cls += " today"
            grid += (
                f'<div class="{cls}">'
                f'<div>{day}</div>'
                f'<div class="cal-dot">{dot}</div>'
                f'</div>'
            )
    grid += "</div>"

    st.markdown(f'<div class="cal-wrap">{grid}'
                '<div class="legend-row">'
                '<span><span class="legend-dot" style="background:#DFF5E1;"></span>정상</span>'
                '<span><span class="legend-dot" style="background:#FFF0C9;"></span>주의</span>'
                '<span><span class="legend-dot" style="background:#FFD5D5;"></span>경고</span>'
                '</div></div>', unsafe_allow_html=True)

    # 최근 기록 리스트
    if logs:
        st.markdown("#### 📋 이번 달 기록")
        sorted_logs = sorted(logs.values(), key=lambda r: r["log_date"], reverse=True)
        for log in sorted_logs[:10]:
            lvl = log.get("alert_level", 0)
            emoji = "✅" if lvl == 0 else ("⚠️" if lvl == 1 else "🚨")
            bg = "#F5FBF5" if lvl == 0 else ("#FFF9E9" if lvl == 1 else "#FFF0F0")
            notes_html = (
                f'<div style="color:#8B6F6F;margin-top:4px;font-size:0.88rem;">'
                f'📝 {log["notes"]}</div>'
            ) if log.get("notes") else ""
            st.markdown(f"""
            <div style="background:{bg};border-radius:12px;padding:12px 16px;
                        margin-bottom:8px;border:1px solid #FFE4E4;">
                <div style="font-weight:700;color:#6B4A4A;">
                    {emoji} {log['log_date']}
                </div>
                <div style="color:#8B6F6F;font-size:0.9rem;margin-top:4px;">
                    🍽️ {log.get('appetite','-')} ·
                    🏃 {log.get('activity','-')} ·
                    💩 {log.get('stool','-')}
                </div>
                {notes_html}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="petlog-card" style="text-align:center; color:#9B7A7A;">
            아직 이번 달 기록이 없어요 🐾<br>
            위에서 오늘의 건강 체크를 시작해보세요!
        </div>
        """, unsafe_allow_html=True)


def render_health_page():
    user = st.session_state["user_info"]
    email = user["email"]
    pet_id = st.session_state.get("selected_pet_id")
    pet = get_pet(pet_id, email) if pet_id else None

    if not pet:
        st.session_state.pop("selected_pet_id", None)
        st.rerun()
        return

    render_topbar(user)

    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("← 뒤로", key="back_to_dash"):
            st.session_state.pop("selected_pet_id", None)
            st.rerun()
    with c2:
        st.markdown(
            f"<div style='font-size:1.5rem;font-weight:900;color:#6B4A4A;'>"
            f"{pet['emoji']} {pet['name']}의 건강 일지</div>",
            unsafe_allow_html=True,
        )

    # 오늘 기록의 알림 배너
    today_log = get_log(pet["id"], date.today().isoformat())
    if today_log:
        render_alert_banner(today_log.get("alert_level", 0), pet["name"])

    # 입력 폼
    st.markdown('<div class="petlog-card">', unsafe_allow_html=True)
    render_health_form(pet, email)
    st.markdown('</div>', unsafe_allow_html=True)

    # 캘린더
    render_calendar(pet)


# ══════════════════════════════════════
# Router
# ══════════════════════════════════════
if st.session_state.get("logged_in"):
    if st.session_state.get("selected_pet_id"):
        render_health_page()
    else:
        render_dashboard()
else:
    render_login()

# Footer
st.markdown(f"""
<div class="petlog-footer">
    🐾 PetLog AI · {APP_DOMAIN}<br>
    <span style="font-size:0.75rem; color:#C8A8A8;">v{APP_VERSION}</span>
</div>
""", unsafe_allow_html=True)
