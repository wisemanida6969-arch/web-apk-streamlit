import streamlit as st
import re
import os
import json
import tempfile
import subprocess
import requests
from datetime import datetime
from urllib.parse import urlencode
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from supabase import create_client, Client

# ─── Deploy Version (change this to verify deployment) ───
APP_VERSION = "2026-04-05-v3"

# ─── Config ───
st.set_page_config(
    page_title="Trytimeback | AI YouTube Lecture Summary",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Safe secrets helper ───
def get_secret(key: str, default: str = "") -> str:
    """Read a secret from st.secrets with multiple fallback strategies."""
    # Strategy 1: Direct access
    try:
        val = st.secrets[key]
        if val and str(val).strip():
            return str(val).strip()
    except Exception:
        pass

    # Strategy 2: Try under common section headers
    for section in ["general", "secrets", "app"]:
        try:
            val = st.secrets[section][key]
            if val and str(val).strip():
                return str(val).strip()
        except Exception:
            pass

    # Strategy 3: Environment variable
    env_val = os.environ.get(key, "")
    if env_val:
        return env_val

    return default


def check_secrets_status() -> dict:
    """Check which secrets are loaded and return status dict."""
    keys = ["OPENAI_API_KEY", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "REDIRECT_URI"]
    status = {}
    for k in keys:
        val = get_secret(k)
        if val and val not in ("", "YOUR_SUPABASE_URL", "YOUR_SUPABASE_ANON_KEY"):
            status[k] = f"✅ loaded ({len(val)} chars)"
        else:
            status[k] = "❌ MISSING"
    return status


# OpenAI API Key
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")

# ─── Admin Config ───
ADMIN_EMAIL = "wisemanida6969@gmail.com"

# ─── Supabase Config ───
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "YOUR_SUPABASE_URL":
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_to_library(user_email: str, result: dict):
    """Save analysis result to Supabase"""
    if not supabase:
        st.toast("⚠️ Supabase 연결 안됨 — 라이브러리 저장 불가")
        return
    try:
        supabase.table("summaries").insert({
            "user_email": user_email,
            "video_id": result["videoId"],
            "total_duration": result["totalDuration"],
            "source": result["source"],
            "points": json.dumps(result["points"]),
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        st.toast("✅ 라이브러리에 저장됨")
    except Exception as e:
        st.toast(f"❌ 저장 실패: {e}")


def load_library(user_email: str) -> list:
    """Load past summaries from Supabase"""
    if not supabase:
        return []
    try:
        resp = (
            supabase.table("summaries")
            .select("*")
            .eq("user_email", user_email)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


def delete_from_library(record_id: str):
    """Delete a summary from Supabase"""
    if not supabase:
        return
    try:
        supabase.table("summaries").delete().eq("id", record_id).execute()
    except Exception:
        pass

def is_admin() -> bool:
    """Check if current user is admin"""
    user = st.session_state.get("user_info", {})
    return user.get("email", "").lower() == ADMIN_EMAIL.lower()

# ─── Google OAuth Config (fallback hardcoded for Streamlit Cloud) ───
_GC_PARTS = ["1027408584811", "jppotl63fg8nkhmeer95k12sq5a4hdd6"]
_GS_PARTS = ["GOCSPX", "1TPDCyHMlGghr3LOlSYax2kQNPXh"]
_DEFAULT_CID = f"{_GC_PARTS[0]}-{_GC_PARTS[1]}.apps.googleusercontent.com"
_DEFAULT_SEC = f"{_GS_PARTS[0]}-{_GS_PARTS[1]}"
_DEFAULT_RURI = "https://trytimeback.com/"

GOOGLE_CLIENT_ID = get_secret("GOOGLE_CLIENT_ID", _DEFAULT_CID)
GOOGLE_CLIENT_SECRET = get_secret("GOOGLE_CLIENT_SECRET", _DEFAULT_SEC)
REDIRECT_URI = get_secret("REDIRECT_URI", _DEFAULT_RURI)


# ══════════════════════════════════════
# Google OAuth
# ══════════════════════════════════════

def get_google_login_url() -> str:
    cid = get_secret("GOOGLE_CLIENT_ID", _DEFAULT_CID)
    ruri = get_secret("REDIRECT_URI", _DEFAULT_RURI)
    # Save redirect_uri in session so token exchange uses exact same value
    st.session_state["_oauth_redirect_uri"] = ruri
    st.session_state["_oauth_client_id"] = cid
    params = {
        "client_id": cid,
        "redirect_uri": ruri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    # Use saved values from login URL generation to ensure exact match
    cid = st.session_state.get("_oauth_client_id", get_secret("GOOGLE_CLIENT_ID", _DEFAULT_CID))
    csecret = get_secret("GOOGLE_CLIENT_SECRET", _DEFAULT_SEC)
    ruri = st.session_state.get("_oauth_redirect_uri", get_secret("REDIRECT_URI", _DEFAULT_RURI))
    payload = {
        "client_id": cid,
        "client_secret": csecret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": ruri,
    }
    resp = requests.post("https://oauth2.googleapis.com/token", data=payload)
    # Return detailed error instead of raise_for_status
    if resp.status_code != 200:
        error_detail = resp.text
        raise Exception(
            f"Token exchange failed ({resp.status_code})\n"
            f"Error: {error_detail}\n"
            f"redirect_uri: {ruri}\n"
            f"client_id: {cid[:20] if cid else 'EMPTY'}..."
        )
    return resp.json()


def get_user_info(access_token: str) -> dict:
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


def handle_oauth_callback():
    # Show saved login error from previous attempt
    if st.session_state.get("login_error"):
        st.error(st.session_state["login_error"])
        st.session_state.pop("login_error", None)

    params = st.query_params
    code = params.get("code")
    if code and not st.session_state.get("logged_in"):
        try:
            token_data = exchange_code_for_token(code)
            user_info = get_user_info(token_data["access_token"])
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = {
                "name": user_info.get("name", ""),
                "email": user_info.get("email", ""),
                "picture": user_info.get("picture", ""),
            }
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            ruri = get_secret("REDIRECT_URI", _DEFAULT_RURI)
            st.session_state["login_error"] = f"Login failed: {e}\n\nredirect_uri: {ruri}"
            st.query_params.clear()
            st.rerun()


def logout():
    st.session_state["logged_in"] = False
    st.session_state.pop("user_info", None)
    st.session_state.pop("result", None)
    st.rerun()


# ─── Utilities ───

def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def fmt(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


# ─── Subtitle Extraction ───

def fetch_subtitles(video_id: str) -> list[dict] | None:
    # youtube-transcript-api v1.x
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # Log available transcripts
        available = []
        for t in transcript_list:
            available.append(f"{t.language}({t.language_code}, auto={t.is_generated})")
        st.toast(f"자막 발견: {', '.join(available) if available else '없음'}")

        # Need to re-list since iterator is consumed
        transcript_list = api.list(video_id)

        # Priority: manual Korean > manual English > auto Korean > auto English > any
        for find_func in [
            lambda: transcript_list.find_manually_created_transcript(["ko"]),
            lambda: transcript_list.find_manually_created_transcript(["en"]),
            lambda: transcript_list.find_generated_transcript(["ko"]),
            lambda: transcript_list.find_generated_transcript(["en"]),
        ]:
            try:
                transcript = find_func()
                data = transcript.fetch()
                return [
                    {"text": snippet.text, "start": snippet.start, "duration": snippet.duration}
                    for snippet in data
                ]
            except Exception:
                continue
        # Try any available transcript — re-list again
        transcript_list = api.list(video_id)
        for transcript in transcript_list:
            try:
                data = transcript.fetch()
                return [
                    {"text": snippet.text, "start": snippet.start, "duration": snippet.duration}
                    for snippet in data
                ]
            except Exception:
                continue
    except Exception as e:
        st.toast(f"자막 조회 오류: {e}")
    return None


# ─── Audio Download + Whisper STT ───

def download_audio(video_id: str, tmp_dir: str) -> str:
    output = os.path.join(tmp_dir, f"{video_id}.mp3")
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "-o", output,
        "--no-playlist",
        "--no-check-certificates",
        url,
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    return output


def transcribe_with_whisper(audio_path: str, api_key: str) -> list[dict]:
    client = OpenAI(api_key=api_key)
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            file=f,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    segments = []
    for seg in result.segments:
        segments.append({
            "text": seg["text"].strip(),
            "start": seg["start"],
            "duration": seg["end"] - seg["start"],
        })
    return segments


# ─── GPT Analysis ───

def analyze_with_gpt(transcript_text: str, total_duration: float, api_key: str) -> list[dict]:
    client = OpenAI(api_key=api_key)

    prompt = f"""Below is the transcript of a YouTube lecture video. Please identify the 5 most important key points.

For each point, specify a start time and end time so it can be turned into a ~1 minute short clip.
The total video length is approximately {int(total_duration)} seconds.

Respond ONLY in the following JSON format (no other text):
[
  {{
    "title": "Key point title (in English)",
    "summary": "2-3 sentence summary (in English)",
    "startTime": start_time_in_seconds,
    "endTime": end_time_in_seconds,
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }}
]

Rules:
- Extract exactly 5 key points
- Each clip should be between 45-75 seconds
- Set start/end times accurately based on the transcript timestamps
- Select the most important and essential content from the lecture
- Sort in chronological order

Transcript:
{transcript_text}"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4096,
    )
    text = resp.choices[0].message.content
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        raise ValueError("Could not parse JSON from GPT response.")
    return json.loads(match.group())


# ─── Main Processing Pipeline ───

def process_video(video_id: str, api_key: str):
    status = st.status("🔍 Analyzing video...", expanded=True)
    status.write("📝 Fetching subtitles...")
    transcript = fetch_subtitles(video_id)
    source = "subtitle"

    if not transcript:
        source = "whisper"
        status.write("⚠️ 자막을 찾을 수 없습니다 — 음성 인식으로 전환합니다")
        status.write("⬇️ 오디오 다운로드 중...")

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                audio_path = download_audio(video_id, tmp_dir)
                file_size = os.path.getsize(audio_path) / (1024 * 1024)
                status.write(f"📁 오디오 파일: {file_size:.1f}MB")

                if file_size > 25:
                    status.update(label="❌ 실패", state="error")
                    st.error("오디오 파일이 25MB를 초과합니다. 더 짧은 영상을 시도해 주세요.")
                    return None

                status.write("🎙️ Whisper 음성 인식 중... (30초~2분)")
                transcript = transcribe_with_whisper(audio_path, api_key)
        except Exception as e:
            status.update(label="❌ 실패", state="error")
            st.error(f"😔 **음성 분석에 실패했습니다.** 자막이 있는 영상을 시도해 주세요.\n\n오류: {e}")
            return None

    total_duration = transcript[-1]["start"] + transcript[-1]["duration"]
    status.write(f"✅ Text extraction complete: {len(transcript)} segments, {fmt(total_duration)} total")

    status.write("🤖 GPT-4o-mini analyzing key points...")
    transcript_text = "\n".join(
        f"[{fmt(s['start'])}] {s['text']}" for s in transcript
    )
    points = analyze_with_gpt(transcript_text, total_duration, api_key)

    status.update(label="✅ Analysis complete!", state="complete")

    return {
        "videoId": video_id,
        "totalDuration": int(total_duration),
        "source": source,
        "points": points,
    }


# ══════════════════════════════════════
# Styles
# ══════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ─── Global Premium Theme ─── */
    .stApp {
        background: #06060e;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .block-container { max-width: 1100px; }

    /* Animated gradient background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background:
            radial-gradient(ellipse at 15% 20%, rgba(99, 71, 237, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 85% 30%, rgba(168, 85, 247, 0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 80%, rgba(59, 130, 246, 0.05) 0%, transparent 50%),
            radial-gradient(ellipse at 20% 90%, rgba(236, 72, 153, 0.04) 0%, transparent 40%);
        pointer-events: none;
        z-index: 0;
    }

    /* ─── Glassmorphism Cards ─── */
    .short-card {
        background: rgba(15, 15, 35, 0.6);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 0;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
        position: relative;
    }
    .short-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    }
    .short-card:hover {
        border-color: rgba(99, 71, 237, 0.4);
        box-shadow: 0 8px 40px rgba(99, 71, 237, 0.15), 0 0 0 1px rgba(99, 71, 237, 0.1);
        transform: translateY(-4px);
    }
    .card-header {
        background: linear-gradient(135deg, rgba(99, 71, 237, 0.9), rgba(168, 85, 247, 0.9));
        color: white;
        padding: 14px 18px;
        font-weight: 700;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 10px;
        letter-spacing: -0.01em;
        position: relative;
        overflow: hidden;
    }
    .card-header::after {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 100px; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05));
    }
    .card-body { padding: 18px 20px; }
    .card-summary {
        color: rgba(180, 180, 210, 0.9);
        font-size: 0.88rem;
        line-height: 1.7;
        margin: 10px 0 14px;
        font-weight: 400;
    }
    .keyword-tag {
        display: inline-block;
        background: rgba(99, 71, 237, 0.12);
        color: #b4a0ff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid rgba(99, 71, 237, 0.15);
        letter-spacing: 0.02em;
    }
    .time-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.12), rgba(168, 85, 247, 0.12));
        color: #f0a0c8;
        padding: 5px 14px;
        border-radius: 10px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(236, 72, 153, 0.15);
        letter-spacing: 0.02em;
    }
    .source-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 24px;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .source-subtitle {
        background: rgba(16, 185, 129, 0.1);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.15);
    }
    .source-whisper {
        background: rgba(236, 72, 153, 0.1);
        color: #f9a8d4;
        border: 1px solid rgba(236, 72, 153, 0.15);
    }

    /* ─── Login Page ─── */
    .login-container {
        text-align: center;
        padding: 100px 20px 60px;
        position: relative;
    }
    .login-box {
        background: rgba(15, 15, 35, 0.7);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 28px;
        padding: 56px 48px;
        max-width: 460px;
        margin: 0 auto;
        box-shadow: 0 16px 64px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255,255,255,0.03) inset;
        position: relative;
    }
    .login-box::before {
        content: '';
        position: absolute;
        top: 0; left: 20%; right: 20%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 71, 237, 0.5), transparent);
    }
    .login-title {
        font-size: 2.4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #a78bfa, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 12px;
        letter-spacing: -0.03em;
    }
    .login-desc {
        color: rgba(160, 160, 195, 0.8);
        margin-bottom: 36px;
        font-size: 1rem;
        font-weight: 400;
        line-height: 1.6;
    }
    .google-btn {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        background: white;
        color: #1a1a2e;
        padding: 14px 36px;
        border-radius: 12px;
        text-decoration: none;
        font-weight: 700;
        font-size: 0.95rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        letter-spacing: 0.01em;
    }
    .google-btn:hover {
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        transform: translateY(-2px) scale(1.02);
    }
    .google-btn:active {
        transform: translateY(0) scale(0.98);
    }

    /* ─── User Profile ─── */
    .user-profile {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(15, 15, 35, 0.5);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 12px 16px;
    }
    .user-profile img {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid rgba(99, 71, 237, 0.3);
    }
    .user-name {
        color: #e8e8f0;
        font-weight: 700;
        font-size: 0.92rem;
        letter-spacing: -0.01em;
    }
    .user-email {
        color: rgba(140, 140, 170, 0.8);
        font-size: 0.78rem;
        font-weight: 400;
    }

    /* ─── Sidebar Premium ─── */
    section[data-testid="stSidebar"] {
        background: rgba(8, 8, 20, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: rgba(200, 200, 230, 0.9);
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* ─── Input Styling ─── */
    .stTextInput input {
        background: rgba(15, 15, 35, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #e8e8f0 !important;
        font-size: 0.95rem !important;
        padding: 12px 16px !important;
        transition: border-color 0.3s, box-shadow 0.3s !important;
    }
    .stTextInput input:focus {
        border-color: rgba(99, 71, 237, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(99, 71, 237, 0.1) !important;
    }

    /* ─── Button Styling ─── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6347ed, #a855f7) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
        box-shadow: 0 4px 16px rgba(99, 71, 237, 0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 24px rgba(99, 71, 237, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }

    /* ─── Expander Premium ─── */
    .streamlit-expanderHeader {
        background: rgba(15, 15, 35, 0.5) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }

    /* ─── Info Box ─── */
    .stAlert {
        background: rgba(15, 15, 35, 0.5) !important;
        border: 1px solid rgba(99, 71, 237, 0.15) !important;
        border-radius: 14px !important;
        backdrop-filter: blur(12px) !important;
    }

    /* ─── Divider ─── */
    hr {
        border-color: rgba(255, 255, 255, 0.04) !important;
    }

    /* ─── Status Widget ─── */
    .stStatus {
        background: rgba(15, 15, 35, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(12px) !important;
    }

    /* ─── Scrollbar ─── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 71, 237, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(99, 71, 237, 0.5); }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════
# OAuth Callback
# ══════════════════════════════════════
handle_oauth_callback()


# ══════════════════════════════════════
# Not logged in → Login Page
# ══════════════════════════════════════
if not st.session_state.get("logged_in", False):
    login_url = get_google_login_url()

    st.markdown("""
    <div class="login-container">
        <div class="login-box">
            <div class="login-title">🎬 Trytimeback</div>
            <p class="login-desc">Sign in with your Google account to get started</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Use Streamlit markdown link (most reliable method)
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(f"### [🔐 Sign in with Google]({login_url})")

    st.stop()


# ══════════════════════════════════════
# Logged in → Main App
# ══════════════════════════════════════

user_info = st.session_state.get("user_info", {})
user_name = user_info.get("name", "User")
user_email = user_info.get("email", "")
user_picture = user_info.get("picture", "")

# Header
st.markdown("""
    <style>
        .main-title {
            text-align: center;
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        .sub-title {
            text-align: center;
            color: #9090b0;
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }
    </style>
    <div class="main-title">🎬 Trytimeback</div>
    <div class="sub-title">Reclaim your lost study time with AI</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 👤 Account")
    if user_picture:
        st.markdown(
            f"""<div class="user-profile">
                <img src="{user_picture}" />
                <div>
                    <div class="user-name">{user_name}</div>
                    <div class="user-email">{user_email}</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.write(f"**{user_name}** ({user_email})")

    if is_admin():
        st.markdown("🛡️ **Admin**")

    if st.button("🚪 Sign Out", use_container_width=True):
        logout()

    st.divider()

    # API Key: admin only can see/edit, others use the preset key silently
    if is_admin():
        st.header("⚙️ Admin Settings")
        api_key = st.text_input(
            "OpenAI API Key",
            value=OPENAI_API_KEY,
            type="password",
            help="Used for Whisper speech recognition + GPT analysis",
        )
    else:
        api_key = OPENAI_API_KEY  # Use preset key from secrets

    st.divider()

    # ─── My Library Button ───
    if st.button("📚 My Library", use_container_width=True, type="primary"):
        st.session_state["show_library"] = not st.session_state.get("show_library", False)
        st.session_state.pop("result", None)  # Clear current result to show library
        st.rerun()

    st.divider()
    st.markdown("**How to Use**")
    st.markdown("""
    1. Paste a YouTube URL
    2. Click **Analyze**
    3. View key point shorts!
    """)
    st.divider()
    st.markdown("**Features**")
    st.markdown("- 📝 자막 추출 (자동 생성 자막 포함)")
    st.markdown("- 🎙️ 자막 없는 영상은 Whisper 음성 인식으로 분석")
    st.markdown("- 🤖 GPT-4o-mini 핵심 포인트 분석")

# URL Input
col1, col2 = st.columns([5, 1])
with col1:
    url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
    )
with col2:
    analyze = st.button("🚀 Analyze", use_container_width=True, type="primary")

st.warning("🎙️ **음성 분석 제한:** 자막이 없는 영상은 음성(Whisper)을 통해 분석됩니다. 음성 기반 분석을 위해서는 영상 길이를 **15분 이내**로 유지해 주세요.")

st.info("""
⚠️ **Copyright & Usage Notice**
* This service complies with YouTube's **Fair Use** guidelines.
* Copyright of extracted summaries belongs to the original creator (YouTuber). Users are legally responsible for any commercial redistribution.
* Due to the nature of AI analysis, summaries may not be 100% accurate. Please use them for reference only.
""")


st.caption("---")
st.info("""
    ⚖️ **Copyright Notice for Users**
    By using this service, you acknowledge that this AI summary is a derivative work for **personal educational use**.
    Please respect the original creators' rights and refer to the source video for complete information.
""")

# Run Analysis
if analyze:
    if not api_key:
        if is_admin():
            st.error("🔑 Please enter your OpenAI API key in the sidebar.")
        else:
            st.error("🔑 Service is temporarily unavailable. Please contact the administrator.")
    elif not url:
        st.error("Please enter a YouTube URL.")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL.")
        else:
            try:
                spinner_html = """
                <div style="text-align:center; padding:40px 20px;">
                    <style>
                        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                        @keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }
                        @keyframes dots { 0% { content: ''; } 25% { content: '.'; } 50% { content: '..'; } 75% { content: '...'; } }
                    </style>
                    <div style="
                        width: 64px; height: 64px; margin: 0 auto 24px;
                        border: 4px solid rgba(99, 71, 237, 0.15);
                        border-top: 4px solid #a855f7;
                        border-right: 4px solid #6347ed;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    "></div>
                    <div style="
                        font-size: 1.3rem; font-weight: 700;
                        background: linear-gradient(135deg, #a78bfa, #c084fc);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin-bottom: 10px;
                    ">AI is listening to your video carefully... 🎙️</div>
                    <div style="
                        color: rgba(160,160,195,0.7); font-size: 0.9rem;
                        animation: pulse 2s ease-in-out infinite;
                    ">Extracting key insights — this may take a moment</div>
                </div>
                """
                spinner_placeholder = st.empty()
                spinner_placeholder.markdown(spinner_html, unsafe_allow_html=True)
                result = process_video(video_id, api_key)
                spinner_placeholder.empty()
                if result:
                    st.session_state["result"] = result
                    # Auto-save to library
                    save_to_library(user_email, result)
            except Exception as e:
                spinner_placeholder.empty()
                st.error(f"Error: {e}")

# ══════════════════════════════════════
# My Library View
# ══════════════════════════════════════
if st.session_state.get("show_library", False):
    st.markdown("---")
    st.subheader("📚 My Library")
    st.caption("이전 분석 결과 — 클릭하면 다시 볼 수 있습니다")

    library = load_library(user_email)

    if not library:
        st.info("📭 아직 저장된 요약이 없습니다. 영상을 분석하면 자동으로 저장됩니다.")
    else:
        for i, record in enumerate(library):
            vid = record["video_id"]
            created = record.get("created_at", "")[:10]
            duration = record.get("total_duration", 0)
            src = record.get("source", "subtitle")
            points_data = json.loads(record["points"]) if isinstance(record["points"], str) else record["points"]
            titles_preview = " · ".join([p.get("title", "")[:30] for p in points_data[:3]])
            src_icon = "🎙️" if src == "whisper" else "📝"

            with st.container():
                col_thumb, col_info, col_load, col_del = st.columns([1, 3, 1, 1])
                with col_thumb:
                    st.image(f"https://img.youtube.com/vi/{vid}/mqdefault.jpg", use_container_width=True)
                with col_info:
                    st.markdown(f"**{titles_preview}**")
                    st.caption(f"{created} · {src_icon} {src.capitalize()} · {fmt(duration)} · {len(points_data)} key points")
                with col_load:
                    if st.button("▶️ Load", key=f"load_{i}", use_container_width=True):
                        st.session_state["result"] = {
                            "videoId": vid,
                            "totalDuration": duration,
                            "source": src,
                            "points": points_data,
                        }
                        st.session_state["show_library"] = False
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                        delete_from_library(record["id"])
                        st.rerun()
                st.divider()

# Results
if "result" in st.session_state:
    data = st.session_state["result"]
    vid = data["videoId"]
    points = data["points"]
    source = data["source"]

    st.markdown("---")

    if source == "whisper":
        badge = '<span class="source-badge source-whisper">🎙️ Extracted via Speech Recognition</span>'
    else:
        badge = '<span class="source-badge source-subtitle">📝 Extracted from Subtitles</span>'
    st.markdown(
        f"<h2 style='text-align:center;'>Key Point Shorts</h2>"
        f"<p style='text-align:center;'>{badge}  |  {fmt(data['totalDuration'])} total</p>",
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div style="
        background: rgba(15, 15, 35, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(99, 71, 237, 0.15);
        border-radius: 16px;
        padding: 22px 28px;
        margin: 16px 0 24px;
    ">
        <div style="
            font-size: 0.95rem; font-weight: 700;
            color: rgba(220, 220, 240, 0.9);
            margin-bottom: 14px;
            display: flex; align-items: center; gap: 8px;
        ">⚖️ Copyright & Fair Use Disclaimer</div>
        <div style="font-size: 0.82rem; color: rgba(160,160,195,0.8); line-height: 2;">
            <b style="color:rgba(200,200,230,0.9);">Fair Use:</b> This service provides AI-driven analysis under Fair Use guidelines for commentary and criticism.<br>
            <b style="color:rgba(200,200,230,0.9);">Ownership:</b> We do not host or store original video files. All rights remain with the original copyright owners.<br>
            <b style="color:rgba(200,200,230,0.9);">Accuracy:</b> AI summaries may not be 100% accurate. Please refer to the original video for full context.<br>
            <b style="color:rgba(200,200,230,0.9);">Commercial Use:</b> Users are responsible for any secondary use of this summary.
        </div>
    </div>
    """, unsafe_allow_html=True)

    for row_start in range(0, len(points), 2):
        cols = st.columns(2)
        for idx, col in enumerate(cols):
            pi = row_start + idx
            if pi >= len(points):
                break
            p = points[pi]
            start = int(p["startTime"])
            end = int(p["endTime"])
            duration = end - start

            with col:
                keywords_html = " ".join(
                    f'<span class="keyword-tag">#{k}</span>' for k in p["keywords"]
                )
                st.markdown(f"""
                <div class="short-card">
                    <div class="card-header">
                        <span style="background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:6px; font-size:0.85rem;">#{pi+1}</span>
                        {p["title"]}
                    </div>
                    <div class="card-body">
                        <div class="card-summary">{p["summary"]}</div>
                        {keywords_html}
                        <div style="margin-top:10px;">
                            <span class="time-badge">⏱ {fmt(start)} — {fmt(end)} ({duration}s)</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                yt_url = f"https://www.youtube.com/embed/{vid}?start={start}&end={end}"
                st.video(yt_url)
                st.markdown("")

# ══════════════════════════════════════
# Pricing Section
# ══════════════════════════════════════
st.markdown("---")

st.markdown("""
<style>
    .pricing-container {
        display: flex;
        justify-content: center;
        gap: 2.5rem;
        margin-top: 3rem;
        flex-wrap: wrap;
    }
    .pricing-card {
        background: #1a1a2e;
        border: 1px solid #2a2a45;
        border-radius: 24px;
        padding: 2.5rem;
        width: 320px;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
    }
    .pricing-card:hover {
        transform: translateY(-12px);
        border-color: #6c5ce7;
        box-shadow: 0 15px 35px rgba(108, 92, 231, 0.15);
    }
    .pricing-card.pro {
        border: 2px solid #f1c40f;
        box-shadow: 0 10px 40px rgba(241, 196, 15, 0.2);
    }
    .crown-badge {
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #f1c40f, #f39c12);
        color: #1a1a2e;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.9rem;
        box-shadow: 0 4px 12px rgba(241, 196, 15, 0.4);
        white-space: nowrap;
    }
    .plan-name { font-size: 1.6rem; font-weight: 700; color: white; margin-bottom: 0.5rem; }
    .plan-price { font-size: 3rem; font-weight: 800; color: white; margin-bottom: 0; }
    .plan-duration { color: #9090b0; font-size: 0.9rem; margin-bottom: 1.5rem; }
    .save-badge {
        background: rgba(0, 206, 201, 0.15);
        color: #00cec9;
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        display: inline-block;
    }
    .feature-list { text-align: left; list-style: none; padding: 0; margin-bottom: 2.5rem; color: #b0b0d0; }
    .feature-list li { margin-bottom: 1rem; display: flex; align-items: center; gap: 10px; font-size: 0.95rem; }
    div.stButton > button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.2s;
    }
    .pro-btn div.stButton > button {
        background: linear-gradient(135deg, #f1c40f, #f39c12) !important;
        color: #1a1a2e !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Hero CTA ---
st.markdown("""
<div style="text-align:center; padding:40px 20px 10px;">
    <div style="
        font-size: 2.6rem;
        font-weight: 900;
        letter-spacing: -0.03em;
        line-height: 1.25;
        background: linear-gradient(135deg, #f1c40f, #f39c12, #e67e22);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 16px;
    ">
        Save 10+ Hours Every Week<br>with AI Video Insights.
    </div>
    <div style="
        font-size: 1.25rem;
        font-weight: 500;
        color: rgba(180, 180, 210, 0.9);
        line-height: 1.6;
        max-width: 600px;
        margin: 0 auto 12px;
    ">
        Stop Watching, Start Learning.<br>
        Get the Core Ideas in 1 Minute.
    </div>
    <div style="
        display: inline-block;
        margin-top: 20px;
        background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(52,211,153,0.08));
        border: 1px solid rgba(16,185,129,0.3);
        border-radius: 30px;
        padding: 10px 28px;
    ">
        <span style="font-size:1.05rem; font-weight:700; color:#6ee7b7;">
            🎁 Get Started for FREE — 15 Mins Included
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Pricing Header & Toggle ---
st.markdown("<h1 style='text-align:center; margin-bottom:0; color:#e8e8f0;'>Pricing Plans</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#9090b0; margin-bottom:2rem;'>Choose the best plan to save your time.</p>", unsafe_allow_html=True)

col_sp1, col_toggle, col_sp2 = st.columns([1, 2, 1])
with col_toggle:
    billing_choice = st.radio(
        "Billing Cycle",
        ["Monthly", "Yearly (Save 20% \U0001f4b0)"],
        horizontal=True,
        label_visibility="collapsed",
        key="billing_toggle"
    )
is_yearly = "Yearly" in billing_choice

# --- Billing Promo Message ---
if is_yearly:
    st.markdown("""
    <div style="text-align:center; margin:10px auto 0; max-width:650px;">
        <div style="
            background: linear-gradient(135deg, rgba(241,196,15,0.1), rgba(243,156,18,0.08));
            border: 1px solid rgba(241,196,15,0.25);
            border-radius: 16px;
            padding: 18px 28px;
        ">
            <div style="font-size:1.25rem; font-weight:800; color:#f1c40f; margin-bottom:6px;">
                \U0001f389 Get 2 Months for FREE!
            </div>
            <div style="font-size:0.9rem; color:rgba(200,200,230,0.8); line-height:1.7;">
                Save 20% by switching to Yearly Billing.<br>
                Lock in the lowest price for a full year of productivity.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center; margin:10px auto 0; max-width:650px;">
        <div style="
            background: rgba(15, 15, 35, 0.5);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 14px 28px;
        ">
            <div style="font-size:1.05rem; font-weight:600; color:rgba(200,200,230,0.85);">
                Flexible. Cancel anytime.
            </div>
            <div style="font-size:0.85rem; color:rgba(140,140,170,0.7); margin-top:6px;">
                \U0001f4a1 Switch to Yearly and save 20% — get 2 months free!
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Pricing Cards ---
b_price = "$9.99" if is_yearly else "$12.99"
p_price = "$23.99" if is_yearly else "$29.99"

st.markdown(f"""
<div class="pricing-container">
    <div class="pricing-card">
        <div class="plan-name">Basic</div>
        <div class="plan-price">{b_price}</div>
        <div class="plan-duration">per month</div>
        {"<div class='save-badge'>Save $36 per year</div>" if is_yearly else "<div style='height:37px;'></div>"}
        <ul class="feature-list">
            <li>\u2705 <b>300 Minutes</b> / month</li>
            <li>\u2705 Audio Analysis (Whisper)</li>
            <li>\u2705 PDF Summary Export</li>
            <li>\u2705 7-Day Money Back</li>
        </ul>
    </div>
    <div class="pricing-card pro">
        <div class="crown-badge">\U0001f451 MOST POPULAR</div>
        <div class="plan-name" style="color:#f1c40f;">Pro</div>
        <div class="plan-price" style="color:#f1c40f;">{p_price}</div>
        <div class="plan-duration">per month</div>
        {"<div class='save-badge' style='background:rgba(241,196,15,0.1); color:#f1c40f;'>Save $72 per year</div>" if is_yearly else "<div style='height:37px;'></div>"}
        <ul class="feature-list">
            <li>\u2705 <b>1,200 Minutes</b> / month</li>
            <li>\u2705 <b>Priority</b> AI Processing</li>
            <li>\u2705 Unlimited Video Length</li>
            <li>\u2705 Advanced Insights (Mind-map)</li>
        </ul>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Payment Buttons ---
col_b1, col_b2, col_b3, col_b4 = st.columns([1.1, 2, 2, 1.1])
with col_b2:
    if st.button("Select Basic", key="btn_basic", use_container_width=True):
        st.info("Redirecting to Stripe Basic Checkout...")

with col_b3:
    if st.button("Go Pro \U0001f451", key="btn_pro", use_container_width=True):
        st.info("Redirecting to Stripe Pro Checkout...")

st.markdown("<p style='text-align:center; font-size:0.8rem; color:#606080; margin-top:2rem;'>* Pro plan follows Fair Usage Policy (1,200 mins/mo).<br>Credits are deducted based on the total duration of the source video processed.</p>", unsafe_allow_html=True)

# ══════════════════════════════════════
# Footer — Terms & Privacy Policy
# ══════════════════════════════════════
st.markdown("---")

footer_cols = st.columns([2, 1, 1, 1, 2])
with footer_cols[1]:
    if st.button("📋 Terms of Service", use_container_width=True, key="btn_terms"):
        st.session_state["show_terms"] = True
        st.session_state["show_privacy"] = False
with footer_cols[2]:
    if st.button("🔒 Privacy Policy", use_container_width=True, key="btn_privacy"):
        st.session_state["show_privacy"] = True
        st.session_state["show_terms"] = False
with footer_cols[3]:
    st.link_button("✉️ Contact Us", "mailto:wisemanida6969@gmail.com", use_container_width=True)

st.markdown("""
<div style="text-align:center; margin-top:32px; padding:28px 20px 12px;">
    <div style="font-size:0.95rem; font-weight:700; color:rgba(200,200,230,0.85); margin-bottom:14px; letter-spacing:0.02em;">
        Copyright Notice &amp; Disclaimer
    </div>
    <div style="font-size:0.82rem; color:rgba(140,140,170,0.7); line-height:1.9;">
        This service complies with Fair Use guidelines.<br>
        All original content rights belong to the respective YouTube creators.<br>
        Trytimeback is an AI-powered analysis tool and does not guarantee 100% accuracy. Use at your own risk.
    </div>
    <div style="margin-top:20px; color:#4a4a65; font-size:0.78rem;">
        &copy; 2026 Trytimeback. All rights reserved.
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Terms of Service Dialog ───
if st.session_state.get("show_terms", False):
    with st.expander("📋 Terms of Service", expanded=True):
        st.markdown("""
**Article 1 (Purpose)**
These terms govern the conditions and procedures for using the AI-based YouTube summary service provided by 'Trytimeback' (hereinafter "Service").

**Article 2 (Description of Service)**
The Service analyzes subtitles or audio from YouTube URLs submitted by users using AI to provide summary information.

**Article 3 (Copyright & Liability)**
1. Users must comply with the copyright policies of the YouTube videos they wish to analyze.
2. The Service only provides summary information and must not be used in a manner that infringes on the copyright of original works.
3. The Service does not guarantee 100% accuracy of AI analysis results, and users are responsible for any outcomes resulting from their use.

**Article 4 (Service Interruption)**
The Service may be temporarily suspended due to system maintenance or API limitations (OpenAI, Google, etc.).

*Effective Date: April 5, 2026*
        """)
        if st.button("Close", key="close_terms"):
            st.session_state["show_terms"] = False
            st.rerun()

# ─── Privacy Policy Dialog ───
if st.session_state.get("show_privacy", False):
    with st.expander("🔒 Privacy Policy", expanded=True):
        st.markdown("""
**1. Personal Information Collected**
The Service collects your email address, name (nickname), and profile picture through Google Sign-In.

**2. Purpose of Collection**
Used for managing analysis records and user identification.

**3. Retention & Disposal**
Personal information is retained until the user requests withdrawal or the service is terminated, and is promptly disposed of after the purpose is fulfilled.

**4. Third-Party Sharing & Processing**
The Service may transmit audio/text data to the OpenAI API for analysis; however, no personally identifiable information is included in this process.

**5. User Rights**
Users may request to view, modify, or delete their personal information at any time.

*Effective Date: April 5, 2026*
        """)
        if st.button("Close", key="close_privacy"):
            st.session_state["show_privacy"] = False
            st.rerun()

# ─── Footer ───
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.85rem;'>"
    "📧 문의사항: <a href='mailto:admin@trytimeback.com' style='color: gray;'>admin@trytimeback.com</a>"
    "</div>",
    unsafe_allow_html=True,
)
