import streamlit as st
import re
import os
import json
import tempfile
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

# ─── 1단계: 사장님의 기존 설정 및 세션 체크 ───
st.set_page_config(page_title="Trytimeback: AI 숏츠 요약", page_icon="🎬", layout="wide")

# API 키 및 DB 설정 (Streamlit Secrets 활용)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# ─── 2단계: 핵심 유틸 함수 (클로드 엔진) ───
def extract_video_id(url: str) -> str | None:
    patterns = [r"(?:v=)([a-zA-Z0-9_-]{11})", r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})", r"shorts/([a-zA-Z0-9_-]{11})"]
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return None

def fmt(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"

# ─── 3단계: 자막 및 오디오 분석 (강력한 기능) ───
def fetch_subtitles(video_id: str):
    for lang in (["ko"], ["en"], None):
        try:
            data = YouTubeTranscriptApi.get_transcript(video_id, languages=lang)
            return data
        except: continue
    return None

def download_audio(video_id: str, tmp_dir: str):
    output = os.path.join(tmp_dir, f"{video_id}.mp3")
    url = f"https://www.youtube.com/watch?v={video_id}"
    # 스트림릿 서버용 yt-dlp 명령어
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5", "-o", output, url]
    subprocess.run(cmd, check=True, capture_output=True)
    return output

# ─── 4단계: UI 구성 (사장님 스타일로 개조) ───
st.markdown("<h1 style='text-align:center;'>🎬 Trytimeback: 최강 요약기</h1>", unsafe_allow_html=True)

# 로그인 체크 (기존 수파베이스 로직이 여기에 들어갑니다)
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("로그인이 필요합니다. (사장님, 아까 그 파란 버튼으로 로그인 먼저 하세요! ㅋ)")
    # 여기에 기존 로그인 버튼 로직 추가...
else:
    url_input = st.text_input("분석할 유튜브 주소를 입력하세요:")
    if st.button("🚀 AI 딥러닝 분석 시작"):
        video_id = extract_video_id(url_input)
        if video_id:
            with st.status("🔍 AI가 영상을 뜯어보는 중...", expanded=True) as status:
                status.write("📝 자막 확인 중...")
                transcript = fetch_subtitles(video_id)
                
                if not transcript:
                    status.write("🎙️ 자막 없음 → Whisper 음성 인식 엔진 가동!")
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        audio_path = download_audio(video_id, tmp_dir)
                        # Whisper API 호출 로직 (생략 - 사장님 키 사용)
                        # ... 분석 결과 출력 ...
                
                status.update(label="✅ 분석 완료!", state="complete")
                st.success(f"{st.session_state.user['email']}님, 분석이 끝났습니다!")
