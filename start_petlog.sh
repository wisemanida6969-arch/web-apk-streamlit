#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# PetLog AI — Railway start script
#
# Railway의 "Settings → Deploy → Custom Start Command" 에
#   bash start_petlog.sh
# 를 입력하면 이 스크립트가 실행됩니다.
#
# Procfile(web: ...)은 Trytimeback(app.py)가 사용하므로,
# PetLog 서비스는 Procfile을 우회해 이 스크립트로 부팅합니다.
# ─────────────────────────────────────────────────────────
set -euo pipefail

# Railway Volume이 마운트된 경우 DB / 사진 디렉토리 준비
if [ -n "${PETLOG_DB_PATH:-}" ]; then
    mkdir -p "$(dirname "$PETLOG_DB_PATH")"
fi
if [ -n "${PETLOG_PHOTO_DIR:-}" ]; then
    mkdir -p "$PETLOG_PHOTO_DIR"
fi

# Railway는 $PORT 환경변수로 바인딩 포트를 전달
PORT="${PORT:-8501}"

echo "🐾 Starting PetLog AI on port $PORT (with SEO reverse proxy)"
echo "   DB:     ${PETLOG_DB_PATH:-petlog.db}"
echo "   Photos: ${PETLOG_PHOTO_DIR:-petlog_photos}"
echo "   Domain: ${PETLOG_APP_URL:-https://petlog.trytimeback.com}"

# serve_petlog.py runs aiohttp on $PORT and proxies to Streamlit on
# STREAMLIT_INTERNAL_PORT. This lets /sitemap.xml and /robots.txt be
# served at the root for Google Search Console.
exec python serve_petlog.py
