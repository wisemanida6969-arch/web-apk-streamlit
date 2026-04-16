"""
PetLog AI — 반려동물 AI 건강 일지 SaaS
Phase 1: Google 로그인 + 반려동물 프로필 등록 + 메인 대시보드
Phase 2: 매일 건강 체크 + 캘린더 보기 + 이상 증상 경고
Phase 3: Claude AI 사진 분석 + 월별 건강 리포트
Phase 4: Paddle 구독 결제 (월 9,900원) + 플랜 제한
"""
import streamlit as st
import sqlite3
import os
import json
import base64
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
APP_VERSION = "2026-04-13-phase4"

# ─── Plans ───
FREE_MAX_PETS = 1
FREE_MAX_PHOTOS_PER_MONTH = 3
PRO_PRICE_KRW = 9900

ADMIN_EMAILS = [
    e.strip().lower() for e in
    os.environ.get("PETLOG_ADMIN_EMAILS",
                   "wisemanida6969@gmail.com").split(",")
    if e.strip()
]

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
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_email TEXT PRIMARY KEY,
            plan TEXT DEFAULT 'free',
            status TEXT,
            paddle_customer_id TEXT,
            paddle_subscription_id TEXT,
            paddle_transaction_id TEXT,
            current_period_end TEXT,
            cancel_at_period_end INTEGER DEFAULT 0,
            updated_at TEXT,
            FOREIGN KEY(user_email) REFERENCES users(email)
        );
        CREATE TABLE IF NOT EXISTS photo_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            photo_path TEXT,
            analysis_text TEXT,
            eye_score INTEGER,
            coat_score INTEGER,
            body_score INTEGER,
            activity_score INTEGER,
            alert_level INTEGER DEFAULT 0,
            concerns TEXT,
            created_at TEXT,
            FOREIGN KEY(pet_id) REFERENCES pets(id)
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


# ── 사진 분석 DB ──
PHOTO_DIR = Path(get_secret("PETLOG_PHOTO_DIR", "petlog_photos"))
PHOTO_DIR.mkdir(exist_ok=True)


def save_photo_analysis(pet_id: int, email: str, photo_path: str,
                        analysis: dict):
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO photo_analyses
               (pet_id, user_email, photo_path, analysis_text,
                eye_score, coat_score, body_score, activity_score,
                alert_level, concerns, created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (pet_id, email, photo_path,
             analysis.get("summary", ""),
             int(analysis.get("eye_score", 0) or 0),
             int(analysis.get("coat_score", 0) or 0),
             int(analysis.get("body_score", 0) or 0),
             int(analysis.get("activity_score", 0) or 0),
             int(analysis.get("alert_level", 0) or 0),
             json.dumps(analysis.get("concerns", []), ensure_ascii=False),
             datetime.utcnow().isoformat()),
        )
        conn.commit()


def list_photo_analyses(pet_id: int, limit: int = 20):
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM photo_analyses WHERE pet_id=?
               ORDER BY created_at DESC LIMIT ?""",
            (pet_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def count_photo_analyses_today(email: str) -> int:
    today = date.today().isoformat()
    with db_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS c FROM photo_analyses
               WHERE user_email=? AND created_at LIKE ?""",
            (email, f"{today}%"),
        ).fetchone()
        return int(row["c"]) if row else 0


def get_photo_analyses_in_month(pet_id: int, year: int, month: int):
    start = date(year, month, 1).isoformat()
    last_day = pycal.monthrange(year, month)[1]
    end = (date(year, month, last_day) + timedelta(days=1)).isoformat()
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM photo_analyses
               WHERE pet_id=? AND created_at >= ? AND created_at < ?
               ORDER BY created_at DESC""",
            (pet_id, start, end),
        ).fetchall()
        return [dict(r) for r in rows]


def count_photo_analyses_this_month(pet_id_or_email, by: str = "email") -> int:
    """이번 달 사진 분석 횟수. by='email' 또는 'pet'"""
    today = date.today()
    start = date(today.year, today.month, 1).isoformat()
    last_day = pycal.monthrange(today.year, today.month)[1]
    end = (date(today.year, today.month, last_day) + timedelta(days=1)).isoformat()
    with db_conn() as conn:
        if by == "email":
            row = conn.execute(
                """SELECT COUNT(*) AS c FROM photo_analyses
                   WHERE user_email=? AND created_at >= ? AND created_at < ?""",
                (pet_id_or_email, start, end),
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT COUNT(*) AS c FROM photo_analyses
                   WHERE pet_id=? AND created_at >= ? AND created_at < ?""",
                (pet_id_or_email, start, end),
            ).fetchone()
        return int(row["c"]) if row else 0


# ── 구독 / 플랜 ──
def get_subscription(email: str) -> dict:
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_email=?", (email,)
        ).fetchone()
        return dict(row) if row else {}


def upsert_subscription(email: str, **fields):
    sub = get_subscription(email)
    data = {
        "user_email": email,
        "plan": sub.get("plan", "free"),
        "status": sub.get("status"),
        "paddle_customer_id": sub.get("paddle_customer_id"),
        "paddle_subscription_id": sub.get("paddle_subscription_id"),
        "paddle_transaction_id": sub.get("paddle_transaction_id"),
        "current_period_end": sub.get("current_period_end"),
        "cancel_at_period_end": sub.get("cancel_at_period_end", 0),
    }
    data.update(fields)
    data["updated_at"] = datetime.utcnow().isoformat()
    with db_conn() as conn:
        conn.execute("""
            INSERT INTO subscriptions
              (user_email, plan, status, paddle_customer_id,
               paddle_subscription_id, paddle_transaction_id,
               current_period_end, cancel_at_period_end, updated_at)
            VALUES(:user_email, :plan, :status, :paddle_customer_id,
                   :paddle_subscription_id, :paddle_transaction_id,
                   :current_period_end, :cancel_at_period_end, :updated_at)
            ON CONFLICT(user_email) DO UPDATE SET
              plan=excluded.plan,
              status=excluded.status,
              paddle_customer_id=excluded.paddle_customer_id,
              paddle_subscription_id=excluded.paddle_subscription_id,
              paddle_transaction_id=excluded.paddle_transaction_id,
              current_period_end=excluded.current_period_end,
              cancel_at_period_end=excluded.cancel_at_period_end,
              updated_at=excluded.updated_at
        """, data)
        conn.commit()


def is_admin(email: str) -> bool:
    return (email or "").strip().lower() in ADMIN_EMAILS


def get_user_plan(email: str) -> str:
    """admin / pro / free"""
    if is_admin(email):
        return "admin"
    sub = get_subscription(email)
    if not sub:
        return "free"
    plan = sub.get("plan", "free")
    status = (sub.get("status") or "").lower()
    # active, trialing, past_due까지 pro로 간주 (canceled/expired는 만료일까지 유효)
    if plan == "pro" and status in ("active", "trialing", "past_due"):
        return "pro"
    # canceled인데 아직 기간이 남은 경우에도 pro 유지
    if plan == "pro" and sub.get("current_period_end"):
        try:
            if datetime.fromisoformat(sub["current_period_end"].replace("Z", "")) > datetime.utcnow():
                return "pro"
        except Exception:
            pass
    return "free"


def plan_limits(plan: str) -> dict:
    if plan in ("pro", "admin"):
        return {"max_pets": 9999, "max_photos_per_month": 9999}
    return {"max_pets": FREE_MAX_PETS, "max_photos_per_month": FREE_MAX_PHOTOS_PER_MONTH}


# ── Paddle API ──
PADDLE_API_KEY = get_secret("PADDLE_API_KEY", "")
PADDLE_API_URL = "https://api.paddle.com"
PADDLE_CLIENT_TOKEN = get_secret("PADDLE_CLIENT_TOKEN",
                                 "live_1a8fd1443de5064e970587e81c9")
PADDLE_PRICE_PETLOG_MONTHLY = get_secret("PADDLE_PRICE_PETLOG_MONTHLY", "")


def paddle_get(path: str) -> dict:
    if not PADDLE_API_KEY:
        raise RuntimeError("PADDLE_API_KEY가 설정되지 않았습니다.")
    r = requests.get(
        f"{PADDLE_API_URL}{path}",
        headers={"Authorization": f"Bearer {PADDLE_API_KEY}"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def paddle_post(path: str, payload: dict) -> dict:
    if not PADDLE_API_KEY:
        raise RuntimeError("PADDLE_API_KEY가 설정되지 않았습니다.")
    r = requests.post(
        f"{PADDLE_API_URL}{path}",
        headers={
            "Authorization": f"Bearer {PADDLE_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def sync_plan_from_transaction(email: str, txn_id: str) -> bool:
    """Paddle 결제 완료 후 transaction → subscription 조회해 DB 업데이트."""
    try:
        txn = paddle_get(f"/transactions/{txn_id}").get("data", {})
        sub_id = txn.get("subscription_id")
        customer_id = txn.get("customer_id")
        if not sub_id:
            return False
        sub = paddle_get(f"/subscriptions/{sub_id}").get("data", {})
        status = sub.get("status", "active")
        period = (sub.get("current_billing_period") or {})
        ends_at = period.get("ends_at") or sub.get("next_billed_at") or ""
        cancel_flag = 1 if sub.get("scheduled_change", {}).get("action") == "cancel" else 0
        upsert_subscription(
            email,
            plan="pro",
            status=status,
            paddle_customer_id=customer_id,
            paddle_subscription_id=sub_id,
            paddle_transaction_id=txn_id,
            current_period_end=ends_at,
            cancel_at_period_end=cancel_flag,
        )
        return True
    except Exception as e:
        print(f"[Paddle] sync error: {e}")
        return False


def sync_plan_from_email(email: str) -> bool:
    """이메일로 고객의 활성 구독 찾기 (fallback)."""
    try:
        # 1. 고객 검색
        cust = paddle_get(f"/customers?email={email}").get("data", [])
        if not cust:
            return False
        customer_id = cust[0]["id"]
        # 2. 구독 목록
        subs = paddle_get(f"/subscriptions?customer_id={customer_id}").get("data", [])
        if not subs:
            return False
        # 가장 최근 활성 구독 선택
        subs.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        sub = next((s for s in subs if s.get("status") in ("active", "trialing", "past_due")), subs[0])
        period = (sub.get("current_billing_period") or {})
        ends_at = period.get("ends_at") or sub.get("next_billed_at") or ""
        cancel_flag = 1 if sub.get("scheduled_change", {}).get("action") == "cancel" else 0
        upsert_subscription(
            email,
            plan="pro" if sub.get("status") in ("active", "trialing", "past_due") else "free",
            status=sub.get("status"),
            paddle_customer_id=customer_id,
            paddle_subscription_id=sub["id"],
            current_period_end=ends_at,
            cancel_at_period_end=cancel_flag,
        )
        return True
    except Exception as e:
        print(f"[Paddle] email sync error: {e}")
        return False


def cancel_subscription(email: str) -> bool:
    sub = get_subscription(email)
    sub_id = sub.get("paddle_subscription_id")
    if not sub_id:
        return False
    try:
        paddle_post(f"/subscriptions/{sub_id}/cancel",
                    {"effective_from": "next_billing_period"})
        upsert_subscription(email, cancel_at_period_end=1, status="canceled")
        return True
    except Exception as e:
        print(f"[Paddle] cancel error: {e}")
        return False


init_db()


# ══════════════════════════════════════
# Claude AI 사진 분석
# ══════════════════════════════════════
ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY", "")


def analyze_pet_photo(image_bytes: bytes, media_type: str, pet: dict) -> dict:
    """Claude vision으로 반려동물 사진 건강 분석.

    반환: {summary, eye_score, coat_score, body_score, activity_score,
           alert_level, concerns: [str]}
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY가 설정되지 않았습니다. Streamlit secrets에 추가해주세요."
        )

    try:
        from anthropic import Anthropic
    except ImportError:
        raise RuntimeError("anthropic 패키지가 설치되지 않았습니다. requirements.txt 확인.")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    system_prompt = (
        "You are a compassionate veterinary assistant AI. "
        "Analyze the uploaded pet photo and assess visible health indicators. "
        "Always respond in Korean. Be warm but honest. "
        "Output ONLY valid JSON — no prose, no code fences."
    )

    user_prompt = f"""
이 반려동물 사진을 보고 건강 상태를 분석해주세요.

반려동물 정보:
- 이름: {pet.get('name')}
- 종류: {pet.get('species')}
- 품종: {pet.get('breed') or '미상'}
- 나이: {pet.get('age_years')}살
- 몸무게: {pet.get('weight_kg')}kg

다음 JSON 형식으로만 응답하세요:
{{
  "summary": "전반적 건강 평가 (2-3문장, 따뜻한 말투)",
  "eye_score": 1-10 정수 (눈 상태: 맑음/충혈/분비물 등),
  "coat_score": 1-10 정수 (털 상태: 윤기/빠짐/탈모),
  "body_score": 1-10 정수 (체형: 마름/비만/적정),
  "activity_score": 1-10 정수 (사진 속 활기/자세),
  "alert_level": 0|1|2 (0=정상, 1=주의, 2=경고: 병원 방문 필요),
  "concerns": ["관찰된 우려 사항 1", "우려 사항 2"],
  "recommendations": ["권장 사항 1", "권장 사항 2"]
}}

사진에서 명확히 보이지 않는 항목은 5점(보통)으로 평가하고, concerns에
"사진으로는 판단이 어려워요"라고 써주세요.
""".strip()

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64,
                    },
                },
                {"type": "text", "text": user_prompt},
            ],
        }],
    )

    text = resp.content[0].text.strip()
    # JSON 코드 펜스 제거
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # fallback: 줄 내용을 요약으로
        data = {
            "summary": text[:500],
            "eye_score": 5, "coat_score": 5, "body_score": 5,
            "activity_score": 5, "alert_level": 0,
            "concerns": ["AI 응답 파싱에 실패했어요. 원문을 확인해주세요."],
            "recommendations": [],
        }
    return data


def generate_monthly_report_text(pet: dict, logs: list, analyses: list,
                                 year: int, month: int) -> str:
    """Claude로 월별 종합 건강 리포트 텍스트 생성."""
    if not ANTHROPIC_API_KEY:
        return _fallback_report(pet, logs, analyses, year, month)

    try:
        from anthropic import Anthropic
    except ImportError:
        return _fallback_report(pet, logs, analyses, year, month)

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    logs_summary = [
        {
            "date": l["log_date"],
            "appetite": l.get("appetite"),
            "activity": l.get("activity"),
            "stool": l.get("stool"),
            "notes": (l.get("notes") or "")[:200],
            "alert_level": l.get("alert_level", 0),
        }
        for l in logs
    ]
    analyses_summary = [
        {
            "date": a["created_at"][:10],
            "summary": (a.get("analysis_text") or "")[:300],
            "eye_score": a.get("eye_score"),
            "coat_score": a.get("coat_score"),
            "body_score": a.get("body_score"),
            "activity_score": a.get("activity_score"),
            "alert_level": a.get("alert_level", 0),
        }
        for a in analyses
    ]

    prompt = f"""
아래는 반려동물 {pet['name']} ({pet['species']}, {pet.get('breed') or '품종 미상'},
{pet.get('age_years')}살)의 {year}년 {month}월 건강 기록이에요.

일별 건강 체크 ({len(logs)}건):
{json.dumps(logs_summary, ensure_ascii=False, indent=2)}

AI 사진 분석 기록 ({len(analyses)}건):
{json.dumps(analyses_summary, ensure_ascii=False, indent=2)}

이 데이터를 바탕으로 한국어로 월별 종합 건강 리포트를 작성해주세요.
따뜻하고 친근한 말투로, 반려인이 읽기 쉽게 4-6개 문단으로요.
다음 내용을 포함해주세요:
1. 이번 달 전반적 건강 상태 요약
2. 긍정적인 변화 또는 잘 관리된 부분
3. 주의가 필요했던 부분 (있다면)
4. 다음 달을 위한 따뜻한 제안

마크다운은 사용하지 말고 일반 텍스트로만 써주세요.
""".strip()

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def _fallback_report(pet, logs, analyses, year, month) -> str:
    n_logs = len(logs)
    n_ana = len(analyses)
    alerts = sum(1 for l in logs if l.get("alert_level", 0) >= 2)
    warns = sum(1 for l in logs if l.get("alert_level", 0) == 1)
    return (
        f"🐾 {pet['name']}의 {year}년 {month}월 건강 요약\n\n"
        f"이번 달 건강 체크 {n_logs}건, AI 사진 분석 {n_ana}건을 기록했어요.\n"
        f"정상 {n_logs - alerts - warns}일 · 주의 {warns}일 · 경고 {alerts}일.\n\n"
        "(AI 종합 리포트는 ANTHROPIC_API_KEY를 설정하면 활성화됩니다.)"
    )


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


def handle_paddle_callback():
    """?paddle_txn=... 또는 ?paddle_success=1 쿼리 파라미터를 처리."""
    if not st.session_state.get("logged_in"):
        return
    email = st.session_state.get("user_info", {}).get("email", "")
    if not email:
        return

    txn_id = st.query_params.get("paddle_txn")
    success = st.query_params.get("paddle_success")
    if not (txn_id or success):
        return

    synced = False
    if txn_id:
        synced = sync_plan_from_transaction(email, txn_id)
    if not synced:
        synced = sync_plan_from_email(email)

    st.session_state["paddle_result"] = "success" if synced else "pending"
    st.query_params.clear()
    st.rerun()


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
    /* 입력창 — 배경 + 글씨색 + placeholder 모두 명확히 */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stDateInput input,
    .stTimeInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        border: 1px solid #FFD6D6 !important;
        background: #ffffff !important;
        color: #3A2A2A !important;
    }
    .stTextInput input::placeholder,
    .stNumberInput input::placeholder,
    .stTextArea textarea::placeholder,
    .stDateInput input::placeholder {
        color: #9B7A7A !important;
        opacity: 1 !important;
    }
    /* Selectbox 내부 선택된 값 글씨 */
    .stSelectbox div[data-baseweb="select"] span,
    .stMultiSelect div[data-baseweb="select"] span {
        color: #3A2A2A !important;
    }
    /* Selectbox 드롭다운 옵션 */
    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] li {
        color: #3A2A2A !important;
        background: #ffffff !important;
    }
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="menu"] li:hover {
        background: #FFF0F5 !important;
    }
    /* 라벨 (입력창 위 텍스트) */
    .stTextInput label,
    .stNumberInput label,
    .stTextArea label,
    .stDateInput label,
    .stTimeInput label,
    .stSelectbox label,
    .stFileUploader label,
    .stRadio label,
    .stCheckbox label {
        color: #5B4A4A !important;
        font-weight: 600 !important;
    }
    /* 파일 업로더 배경 */
    .stFileUploader > div {
        background: #ffffff !important;
        border: 1px dashed #FFD6D6 !important;
        border-radius: 12px !important;
    }
    .stFileUploader > div > div,
    .stFileUploader small {
        color: #5B4A4A !important;
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

    /* AI 스코어 바 */
    .score-row {
        display:flex; gap:10px; margin: 12px 0;
        flex-wrap: wrap;
    }
    .score-item {
        flex:1; min-width: 140px;
        background: rgba(255,255,255,0.7);
        border-radius: 14px; padding: 12px 14px;
        border: 1px solid #FFE0E0;
    }
    .score-label { font-size:0.82rem; color:#8B6F6F; margin-bottom:6px; font-weight:600;}
    .score-bar-wrap {
        height: 8px; background: #FFEBEB; border-radius: 4px; overflow:hidden;
        margin-top: 4px;
    }
    .score-bar-fill {
        height: 100%; border-radius: 4px;
        background: linear-gradient(90deg, #FFB5A7, #FFA6C1);
    }
    .score-value { font-size: 1.15rem; font-weight: 800; color: #6B4A4A; }

    .concern-pill {
        display:inline-block; background:#FFECEC; color:#8B4A4A;
        padding:4px 10px; border-radius:10px; font-size:0.82rem;
        margin:3px 4px 3px 0; border:1px solid #FFD0D0;
    }
    .rec-pill {
        display:inline-block; background:#FFF6E8; color:#8A6A20;
        padding:4px 10px; border-radius:10px; font-size:0.82rem;
        margin:3px 4px 3px 0; border:1px solid #F1D89B;
    }

    .report-box {
        background: linear-gradient(135deg, #FFF9F0 0%, #FFF0F5 100%);
        border-radius: 18px; padding: 24px 26px;
        border: 1px solid #FFD6D6;
        line-height: 1.9; color: #5B4A4A;
        white-space: pre-wrap;
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
# OAuth 콜백 & Paddle 콜백 처리
# ══════════════════════════════════════
handle_oauth_callback()
handle_paddle_callback()


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
    plan = get_user_plan(user.get("email", ""))
    plan_badge = ""
    if plan == "admin":
        plan_badge = '<span style="background:linear-gradient(135deg,#F1C873,#F3A34C);color:white;padding:3px 10px;border-radius:10px;font-size:0.72rem;font-weight:800;margin-left:8px;">👑 ADMIN</span>'
    elif plan == "pro":
        plan_badge = '<span style="background:linear-gradient(135deg,#FFB5A7,#FFA6C1);color:white;padding:3px 10px;border-radius:10px;font-size:0.72rem;font-weight:800;margin-left:8px;">💝 PRO</span>'
    else:
        plan_badge = '<span style="background:#F5F0F0;color:#9B7A7A;padding:3px 10px;border-radius:10px;font-size:0.72rem;font-weight:700;margin-left:8px;">FREE</span>'

    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        st.markdown(f"""
        <div class="topbar">
            <div class="topbar-user">
                {img_tag}
                <span>{user.get('name', '반려인')}님 🌸{plan_badge}</span>
            </div>
            <div style="font-weight:800; color:#FF8FA3;">🐾 PetLog AI</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if not st.session_state.get("show_upgrade"):
            if st.button("💳 구독", key="upg_btn"):
                st.session_state["show_upgrade"] = True
                st.session_state.pop("selected_pet_id", None)
                st.rerun()
    with col3:
        if st.button("로그아웃", key="logout_btn"):
            logout()


def render_pet_form(email: str):
    plan = get_user_plan(email)
    limits = plan_limits(plan)
    existing_count = len(list_pets(email))
    if existing_count >= limits["max_pets"]:
        st.markdown(f"""
        <div class="warn-banner">
            🔒 <b>무료 플랜은 반려동물 {FREE_MAX_PETS}마리까지 등록할 수 있어요.</b><br>
            PetLog Pro (월 {PRO_PRICE_KRW:,}원)로 업그레이드하면 무제한으로 등록할 수 있습니다.
        </div>
        """, unsafe_allow_html=True)
        if st.button("💝 Pro로 업그레이드하기", key="upg_from_pet", use_container_width=True):
            st.session_state["show_upgrade"] = True
            st.rerun()
        return

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
    photo_count = count_photo_analyses_today(email)
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
            <div class="stat-num">{photo_count}</div>
            <div class="stat-lbl">📸 사진 분석</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 반려동물 목록
    render_pet_list(pets, email)

    # 등록 폼
    with st.expander("➕ 반려동물 등록하기", expanded=(len(pets) == 0)):
        render_pet_form(email)

    # 플랜별 액션 카드
    plan = get_user_plan(email)
    if plan == "free":
        st.markdown(f"""
        <div class="petlog-card" style="background:linear-gradient(135deg,#FFF9F0,#FFECEC);
                                        border:2px solid #FFB5A7;">
            <div style="font-weight:900; color:#6B4A4A; margin-bottom:6px; font-size:1.05rem;">
                💝 PetLog Pro로 더 알차게!
            </div>
            <div style="color:#8B6F6F; line-height:1.8; margin-bottom:10px;">
                반려동물 무제한 · 사진 분석 무제한 · 월별 AI 리포트<br>
                <b style="color:#FF8FA3;">월 {PRO_PRICE_KRW:,}원</b> — 언제든 취소 가능
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💝 Pro 알아보기", key="upg_dash", use_container_width=True):
            st.session_state["show_upgrade"] = True
            st.rerun()


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


def _score_bar_html(label: str, emoji: str, score) -> str:
    try:
        s = int(score or 0)
    except (TypeError, ValueError):
        s = 0
    s = max(0, min(10, s))
    pct = s * 10
    return (
        f'<div class="score-item">'
        f'<div class="score-label">{emoji} {label}</div>'
        f'<div class="score-value">{s}/10</div>'
        f'<div class="score-bar-wrap"><div class="score-bar-fill" style="width:{pct}%"></div></div>'
        f'</div>'
    )


def render_analysis_result(analysis: dict):
    alert_level = int(analysis.get("alert_level", 0) or 0)
    if alert_level == 2:
        st.markdown(f"""
        <div class="alert-banner">
            🚨 <b>이상 징후가 발견되었어요!</b><br>
            <span style="font-weight:500;">AI 분석 결과 병원 방문이 권장됩니다. 수의사와 상담하세요.</span>
        </div>
        """, unsafe_allow_html=True)
    elif alert_level == 1:
        st.markdown("""
        <div class="warn-banner">
            ⚠️ <b>조금 주의가 필요해 보여요.</b> 상태를 지켜보시고 컨디션이 계속되면 병원에 문의해주세요.
        </div>
        """, unsafe_allow_html=True)

    # 요약
    summary = analysis.get("summary", "") or "(요약 없음)"
    st.markdown(f"""
    <div class="petlog-card">
        <div style="font-weight:800;color:#6B4A4A;margin-bottom:10px;">🤖 AI 종합 평가</div>
        <div style="color:#5B4A4A;line-height:1.8;">{summary}</div>
    </div>
    """, unsafe_allow_html=True)

    # 스코어 바
    bars = (
        _score_bar_html("눈 상태", "👁️", analysis.get("eye_score"))
        + _score_bar_html("털 상태", "🧶", analysis.get("coat_score"))
        + _score_bar_html("체형", "⚖️", analysis.get("body_score"))
        + _score_bar_html("활동성", "🏃", analysis.get("activity_score"))
    )
    st.markdown(f'<div class="score-row">{bars}</div>', unsafe_allow_html=True)

    # 우려 / 권장
    concerns = analysis.get("concerns") or []
    if isinstance(concerns, str):
        try:
            concerns = json.loads(concerns)
        except Exception:
            concerns = [concerns]
    if concerns:
        pills = "".join(f'<span class="concern-pill">⚠️ {c}</span>' for c in concerns)
        st.markdown(f"""
        <div class="petlog-card">
            <div style="font-weight:700;color:#6B4A4A;margin-bottom:8px;">🔎 관찰된 점</div>
            {pills}
        </div>
        """, unsafe_allow_html=True)

    recs = analysis.get("recommendations") or []
    if recs:
        pills = "".join(f'<span class="rec-pill">💡 {r}</span>' for r in recs)
        st.markdown(f"""
        <div class="petlog-card">
            <div style="font-weight:700;color:#6B4A4A;margin-bottom:8px;">💝 권장 사항</div>
            {pills}
        </div>
        """, unsafe_allow_html=True)


def render_photo_analysis_tab(pet: dict, email: str):
    pet_id = pet["id"]

    plan = get_user_plan(email)
    limits = plan_limits(plan)
    used = count_photo_analyses_this_month(email, by="email")
    remaining = max(0, limits["max_photos_per_month"] - used)

    st.markdown(f"#### 📸 {pet['name']}의 사진으로 건강 체크")
    if plan in ("pro", "admin"):
        st.markdown(
            '<div style="color:#4A8A5C;margin-bottom:8px;font-weight:600;">'
            '✨ Pro 플랜: 이번 달 사진 분석 무제한</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"""
        <div style="color:#8B6F6F;margin-bottom:8px;">
            🆓 무료 플랜: 이번 달 <b>{used} / {FREE_MAX_PHOTOS_PER_MONTH}</b>회 사용
            ({remaining}회 남음)
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div style="color:#8B6F6F;margin-bottom:12px;">'
        '또렷한 얼굴/전신 사진을 올려주시면 Claude AI가 눈·털·체형·활동성을 분석해드려요.'
        '</div>',
        unsafe_allow_html=True,
    )

    if plan == "free" and remaining <= 0:
        st.markdown(f"""
        <div class="warn-banner">
            🔒 <b>이번 달 무료 분석 {FREE_MAX_PHOTOS_PER_MONTH}회를 모두 사용했어요.</b><br>
            PetLog Pro (월 {PRO_PRICE_KRW:,}원)로 업그레이드하면 무제한으로 분석할 수 있습니다.
        </div>
        """, unsafe_allow_html=True)
        if st.button("💝 Pro로 업그레이드하기", key=f"upg_photo_{pet_id}",
                     use_container_width=True):
            st.session_state["show_upgrade"] = True
            st.rerun()
        return

    uploaded = None
    uploaded_name = None
    uploaded_type = None

    # 단일 file_uploader — 모바일에서 "사진 촬영" + "파일 선택" 둘 다 제공
    up = st.file_uploader(
        "📷 사진 촬영 또는 앨범에서 선택",
        type=["jpg", "jpeg", "png", "webp"],
        key=f"upl_{pet_id}",
    )

    # 모바일에서 file input 클릭 시 네이티브 카메라가 바로 열리도록
    # capture="environment" 속성을 JS로 주입
    import streamlit.components.v1 as _photo_comp
    _photo_comp.html(f"""
    <script>
    (function() {{
        var isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        if (!isMobile) return;
        // Streamlit file_uploader의 <input type="file"> 를 찾아 capture 속성 추가
        var root = window.parent.document;
        function addCapture() {{
            var inputs = root.querySelectorAll('input[type="file"]');
            inputs.forEach(function(inp) {{
                if (!inp.hasAttribute('capture')) {{
                    inp.setAttribute('capture', 'environment');
                    inp.setAttribute('accept', 'image/*');
                }}
            }});
        }}
        addCapture();
        // DOM 변경 대비 MutationObserver
        var obs = new MutationObserver(addCapture);
        obs.observe(root.body, {{childList: true, subtree: true}});
        setTimeout(function() {{ obs.disconnect(); }}, 10000);
    }})();
    </script>
    """, height=0)

    if up is not None:
        uploaded = up
        uploaded_name = up.name or f"photo_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
        uploaded_type = up.type or "image/jpeg"

    if uploaded is not None:
        image_bytes = uploaded.getvalue()
        st.image(image_bytes, caption=f"{pet['emoji']} {pet['name']}", width=320)

        if st.button("🤖 Claude AI로 분석하기", type="primary",
                     key=f"ana_{pet_id}", use_container_width=True):
            with st.spinner("🐾 AI가 사진을 살펴보고 있어요..."):
                try:
                    mt = uploaded_type or "image/jpeg"
                    if mt == "image/jpg":
                        mt = "image/jpeg"
                    analysis = analyze_pet_photo(image_bytes, mt, pet)

                    # 사진 저장
                    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    ext = (uploaded_name.rsplit(".", 1)[-1].lower()
                           if uploaded_name and "." in uploaded_name else "jpg")
                    path = PHOTO_DIR / f"{pet_id}_{ts}.{ext}"
                    path.write_bytes(image_bytes)

                    save_photo_analysis(pet_id, email, str(path), analysis)
                    st.session_state[f"last_ana_{pet_id}"] = analysis
                    st.rerun()
                except Exception as e:
                    st.error(f"분석 실패: {e}")

    # 마지막 분석 결과
    last = st.session_state.get(f"last_ana_{pet_id}")
    if last:
        st.markdown("---")
        st.markdown("### 🔍 방금 분석 결과")
        render_analysis_result(last)

    # 이전 분석 기록
    history = list_photo_analyses(pet_id, limit=10)
    if history:
        st.markdown("---")
        st.markdown("#### 📚 이전 AI 분석 기록")
        for h in history:
            concerns = h.get("concerns") or "[]"
            try:
                concerns_list = json.loads(concerns)
            except Exception:
                concerns_list = []
            lvl = h.get("alert_level", 0)
            emoji = "✅" if lvl == 0 else ("⚠️" if lvl == 1 else "🚨")
            bg = "#F5FBF5" if lvl == 0 else ("#FFF9E9" if lvl == 1 else "#FFF0F0")
            date_str = (h.get("created_at") or "")[:10]
            with st.expander(f"{emoji} {date_str} — 눈 {h.get('eye_score','?')}/10 · "
                             f"털 {h.get('coat_score','?')}/10 · "
                             f"체형 {h.get('body_score','?')}/10 · "
                             f"활동 {h.get('activity_score','?')}/10"):
                if h.get("photo_path") and Path(h["photo_path"]).exists():
                    try:
                        st.image(h["photo_path"], width=240)
                    except Exception:
                        pass
                st.markdown(
                    f'<div style="background:{bg};padding:12px 14px;border-radius:10px;'
                    f'color:#5B4A4A;line-height:1.7;">'
                    f'{h.get("analysis_text","")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if concerns_list:
                    st.markdown(
                        "".join(f'<span class="concern-pill">⚠️ {c}</span>'
                                for c in concerns_list),
                        unsafe_allow_html=True,
                    )


def render_monthly_report_tab(pet: dict, email: str):
    pet_id = pet["id"]
    today = date.today()

    rkey = f"rep_{pet_id}"
    if rkey not in st.session_state:
        st.session_state[rkey] = (today.year, today.month)
    year, month = st.session_state[rkey]

    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if st.button("◀", key=f"rprev_{pet_id}"):
            y, m = year, month - 1
            if m < 1:
                y, m = y - 1, 12
            st.session_state[rkey] = (y, m)
            st.rerun()
    with c2:
        st.markdown(
            f"<div style='text-align:center;font-weight:800;color:#6B4A4A;"
            f"font-size:1.25rem;'>📊 {year}년 {month}월 건강 리포트</div>",
            unsafe_allow_html=True,
        )
    with c3:
        allow_next = not (year == today.year and month == today.month)
        if st.button("▶", key=f"rnext_{pet_id}", disabled=not allow_next):
            y, m = year, month + 1
            if m > 12:
                y, m = y + 1, 1
            st.session_state[rkey] = (y, m)
            st.rerun()

    logs = list(get_logs_in_month(pet_id, year, month).values())
    analyses = get_photo_analyses_in_month(pet_id, year, month)

    total_days = pycal.monthrange(year, month)[1]
    n_logs = len(logs)
    n_ana = len(analyses)
    alerts = sum(1 for l in logs if l.get("alert_level", 0) >= 2)
    warns = sum(1 for l in logs if l.get("alert_level", 0) == 1)
    ok = n_logs - alerts - warns
    coverage = int((n_logs / total_days) * 100) if total_days else 0

    # 통계 카드
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box">
            <div class="stat-num">{coverage}%</div>
            <div class="stat-lbl">📅 기록 커버리지</div>
        </div>
        <div class="stat-box">
            <div class="stat-num" style="color:#4A8A5C;">{ok}</div>
            <div class="stat-lbl">✅ 정상일</div>
        </div>
        <div class="stat-box">
            <div class="stat-num" style="color:#A07A20;">{warns}</div>
            <div class="stat-lbl">⚠️ 주의일</div>
        </div>
        <div class="stat-box">
            <div class="stat-num" style="color:#B5484A;">{alerts}</div>
            <div class="stat-lbl">🚨 경고일</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if n_logs == 0 and n_ana == 0:
        st.markdown("""
        <div class="petlog-card" style="text-align:center;color:#9B7A7A;">
            이 달에는 아직 기록이 없어요 🐾<br>
            건강 체크나 사진 분석을 먼저 진행해주세요.
        </div>
        """, unsafe_allow_html=True)
        return

    # AI 요약
    report_cache_key = f"reptxt_{pet_id}_{year}_{month}"
    if st.button("🤖 AI 월간 종합 리포트 생성하기",
                 type="primary", use_container_width=True,
                 key=f"genrep_{pet_id}_{year}_{month}"):
        with st.spinner("📝 Claude가 이번 달을 정리하고 있어요..."):
            try:
                text = generate_monthly_report_text(pet, logs, analyses, year, month)
                st.session_state[report_cache_key] = text
            except Exception as e:
                st.error(f"리포트 생성 실패: {e}")

    report_text = st.session_state.get(report_cache_key)
    if report_text:
        st.markdown("#### 💌 AI가 쓴 이번 달 이야기")
        st.markdown(f'<div class="report-box">{report_text}</div>',
                    unsafe_allow_html=True)

    # AI 사진 평균 점수
    if analyses:
        def _avg(key):
            vals = [a.get(key) for a in analyses if a.get(key) is not None]
            return round(sum(vals) / len(vals), 1) if vals else 0

        st.markdown("#### 📸 이번 달 AI 사진 분석 평균")
        bars = (
            _score_bar_html("눈 상태", "👁️", _avg("eye_score"))
            + _score_bar_html("털 상태", "🧶", _avg("coat_score"))
            + _score_bar_html("체형", "⚖️", _avg("body_score"))
            + _score_bar_html("활동성", "🏃", _avg("activity_score"))
        )
        st.markdown(f'<div class="score-row">{bars}</div>',
                    unsafe_allow_html=True)


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

    tab_daily, tab_photo, tab_report = st.tabs(
        ["📝 매일 체크", "📸 AI 사진 분석", "📊 월별 리포트"]
    )

    with tab_daily:
        st.markdown('<div class="petlog-card">', unsafe_allow_html=True)
        render_health_form(pet, email)
        st.markdown('</div>', unsafe_allow_html=True)
        render_calendar(pet)

    with tab_photo:
        render_photo_analysis_tab(pet, email)

    with tab_report:
        render_monthly_report_tab(pet, email)


# ══════════════════════════════════════
# Pricing / Upgrade 페이지
# ══════════════════════════════════════
import streamlit.components.v1 as paddle_components


def render_pricing_checkout(user: dict):
    """PostGenie와 동일한 window.top 탈출 방식 Paddle.js 체크아웃."""
    email = user.get("email", "")
    price_id = PADDLE_PRICE_PETLOG_MONTHLY or ""
    client_token = PADDLE_CLIENT_TOKEN
    app_host = get_secret("PETLOG_APP_URL", f"https://{APP_DOMAIN}")

    html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <script>
        (function() {{
            var top = window.top;
            if (top._petlogPaddleReady) return;
            if (!top.document.getElementById('petlog-paddle-sdk')) {{
                var s = top.document.createElement('script');
                s.id = 'petlog-paddle-sdk';
                s.src = 'https://cdn.paddle.com/paddle/v2/paddle.js';
                s.onload = function() {{
                    top.Paddle.Initialize({{
                        token: '{client_token}',
                        environment: 'production',
                        eventCallback: function(ev) {{
                            if (ev && ev.name === 'checkout.completed') {{
                                var txn = (ev.data && ev.data.transaction_id) || '';
                                var sep = '{app_host}'.indexOf('?') >= 0 ? '&' : '?';
                                top.location.href = '{app_host}' + sep + 'paddle_txn=' + txn;
                            }}
                        }}
                    }});
                    top._petlogPaddleReady = true;
                }};
                top.document.head.appendChild(s);
            }}
        }})();

        function openPetlogCheckout() {{
            var top = window.top;
            var priceId = '{price_id}';
            if (!priceId) {{
                alert('가격 ID가 설정되지 않았습니다. PADDLE_PRICE_PETLOG_MONTHLY 시크릿을 확인해주세요.');
                return;
            }}
            function doOpen() {{
                top.Paddle.Checkout.open({{
                    items: [{{ priceId: priceId, quantity: 1 }}],
                    customer: {{ email: '{email}' }},
                    customData: {{ user_email: '{email}' }},
                    settings: {{
                        successUrl: '{app_host}?paddle_success=1'
                    }}
                }});
            }}
            if (top.Paddle && top._petlogPaddleReady) {{ doOpen(); }}
            else {{
                setTimeout(function() {{
                    if (top.Paddle) doOpen();
                    else alert('결제 시스템을 불러오는 중이에요. 잠시 후 다시 시도해주세요.');
                }}, 1500);
            }}
        }}
    </script>
    <style>
        * {{ font-family: 'Inter', -apple-system, sans-serif; box-sizing: border-box;
             margin: 0; padding: 0; }}
        body {{ background: transparent; }}
        .pricing-wrap {{ max-width: 560px; margin: 0 auto; padding: 12px; }}
        .pricing-header {{ text-align: center; margin-bottom: 18px; }}
        .pricing-header h1 {{
            font-size: 1.8rem; font-weight: 900; color: #6B4A4A;
            margin-bottom: 4px; letter-spacing: -0.02em;
        }}
        .pricing-header p {{ color: #9B7A7A; font-size: 0.98rem; }}

        .card {{
            background: linear-gradient(135deg, #FFF9F0 0%, #FFECEC 100%);
            border: 2px solid #FFB5A7;
            border-radius: 24px;
            padding: 28px 28px 24px;
            text-align: center;
            box-shadow: 0 8px 28px rgba(255, 181, 167, 0.25);
            position: relative;
        }}
        .badge {{
            position: absolute; top: -14px; left: 50%; transform: translateX(-50%);
            background: linear-gradient(135deg, #FFB5A7, #FFA6C1);
            color: white; padding: 5px 18px; border-radius: 20px;
            font-weight: 800; font-size: 0.82rem;
            box-shadow: 0 4px 12px rgba(255, 166, 193, 0.4);
        }}
        .plan-emoji {{ font-size: 2.8rem; margin-bottom: 4px; }}
        .plan-name {{ font-size: 1.5rem; font-weight: 900; color: #6B4A4A; margin-bottom: 4px; }}
        .plan-price {{
            font-size: 3rem; font-weight: 900;
            background: linear-gradient(135deg, #FF8FA3, #FFB085);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
        }}
        .plan-per {{ color: #9B7A7A; font-size: 0.9rem; margin-bottom: 18px; }}

        .features {{ list-style: none; padding: 0; text-align: left; margin: 20px 0; }}
        .features li {{ color: #5B4A4A; font-size: 0.95rem;
                       margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }}
        .features li b {{ color: #6B4A4A; }}

        .btn {{
            width: 100%; padding: 14px 0; border: none; border-radius: 14px;
            font-size: 1.05rem; font-weight: 800; cursor: pointer;
            background: linear-gradient(135deg, #FFB5A7, #FFA6C1);
            color: white;
            box-shadow: 0 4px 16px rgba(255, 166, 193, 0.4);
            transition: all 0.25s;
        }}
        .btn:hover {{ transform: translateY(-2px);
                      box-shadow: 0 8px 28px rgba(255, 166, 193, 0.55); }}

        .secure {{ text-align: center; margin-top: 16px;
                   font-size: 0.8rem; color: #B89898; }}

        .compare {{
            display: flex; gap: 12px; margin-bottom: 20px;
        }}
        .col {{
            flex: 1; background: rgba(255,255,255,0.7);
            border-radius: 16px; padding: 18px;
            border: 1px solid #FFE0E0;
        }}
        .col h3 {{ font-size: 1rem; color: #6B4A4A; margin-bottom: 8px; }}
        .col .p {{ font-weight: 800; color: #FF8FA3; font-size: 1.4rem; margin-bottom: 10px; }}
        .col ul {{ list-style: none; padding: 0; }}
        .col li {{ font-size: 0.85rem; color: #8B6F6F; padding: 3px 0; }}
    </style>

    <div class="pricing-wrap">
        <div class="pricing-header">
            <h1>🐾 PetLog Pro</h1>
            <p>우리 아이 건강을 더 세심하게 챙겨보세요</p>
        </div>

        <div class="compare">
            <div class="col">
                <h3>🆓 무료</h3>
                <div class="p">₩0</div>
                <ul>
                    <li>🐶 반려동물 1마리</li>
                    <li>📸 사진 분석 3회/월</li>
                    <li>📝 매일 건강 체크</li>
                </ul>
            </div>
            <div class="col" style="background:linear-gradient(135deg,#FFF9F0,#FFECEC);
                                    border:2px solid #FFB5A7;">
                <h3>💝 Pro</h3>
                <div class="p">₩9,900<span style="font-size:0.85rem;color:#9B7A7A;">/월</span></div>
                <ul>
                    <li>🐾 반려동물 <b>무제한</b></li>
                    <li>📸 사진 분석 <b>무제한</b></li>
                    <li>📊 월별 AI 리포트</li>
                    <li>🚨 실시간 이상 증상 알림</li>
                </ul>
            </div>
        </div>

        <div class="card">
            <div class="badge">👑 가장 인기</div>
            <div class="plan-emoji">💝</div>
            <div class="plan-name">PetLog Pro</div>
            <div class="plan-price">₩9,900</div>
            <div class="plan-per">월 구독 · 언제든 취소 가능</div>
            <ul class="features">
                <li>✅ 반려동물 <b>무제한</b> 등록</li>
                <li>✅ Claude AI 사진 분석 <b>무제한</b></li>
                <li>✅ 월별 AI 건강 리포트 무제한 생성</li>
                <li>✅ 이상 증상 즉시 알림</li>
                <li>✅ 7일 내 전액 환불 보장</li>
            </ul>
            <button class="btn" onclick="openPetlogCheckout()">
                💝 Pro 시작하기 — 월 9,900원
            </button>
        </div>

        <div class="secure">🔒 Paddle 안전 결제 · 언제든 취소 가능 · 7일 환불 보장</div>
    </div>
    """
    paddle_components.html(html, height=820, scrolling=False)


def render_upgrade_page():
    user = st.session_state["user_info"]
    email = user["email"]
    plan = get_user_plan(email)
    sub = get_subscription(email)

    render_topbar(user)

    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button("← 뒤로", key="back_from_upg"):
            st.session_state.pop("show_upgrade", None)
            st.rerun()
    with c2:
        st.markdown(
            "<div style='font-size:1.5rem;font-weight:900;color:#6B4A4A;'>"
            "💳 구독 & 결제</div>",
            unsafe_allow_html=True,
        )

    # 결제 결과 알림
    result = st.session_state.pop("paddle_result", None)
    if result == "success":
        st.success("🎉 결제가 완료되었어요! Pro 플랜이 활성화되었습니다. 🐾")
    elif result == "pending":
        st.info("⏳ 결제 처리 중입니다. 잠시 후 '결제 확인' 버튼을 눌러주세요.")

    # 현재 상태 카드
    if plan == "admin":
        st.markdown("""
        <div class="petlog-card" style="background:linear-gradient(135deg,#FFF4E0,#FFE8D0);
                                        border-color:#F1C873;">
            <div style="font-weight:900;color:#8A6A20;font-size:1.1rem;">
                👑 ADMIN — 모든 기능 무제한
            </div>
            <div style="color:#8A6A20;font-size:0.88rem;margin-top:6px;">
                아래 결제 테스트는 실제 구독 흐름을 확인하기 위한 용도예요.
                결제해도 ADMIN 권한은 유지됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
        # ADMIN도 결제창을 테스트할 수 있도록 체크아웃 UI 노출
        render_pricing_checkout(user)
    elif plan == "pro":
        period_end = sub.get("current_period_end", "") or "-"
        cancel_at = sub.get("cancel_at_period_end", 0)
        status_emoji = "✨" if not cancel_at else "⏳"
        status_text = (
            "활성 구독 중이에요" if not cancel_at
            else "구독이 예정된 취소 상태입니다 (현재 기간까지 이용 가능)"
        )
        st.markdown(f"""
        <div class="petlog-card" style="background:linear-gradient(135deg,#FFF9F0,#FFECEC);
                                        border-color:#FFB5A7;">
            <div style="font-weight:900;color:#6B4A4A;font-size:1.15rem;margin-bottom:6px;">
                {status_emoji} PetLog Pro
            </div>
            <div style="color:#8B6F6F;line-height:1.8;">
                {status_text}<br>
                다음 갱신일: <b>{period_end[:10] if period_end else '-'}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not cancel_at:
            with st.expander("⚙️ 구독 관리"):
                st.markdown(
                    "구독을 취소하면 **현재 결제 기간이 끝날 때까지 Pro 기능을 계속 이용**할 수 있어요."
                )
                if st.button("😢 구독 취소하기", key="cancel_sub"):
                    ok = cancel_subscription(email)
                    if ok:
                        st.success("구독 취소 요청이 접수되었어요. 현재 기간 종료 후 무료 플랜으로 전환됩니다.")
                        st.rerun()
                    else:
                        st.error("구독 취소에 실패했어요. 잠시 후 다시 시도해주세요.")
        else:
            st.info("이미 취소 요청이 접수되어 있어요.")
    else:
        # 무료 플랜 — Pro 업그레이드 카드
        render_pricing_checkout(user)

    # 결제 확인 버튼 (resync)
    with st.expander("🔄 결제 후 플랜이 안 바뀌었나요?"):
        st.markdown(
            "결제가 완료되었는데 플랜이 여전히 무료로 표시된다면 아래 버튼을 눌러주세요. "
            "Paddle에 등록된 이메일(`"
            + email + "`)로 구독을 다시 조회합니다."
        )
        if st.button("🔄 결제 상태 새로 가져오기", key="resync"):
            if sync_plan_from_email(email):
                st.success("✅ 구독 정보가 업데이트되었어요!")
                st.rerun()
            else:
                st.warning("구독을 찾지 못했어요. Paddle 결제 이메일이 Google 로그인 이메일과 같은지 확인해주세요.")

    # 관리자 전용
    if is_admin(email):
        with st.expander("🛠 관리자 전용"):
            st.write("현재 subscription 레코드:")
            st.json(sub or {"note": "no record"})


# ══════════════════════════════════════
# 법적 문서
# ══════════════════════════════════════
LEGAL_UPDATED = "2026년 4월 15일"


def render_legal_terms():
    st.markdown("# 📜 이용약관")
    st.caption(f"최종 업데이트: {LEGAL_UPDATED}")
    st.divider()
    st.markdown(f"""
## 1. 서비스 소개 및 약관의 효력

**PetLog AI**(이하 "서비스")는 반려동물의 건강 상태를 기록하고 Claude AI로
사진을 분석하여 월별 리포트를 제공하는 SaaS입니다. 본 약관은 서비스 이용에
관한 회원과 운영자 간의 권리·의무 및 책임 사항을 규정합니다.

서비스에 접속하거나 이용함으로써 귀하는 본 약관에 동의한 것으로 간주됩니다.
만 14세 이상만 이용할 수 있습니다.

## 2. 회원가입 및 계정

- 계정은 Google OAuth로 생성됩니다. Google 계정당 하나의 PetLog 계정만
  허용됩니다.
- 회원 정보(이메일, 이름, 프로필 이미지)는 정확해야 하며, 계정 내 모든
  활동에 대한 책임은 회원에게 있습니다.
- 계정의 양도·대여·판매는 엄격히 금지됩니다.
- 계정 보안이 침해되었다고 판단되면 즉시 **admin@trytimeback.com**으로
  연락주세요.

## 3. AI 사진 분석의 성격과 책임 한계

PetLog는 Claude AI Vision을 이용해 반려동물 사진에서 관찰 가능한 외형적
특징을 분석합니다. **다음 사항을 반드시 이해하고 이용해 주세요.**

- AI 분석 결과는 **수의사의 진단을 대체하지 않습니다.**
- 사진만으로는 파악할 수 없는 질병이 있을 수 있으며, 결과가 부정확할
  수도 있습니다.
- 건강에 이상이 의심되거나 AI가 "경고" 레벨로 판단한 경우 **반드시
  동물병원 진료를 받아주세요.**
- 회원이 AI 분석 결과만 믿고 수의학적 진료를 지연하여 발생한 피해에
  대해 PetLog는 책임지지 않습니다.

## 4. 유료 서비스 (PetLog Pro)

- PetLog Pro는 월 9,900원(VAT 별도)의 정기 구독입니다.
- 결제는 **Paddle**을 통해 안전하게 처리되며, Paddle의 이용약관이 함께
  적용됩니다.
- 구독은 언제든지 취소할 수 있으며, 현재 결제 기간이 종료될 때까지
  Pro 기능을 계속 이용할 수 있습니다.
- 환불은 별도의 **환불 정책**에 따릅니다.
- 가격은 사전 공지 후 다음 결제 주기부터 변경될 수 있습니다.

## 5. 금지 행위

- 타인의 사진을 무단으로 업로드·분석하는 행위
- 반려동물이 아닌 사진(인물, 불법 촬영물 등)을 업로드하는 행위
- 서비스 또는 관련 API(Claude, Paddle)에 비정상적인 부하를 발생시키는 행위
- 계정 정보를 공유·판매하거나 크롤링·자동화 도구로 서비스를 오용하는 행위

## 6. 서비스 중단 및 해지

- 회원은 언제든지 **admin@trytimeback.com**으로 계정 삭제를 요청할 수
  있습니다.
- 본 약관을 위반하거나 서비스를 오용하는 경우, 운영자는 사전 통지 없이
  이용을 제한·해지할 수 있습니다.
- 해지 시 데이터는 개인정보처리방침에 따라 처리됩니다.

## 7. 면책 조항

서비스는 "있는 그대로(as-is)" 제공되며, 명시적·묵시적 보증 없이 제공됩니다.
서비스 중단, 데이터 손실, AI 분석 오류 등으로 인한 직·간접 손해에 대해
PetLog는 책임지지 않습니다.

## 8. 준거법 및 분쟁 해결

본 약관은 대한민국 법률을 준거법으로 합니다. 서비스 관련 분쟁은 민사
소송법상의 관할 법원에서 해결합니다.

## 9. 문의

본 약관에 대한 문의: **admin@trytimeback.com**
""")


def render_legal_privacy():
    st.markdown("# 🔒 개인정보처리방침")
    st.caption(f"최종 업데이트: {LEGAL_UPDATED}")
    st.divider()
    st.markdown("""
PetLog AI는 회원의 개인정보를 소중히 다루며 「개인정보 보호법」등 관련
법령을 준수합니다.

## 1. 수집하는 개인정보 항목

**A. Google 계정 정보 (로그인 시)**
- 이메일 주소, 이름, 프로필 이미지 URL

**B. 반려동물 정보 (회원이 직접 입력)**
- 이름, 종류, 품종, 나이, 몸무게, 이모지

**C. 건강 기록 (회원이 직접 입력)**
- 식욕·활동량·배변 상태, 체중, 메모

**D. 업로드한 사진 및 AI 분석 결과**
- 회원이 업로드한 반려동물 사진(서버 파일 저장)
- Claude AI가 생성한 분석 텍스트·점수

**E. 결제 정보 (Pro 구독 시)**
- Paddle 고객 ID, 구독 ID, 거래 ID, 구독 상태, 결제 주기 정보
- ※ **카드번호·CVC 등 민감 결제정보는 Paddle에만 저장**되며 PetLog는
  절대 수집·보관하지 않습니다.

## 2. 이용 목적

- 서비스 제공 (건강 기록·AI 사진 분석·월별 리포트 생성)
- 회원 관리 및 본인 확인
- 결제 처리 및 구독 관리
- 플랜별 사용량 제한 적용
- 서비스 품질 개선 및 통계 분석
- 고객 문의 대응 및 법령상 의무 이행

## 3. 제3자 제공 및 처리 위탁

- **Google (OAuth)**: 로그인 인증. [Google 개인정보처리방침](https://policies.google.com/privacy)
- **Anthropic (Claude API)**: 업로드한 사진을 AI 분석에 활용.
  [Anthropic 개인정보처리방침](https://www.anthropic.com/privacy)
- **Paddle**: 결제 처리·구독 관리.
  [Paddle 개인정보처리방침](https://www.paddle.com/legal/privacy)
- **Railway**: 서비스 호스팅. 전송 구간 및 저장 데이터는 암호화 처리.

## 4. 보유 및 파기

- 회원이 탈퇴를 요청하면 개인정보는 지체 없이 파기되며, 저장된 사진 파일도
  30일 이내에 완전 삭제됩니다.
- 관계 법령에 따라 보관이 필요한 경우 해당 기간 동안에만 보관한 후 파기합니다.
  (전자상거래법: 거래 기록 5년 등)
- 파기 요청: **admin@trytimeback.com**

## 5. 회원의 권리

회원은 언제든지 본인의 개인정보를 열람·수정·삭제·처리정지 요청할 수 있습니다.
앱 내 "내 정보" 또는 이메일 문의로 행사 가능합니다.

## 6. 쿠키 및 세션

PetLog는 로그인 상태 유지를 위해 최소한의 세션 쿠키를 사용합니다. 광고 추적
쿠키는 사용하지 않습니다.

## 7. 개인정보 보호책임자

- 담당자: PetLog 운영팀
- 이메일: **admin@trytimeback.com**

개인정보 침해 관련 신고·상담은 KISA 개인정보침해신고센터(privacy.kisa.or.kr,
국번 없이 118)에서도 도움을 받을 수 있습니다.
""")


def render_legal_refund():
    st.markdown("# 💰 환불 정책")
    st.caption(f"최종 업데이트: {LEGAL_UPDATED}")
    st.divider()
    st.markdown("""
PetLog Pro 구독의 환불은 전자상거래법과 본 정책에 따라 처리됩니다.

## 1. 7일 이내 환불 (청약 철회)

- Pro 구독 **결제 후 7일 이내**이며 **AI 사진 분석을 한 번도 이용하지 않은
  경우** 전액 환불이 가능합니다.
- 이는 전자상거래법 제17조(청약 철회 등)에 따른 권리입니다.
- 환불 요청: **admin@trytimeback.com**으로 결제 이메일·거래 ID를 보내주세요.

## 2. 부분 이용 후 환불

AI 사진 분석을 1회 이상 사용한 경우 **서비스 성격상 청약 철회가 제한**될
수 있습니다. (전자상거래법 제17조 제2항) 다만, 아래 경우에는 검토 후
부분 환불을 진행합니다.

- 서비스 장애·오류로 정상적인 이용이 불가능했던 경우
- 회원이 결제 후 7일 이내이며 1~3회만 이용한 경우 (할인 후 일할 계산 가능)

## 3. 결제 실수에 의한 환불

- 중복 결제, 금액 오류, 의도하지 않은 결제 등 명백한 결제 실수는 **즉시
  전액 환불**해 드립니다.
- 결제 이메일을 포함해 **admin@trytimeback.com**으로 연락 바랍니다.

## 4. 환불 불가 사유

- 결제 후 7일이 경과하고 AI 사진 분석을 사용한 경우
- 회원의 이용약관 위반으로 계정이 정지된 경우
- 무료 플랜 사용 중 발생한 서비스 불만족

## 5. 환불 절차 및 소요 시간

1. **admin@trytimeback.com**에 환불 요청 메일 발송
2. 담당자가 **영업일 기준 3일 이내** 확인 후 회신
3. 승인된 환불은 **Paddle을 통해 원결제수단으로 환급**
4. 실제 환급 반영까지 카드사·은행에 따라 **3~10영업일**이 소요될 수 있습니다.

## 6. 구독 취소 vs 환불

- **구독 취소**: 다음 결제 주기부터 청구가 중단됩니다. 현재 결제 기간
  종료일까지는 Pro 기능을 계속 이용할 수 있으며, 사용한 기간에 대한 환불은
  없습니다.
- **환불**: 이미 결제된 금액을 돌려받는 절차로, 위 1~3항에 해당하는
  경우에만 가능합니다.

앱 내에서 언제든지 **구독 & 결제 → 구독 관리 → 구독 취소하기**로 취소할
수 있습니다.

## 7. 문의

환불·결제 관련 문의: **admin@trytimeback.com**
""")


def render_legal_page(doc: str):
    c1, _ = st.columns([1, 5])
    with c1:
        if st.button("← 뒤로", key=f"back_legal_{doc}"):
            st.query_params.clear()
            st.rerun()

    if doc == "terms":
        render_legal_terms()
    elif doc == "privacy":
        render_legal_privacy()
    elif doc == "refund":
        render_legal_refund()
    else:
        st.error("잘못된 페이지입니다.")


# ══════════════════════════════════════
# Router
# ══════════════════════════════════════
_legal_doc = st.query_params.get("page", "")
if _legal_doc in ("terms", "privacy", "refund"):
    render_legal_page(_legal_doc)
elif st.session_state.get("logged_in"):
    if st.session_state.get("show_upgrade"):
        render_upgrade_page()
    elif st.session_state.get("selected_pet_id"):
        render_health_page()
    else:
        render_dashboard()
else:
    render_login()

# Footer
st.markdown(f"""
<div class="petlog-footer">
    <div style="margin-bottom:10px;">
        <a href="?page=terms" target="_self"
           style="color:#9B7A7A;text-decoration:none;margin:0 8px;font-weight:600;">
           📜 이용약관</a>
        ·
        <a href="?page=privacy" target="_self"
           style="color:#9B7A7A;text-decoration:none;margin:0 8px;font-weight:600;">
           🔒 개인정보처리방침</a>
        ·
        <a href="?page=refund" target="_self"
           style="color:#9B7A7A;text-decoration:none;margin:0 8px;font-weight:600;">
           💰 환불정책</a>
    </div>
    <div style="margin-bottom:8px;color:#6B4A4A;font-weight:600;">
        📮 문의사항 ·
        <a href="mailto:admin@trytimeback.com"
           style="color:#FF8FA3;text-decoration:none;font-weight:700;">
           admin@trytimeback.com</a>
    </div>
    🐾 PetLog AI · {APP_DOMAIN}<br>
    <span style="font-size:0.75rem; color:#C8A8A8;">v{APP_VERSION}</span>
</div>
""", unsafe_allow_html=True)
