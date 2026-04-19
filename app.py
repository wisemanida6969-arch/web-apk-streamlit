import streamlit as st
import re
import os
import json
import requests
import db
from datetime import datetime
from urllib.parse import urlencode
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI

# ─── Deploy Version (change this to verify deployment) ───
APP_VERSION = "2026-04-07-v1"

# ─── Config ───
st.set_page_config(
    page_title="Trytimeback - AI YouTube Summarizer & PDF Export",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════
# Paddle _ptxn handler — render hosted checkout for any transaction
# ══════════════════════════════════════
# Paddle Billing redirects users to the seller's default payment link URL
# with ?_ptxn=<transaction_id>. Sister apps (PetLog, PostGenie) in the
# same Paddle seller account create transactions and Paddle sends users
# here because trytimeback.com is the account's default approved domain.
#
# Render the checkout by injecting paddle.js and calling
# Paddle.Checkout.open({ transactionId }) — works for any product/price
# in the same Paddle seller account.
_ptxn = st.query_params.get("_ptxn")
if _ptxn:
    import streamlit.components.v1 as _ptxn_components
    # Read Paddle client token from env first (set on Railway), fall back
    # to the hardcoded value that matches the current seller account.
    _PADDLE_CLIENT_TOKEN = (
        os.environ.get("PADDLE_CLIENT_TOKEN")
        or "live_1a8fd1443de5064e970587e81c9"
    ).strip()
    # IMPORTANT: Paddle's checkout iframe sets `frame-ancestors 'none'` CSP,
    # so it cannot be nested inside Streamlit's component iframe.
    # We must escape to window.top and run paddle.js there.
    _ptxn_components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Complete your payment — Paddle</title>
      <style>
        body {{
          margin: 0;
          font-family: -apple-system, 'Inter', sans-serif;
          background: transparent;
          color: #e4e4ed;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }}
        .box {{
          max-width: 440px;
          text-align: center;
          padding: 32px;
          background: rgba(255,255,255,0.04);
          border-radius: 16px;
          border: 1px solid rgba(255,255,255,0.08);
        }}
        .box h1 {{ font-size: 1.4rem; margin: 0 0 10px; }}
        .box p {{ color: #9aa; font-size: 0.95rem; line-height: 1.6; }}
        .spin {{
          display: inline-block; width: 28px; height: 28px;
          border: 3px solid rgba(255,255,255,0.15);
          border-top-color: #8ab4ff;
          border-radius: 50%;
          animation: spin 0.9s linear infinite;
          margin-bottom: 12px;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
      </style>
    </head>
    <body>
      <div class="box">
        <div class="spin"></div>
        <h1>🔒 결제창을 여는 중...</h1>
        <p>잠시만 기다려주세요. Paddle 결제창이 곧 표시됩니다.</p>
      </div>
      <script>
        (function() {{
          var TOP = window.top;
          var TXN = '{_ptxn}';
          var TOKEN = '{_PADDLE_CLIENT_TOKEN}';

          function showError(msg) {{
            try {{
              document.querySelector('.box').innerHTML =
                '<h1>⚠️ 결제창을 열 수 없어요</h1><p>' + msg + '</p>';
            }} catch (_) {{}}
          }}

          function openCheckout() {{
            try {{
              if (!TOP._tbPaddleInited) {{
                TOP.Paddle.Initialize({{ token: TOKEN }});
                TOP._tbPaddleInited = true;
              }}
              TOP.Paddle.Checkout.open({{ transactionId: TXN }});
            }} catch (e) {{
              showError(e.message || 'Unknown error');
            }}
          }}

          function loadPaddleAndOpen() {{
            // 이미 top frame 에 paddle.js 가 있으면 바로 오픈
            if (TOP.Paddle) {{ openCheckout(); return; }}
            // 없으면 top frame 에 script 태그 주입
            var existing = TOP.document.getElementById('tb-paddle-sdk');
            if (existing) {{
              // 로딩 대기
              var waited = 0;
              var poll = setInterval(function() {{
                waited += 200;
                if (TOP.Paddle) {{ clearInterval(poll); openCheckout(); }}
                else if (waited >= 8000) {{
                  clearInterval(poll);
                  showError('Paddle SDK 로드 실패');
                }}
              }}, 200);
              return;
            }}
            var s = TOP.document.createElement('script');
            s.id = 'tb-paddle-sdk';
            s.src = 'https://cdn.paddle.com/paddle/v2/paddle.js';
            s.onload = openCheckout;
            s.onerror = function() {{
              showError('paddle.js 다운로드 실패');
            }};
            TOP.document.head.appendChild(s);
          }}

          try {{
            loadPaddleAndOpen();
          }} catch (e) {{
            showError('window.top 접근 실패: ' + (e.message || e));
          }}
        }})();
      </script>
    </body>
    </html>
    """, height=300, scrolling=False)
    st.stop()


# ─── SEO: Inject meta tags into the MAIN page via window.top ───
import streamlit.components.v1 as seo_components
seo_components.html("""
<script>
(function() {
    var doc = window.top.document;

    // 1) Force <title>
    doc.title = 'Trytimeback - AI YouTube Summarizer & PDF Export';

    // 2) Helper: set or create <meta>
    function setMeta(attr, attrVal, content) {
        var el = doc.querySelector('meta[' + attr + '="' + attrVal + '"]');
        if (!el) {
            el = doc.createElement('meta');
            el.setAttribute(attr, attrVal);
            doc.head.appendChild(el);
        }
        el.setAttribute('content', content);
    }

    // 3) Primary SEO
    setMeta('name', 'description', 'Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week with Trytimeback.');
    setMeta('name', 'keywords', 'YouTube summary, AI summarizer, PDF export, lecture notes, Trytimeback, 유튜브 요약, AI 요약');
    setMeta('name', 'author', 'Trytimeback');
    setMeta('name', 'robots', 'index, follow');

    // 4) Open Graph
    setMeta('property', 'og:title', 'Trytimeback - AI YouTube Summarizer & PDF Export');
    setMeta('property', 'og:description', 'Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week with Trytimeback.');
    setMeta('property', 'og:type', 'website');
    setMeta('property', 'og:url', 'https://trytimeback.com');
    setMeta('property', 'og:site_name', 'Trytimeback');
    setMeta('property', 'og:locale', 'en_US');

    // 5) Twitter Card
    setMeta('name', 'twitter:card', 'summary_large_image');
    setMeta('name', 'twitter:title', 'Trytimeback - AI YouTube Summarizer & PDF Export');
    setMeta('name', 'twitter:description', 'Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week.');

    // 6) Canonical URL
    if (!doc.querySelector('link[rel="canonical"]')) {
        var link = doc.createElement('link');
        link.rel = 'canonical';
        link.href = 'https://trytimeback.com';
        doc.head.appendChild(link);
    }

    // 7) <html lang="en">
    doc.documentElement.setAttribute('lang', 'en');

    // 8) JSON-LD Structured Data
    if (!doc.querySelector('script[data-seo="trytimeback"]')) {
        var ld = doc.createElement('script');
        ld.type = 'application/ld+json';
        ld.setAttribute('data-seo', 'trytimeback');
        ld.textContent = JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": "Trytimeback",
            "url": "https://trytimeback.com",
            "description": "Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week.",
            "applicationCategory": "EducationalApplication",
            "operatingSystem": "Web",
            "offers": {
                "@type": "AggregateOffer",
                "lowPrice": "9.99",
                "highPrice": "29.99",
                "priceCurrency": "USD",
                "offerCount": "4"
            }
        });
        doc.head.appendChild(ld);
    }

    // 9) Update <noscript> — for crawlers that read it
    var ns = doc.querySelector('noscript');
    if (ns) {
        ns.innerHTML = '<div style="font-family:sans-serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.8;">' +
            '<h1>Trytimeback - AI YouTube Summarizer</h1>' +
            '<p>Paste any YouTube lecture URL and get 5 key-point short clips + a detailed PDF summary in seconds.</p>' +
            '<ul><li>5 AI-curated key moment clips</li><li>Comprehensive PDF summary download</li>' +
            '<li>Multi-language subtitle support</li><li>Mobile responsive</li></ul>' +
            '<p>Basic $12.99/mo | Pro $29.99/mo — Save up to 23% with yearly billing</p>' +
            '<p><a href="https://trytimeback.com">trytimeback.com</a></p></div>';
    }

    console.log('[SEO] Meta tags injected into top document');
})();
</script>
""", height=0, scrolling=False)

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

# YouTube Data API Key
YOUTUBE_API_KEY = get_secret("YOUTUBE_API_KEY")

# ─── Admin Config ───
ADMIN_EMAIL = "wisemanida6969@gmail.com"

def generate_summary_pdf(result: dict) -> bytes:
    """Generate a PDF with full video summary and key points."""
    from fpdf import FPDF
    import os

    class PDF(FPDF):
        def header(self):
            self.set_font("NotoSans", "B", 14)
            self.set_text_color(60, 60, 60)
            self.cell(0, 10, "Trytimeback - Video Summary", align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(100, 80, 220)
            self.set_line_width(0.8)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font("NotoSans", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Generated by Trytimeback (trytimeback.com)  |  Page {self.page_no()}", align="C")

    pdf = PDF()

    # Register Korean font
    font_path = os.path.join(os.path.dirname(__file__), "NotoSansKR-Regular.ttf")
    font_bold_path = os.path.join(os.path.dirname(__file__), "NotoSansKR-Bold.ttf")
    if os.path.exists(font_path):
        pdf.add_font("NotoSans", "", font_path)
        pdf.add_font("NotoSans", "B", font_bold_path if os.path.exists(font_bold_path) else font_path)
    else:
        # Fallback: download from Google Fonts CDN
        import urllib.request
        font_url = "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
        try:
            urllib.request.urlretrieve(font_url, font_path)
            pdf.add_font("NotoSans", "", font_path)
            pdf.add_font("NotoSans", "B", font_path)
        except Exception:
            # Use built-in font (limited Korean support)
            pdf.add_font("NotoSans", "", font_path if os.path.exists(font_path) else "")

    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    vid = result["videoId"]
    total_dur = result["totalDuration"]
    generated = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    # Video info
    pdf.set_font("NotoSans", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Video: youtube.com/watch?v={vid}  |  Duration: {fmt(total_dur)}  |  Generated: {generated}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Full Summary Section
    full_summary = result.get("full_summary")
    if full_summary:
        # Title
        pdf.set_font("NotoSans", "B", 16)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 9, full_summary.get("title", "Video Summary"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Overview
        pdf.set_font("NotoSans", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, full_summary.get("overview", ""), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # Sections
        for sec in full_summary.get("sections", []):
            pdf.set_font("NotoSans", "B", 12)
            pdf.set_text_color(80, 60, 200)
            pdf.multi_cell(0, 7, f"■ {sec['heading']}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.set_font("NotoSans", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 6, sec["content"], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        # Key Takeaways
        takeaways = full_summary.get("key_takeaways", [])
        if takeaways:
            pdf.ln(2)
            pdf.set_font("NotoSans", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, "Key Takeaways", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.set_font("NotoSans", "", 10)
            pdf.set_text_color(50, 50, 50)
            for i, t in enumerate(takeaways):
                pdf.multi_cell(0, 6, f"  {i+1}. {t}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1)

        # Conclusion
        conclusion = full_summary.get("conclusion", "")
        if conclusion:
            pdf.ln(4)
            pdf.set_font("NotoSans", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, "Conclusion", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.set_font("NotoSans", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 6, conclusion, new_x="LMARGIN", new_y="NEXT")

    # Key Points Section
    pdf.add_page()
    pdf.set_font("NotoSans", "B", 14)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, "Key Points for Shorts", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for i, p in enumerate(result["points"]):
        start = int(p["startTime"])
        end = int(p["endTime"])
        keywords = p.get("keywords", [])

        # Point header
        pdf.set_font("NotoSans", "B", 11)
        pdf.set_text_color(80, 60, 200)
        pdf.multi_cell(0, 7, f"#{i+1}  {p['title']}", new_x="LMARGIN", new_y="NEXT")

        # Time
        pdf.set_font("NotoSans", "", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, f"{fmt(start)} - {fmt(end)}  ({end - start}s)", new_x="LMARGIN", new_y="NEXT")

        # Summary
        pdf.set_font("NotoSans", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, p["summary"], new_x="LMARGIN", new_y="NEXT")

        # Keywords
        if keywords:
            pdf.set_font("NotoSans", "", 9)
            pdf.set_text_color(100, 80, 200)
            pdf.cell(0, 5, "  ".join(f"#{k}" for k in keywords), new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)

    # Disclaimer
    pdf.ln(4)
    pdf.set_font("NotoSans", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4, "This summary is for personal educational use only. AI-generated content may not be 100% accurate.",
                   new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())

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

def _oauth_client_id() -> str:
    return get_secret("GOOGLE_CLIENT_ID", _DEFAULT_CID)


def _oauth_redirect_uri() -> str:
    # Always resolve from env/defaults so the value used to build the auth URL
    # is identical to the value used during token exchange, regardless of
    # Streamlit session lifetime. Any mismatch here causes Google to 400 with
    # "redirect_uri_mismatch".
    return get_secret("REDIRECT_URI", _DEFAULT_RURI)


def get_google_login_url() -> str:
    params = {
        "client_id": _oauth_client_id(),
        "redirect_uri": _oauth_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    cid = _oauth_client_id()
    csecret = get_secret("GOOGLE_CLIENT_SECRET", _DEFAULT_SEC)
    ruri = _oauth_redirect_uri()
    payload = {
        "client_id": cid,
        "client_secret": csecret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": ruri,
    }
    resp = requests.post("https://oauth2.googleapis.com/token", data=payload, timeout=10)
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
    if not code or st.session_state.get("logged_in"):
        return

    # Guard against re-exchanging the same code on reruns / refreshes.
    # Google's `code` is single-use; a second exchange returns 400 invalid_grant.
    if st.session_state.get("_oauth_code_used") == code:
        st.query_params.clear()
        return

    st.session_state["_oauth_code_used"] = code
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
        ruri = _oauth_redirect_uri()
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


def parse_iso8601_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration (PT1H2M3S) to total seconds."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
    if not m:
        return 0
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


# ─── YouTube Data API v3 ───

def get_video_info(video_id: str) -> dict | None:
    """Fetch video metadata using YouTube Data API v3."""
    if not YOUTUBE_API_KEY:
        return None
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,contentDetails,statistics",
                "id": video_id,
                "key": YOUTUBE_API_KEY,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("items"):
            return None
        item = data["items"][0]
        snippet = item["snippet"]
        details = item["contentDetails"]
        stats = item.get("statistics", {})
        return {
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "duration": parse_iso8601_duration(details.get("duration", "")),
            "view_count": int(stats.get("viewCount", 0)),
            "published_at": snippet.get("publishedAt", "")[:10],
        }
    except Exception as e:
        import sys
        print(f"[YT-API] Failed to get video info: {e}", file=sys.stderr, flush=True)
        return None


# ─── Subtitle Extraction ───

import streamlit.components.v1 as components


def _try_fetch(api, video_id: str, label: str) -> list[dict] | None:
    """Try fetching subtitles with given api instance."""
    import sys
    for langs in [["ko"], ["en"], ["ko", "en"]]:
        try:
            print(f"[SUBTITLE][{label}] Trying languages={langs} for {video_id}", file=sys.stderr, flush=True)
            data = api.fetch(video_id, languages=langs)
            print(f"[SUBTITLE][{label}] SUCCESS! Got {len(data)} snippets", file=sys.stderr, flush=True)
            return [
                {"text": snippet.text, "start": snippet.start, "duration": snippet.duration}
                for snippet in data
            ]
        except Exception as e:
            print(f"[SUBTITLE][{label}] Failed with {langs}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            continue
    # Last resort: no language preference
    try:
        print(f"[SUBTITLE][{label}] Trying without language preference", file=sys.stderr, flush=True)
        data = api.fetch(video_id)
        print(f"[SUBTITLE][{label}] SUCCESS! Got {len(data)} snippets", file=sys.stderr, flush=True)
        return [
            {"text": snippet.text, "start": snippet.start, "duration": snippet.duration}
            for snippet in data
        ]
    except Exception as e:
        print(f"[SUBTITLE][{label}] Failed: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return None


def fetch_subtitles(video_id: str) -> list[dict] | None:
    """Fetch YouTube subtitles using Webshare residential proxy."""
    import sys
    from youtube_transcript_api.proxies import WebshareProxyConfig

    proxy_user = os.environ.get("WEBSHARE_PROXY_USER", "")
    proxy_pass = os.environ.get("WEBSHARE_PROXY_PASS", "")

    # 1) Try with WebshareProxyConfig (built-in rotating residential proxy)
    if proxy_user and proxy_pass:
        try:
            print(f"[SUBTITLE] Using WebshareProxyConfig (user={proxy_user[:4]}...)", file=sys.stderr, flush=True)
            proxy_config = WebshareProxyConfig(
                proxy_username=proxy_user,
                proxy_password=proxy_pass,
                retries_when_blocked=10,
            )
            api = YouTubeTranscriptApi(proxy_config=proxy_config)
            result = _try_fetch(api, video_id, "WEBSHARE")
            if result:
                return result
            print(f"[SUBTITLE] WebshareProxyConfig returned no results", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[SUBTITLE] WebshareProxyConfig failed: {type(e).__name__}: {e}", file=sys.stderr, flush=True)

    # 2) Fallback: try direct (no proxy)
    try:
        print(f"[SUBTITLE] Falling back to direct (no proxy)", file=sys.stderr, flush=True)
        api_direct = YouTubeTranscriptApi()
        result = _try_fetch(api_direct, video_id, "DIRECT")
        if result:
            return result
    except Exception as e:
        print(f"[SUBTITLE] Direct method failed: {type(e).__name__}: {e}", file=sys.stderr, flush=True)

    print(f"[SUBTITLE] All methods exhausted for {video_id}", file=sys.stderr, flush=True)
    return None


def render_youtube_clip(video_id: str, start: int = 0, end: int = 0):
    """Render a YouTube clip player using official iframe embed.
    Video plays in user's browser — no server-side download needed."""
    end_param = f"&end={end}" if end else ""
    html_code = f"""
    <div style="border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.3); margin: 8px 0; position: relative; padding-bottom: 56.25%; height: 0;">
        <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
            src="https://www.youtube.com/embed/{video_id}?start={start}{end_param}&rel=0&modestbranding=1"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen>
        </iframe>
    </div>
    """
    components.html(html_code, height=320)


# ─── GPT Analysis ───

def analyze_with_gpt(transcript_text: str, total_duration: float, api_key: str) -> dict:
    """Analyze transcript: returns {"points": [...], "full_summary": "..."}"""
    client = OpenAI(api_key=api_key)

    prompt = f"""You are a professional lecture note-taker. Below is the full transcript of a YouTube video ({int(total_duration)} seconds long).

You MUST produce TWO outputs in JSON:

1. "points": 5 key clips for short-form videos
2. "full_summary": a THOROUGH written document that fully replaces watching the video

CRITICAL: The full_summary must be EXTREMELY detailed. A student who reads this document should NEVER need to watch the original video. Every important idea, fact, example, name, number, story, and argument from the transcript must appear in the summary.

JSON format:
{{
  "points": [
    {{
      "title": "Key point title",
      "summary": "2-3 sentence summary",
      "startTime": start_time_in_seconds,
      "endTime": end_time_in_seconds,
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ],
  "full_summary": {{
    "title": "Video title/topic",
    "overview": "A comprehensive 6-8 sentence paragraph introducing what the video covers, who the speaker is, and the main thesis.",
    "sections": [
      {{
        "heading": "Section title",
        "content": "A LONG, DETAILED paragraph of 10-15 sentences. Mention every specific example, story, statistic, person, company, date, or argument the speaker discusses in this part. Paraphrase the speaker's actual words — do not just say 'the speaker discusses X', instead write WHAT they said about X in detail."
      }}
    ],
    "key_takeaways": ["Complete actionable sentence 1", "Complete actionable sentence 2"],
    "conclusion": "5-6 sentence conclusion summarizing the overall message, implications, and call to action if any."
  }}
}}

Rules for points:
- Exactly 5 key points, 45-75 seconds each, sorted chronologically
- Timestamps must match the transcript

Rules for full_summary:
- Language: match the transcript language (Korean transcript → Korean output, English → English, etc.)
- 5-8 sections, each with 10-15 sentences of REAL CONTENT (not filler)
- DO NOT write generic statements like "the speaker discusses various topics" — write the ACTUAL content
- Include direct paraphrases, specific numbers, names, dates, examples, anecdotes
- key_takeaways: 6-10 items, each a full sentence with specific information
- Total full_summary should be 1500-3000 words equivalent

Transcript:
{transcript_text}"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=16384,
    )
    text = resp.choices[0].message.content
    # Try parsing as full object first
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        parsed = json.loads(obj_match.group())
        if "points" in parsed and "full_summary" in parsed:
            return parsed
    # Fallback: array-only response
    arr_match = re.search(r"\[[\s\S]*\]", text)
    if arr_match:
        return {"points": json.loads(arr_match.group()), "full_summary": None}
    raise ValueError("Could not parse JSON from GPT response.")


# ─── Main Processing Pipeline ───

def process_video(video_id: str, api_key: str):
    """Fetch subtitles and analyze with GPT."""
    progress = st.progress(0, text="🔍 Starting analysis...")
    status = st.status("🔍 Analyzing video...", expanded=True)

    # Step 1: Fetch subtitles (0% → 40%)
    progress.progress(10, text="📝 Step 1/3 — Fetching subtitles via proxy...")
    status.write("📝 Fetching subtitles...")
    transcript = fetch_subtitles(video_id)

    if not transcript:
        progress.empty()
        status.update(label="❌ No subtitles found", state="error")
        st.error("😔 **No subtitles found for this video.**\n\n"
                 "Please try a video with subtitles (including auto-generated ones).\n\n"
                 "💡 **Tip:** Most YouTube videos have auto-generated subtitles.")
        return None

    total_duration = transcript[-1]["start"] + transcript[-1]["duration"]
    progress.progress(40, text="✅ Step 1/3 — Subtitles loaded!")
    status.write(f"✅ Subtitles loaded: {len(transcript)} segments, {fmt(total_duration)} total")

    # Step 2: GPT analysis (40% → 90%) with animated progress
    import threading, time
    progress.progress(45, text="🤖 Step 2/3 — AI analyzing content...")
    status.write("🤖 GPT-4o-mini analyzing key points + full summary...")
    transcript_text = "\n".join(
        f"[{fmt(s['start'])}] {s['text']}" for s in transcript
    )

    tips = [
        "🤖 AI is reading the transcript...",
        "🔍 Identifying key points...",
        "📝 Writing detailed summary...",
        "📊 Extracting facts and examples...",
        "✍️ Finalizing analysis...",
    ]
    gpt_result = {"done": False, "data": None, "error": None}

    def run_gpt():
        try:
            gpt_result["data"] = analyze_with_gpt(transcript_text, total_duration, api_key)
        except Exception as e:
            gpt_result["error"] = e
        gpt_result["done"] = True

    thread = threading.Thread(target=run_gpt)
    thread.start()

    pct = 45
    tip_idx = 0
    while not gpt_result["done"]:
        time.sleep(1.5)
        if pct < 88:
            pct += 2
        tip_text = tips[tip_idx % len(tips)]
        progress.progress(pct, text=f"🤖 Step 2/3 — {tip_text} ({pct}%)")
        tip_idx += 1

    thread.join()
    if gpt_result["error"]:
        raise gpt_result["error"]
    analysis = gpt_result["data"]

    # Step 3: Done (90% → 100%)
    progress.progress(100, text="✅ Step 3/3 — Analysis complete!")
    status.update(label="✅ Analysis complete!", state="complete")

    return {
        "videoId": video_id,
        "totalDuration": int(total_duration),
        "source": "subtitle",
        "points": analysis["points"],
        "full_summary": analysis.get("full_summary"),
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

    /* ─── Mobile Responsive ─── */
    @media (max-width: 768px) {
        .block-container { max-width: 100%; padding-left: 1rem; padding-right: 1rem; }
        .login-box { padding: 32px 20px; max-width: 95%; border-radius: 20px; }
        .login-title { font-size: 1.8rem; }
        .login-desc { font-size: 0.9rem; margin-bottom: 20px; }
        .short-card { border-radius: 14px; }
        .card-header { padding: 10px 14px; font-size: 0.85rem; }
        .card-body { padding: 12px 14px; }
        .card-summary { font-size: 0.82rem; }
        .keyword-tag { font-size: 0.7rem; padding: 3px 8px; }
        .time-badge { font-size: 0.75rem; }
        .pricing-container { gap: 1.2rem; }
        .pricing-card { width: 100%; max-width: 340px; padding: 1.8rem; border-radius: 18px; }
        .pricing-card:hover { transform: none; }
        .feature-list li { font-size: 0.85rem; }
    }
    @media (max-width: 480px) {
        .login-box { padding: 24px 16px; }
        .login-title { font-size: 1.5rem; }
        .card-header { font-size: 0.8rem; padding: 8px 12px; }
        .card-body { padding: 10px 12px; }
    }
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

    # ── Hero Section with Logo ──
    import base64
    logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width: 220px; margin-bottom: 12px; border-radius: 16px;" alt="Trytimeback Logo">'
    else:
        logo_html = '<div style="font-size: 3.5rem; margin-bottom: 8px;">🎬</div>'

    st.markdown(f"""
    <div style="text-align: center; padding: 40px 20px 20px;">
        {logo_html}
        <div style="
            font-size: 1.3rem; font-weight: 300; color: rgba(200, 200, 230, 0.9);
            margin-bottom: 6px;
        ">Stop watching. Start learning.</div>
        <div style="
            font-size: 0.95rem; color: rgba(140, 140, 170, 0.7);
            max-width: 500px; margin: 0 auto;
        ">AI-powered YouTube lecture analyzer that extracts key insights<br>so you can learn in minutes, not hours.</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sign In Button ──
    st.markdown(f"""
    <div style="text-align: center; margin: 28px auto 16px;">
        <a href="{login_url}" style="text-decoration: none; display: inline-block;">
            <div style="
                background: #ffffff;
                border-radius: 40px;
                padding: 14px 40px;
                display: inline-flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.08);
                transition: all 0.3s ease;
                cursor: pointer;
            ">
                <svg width="20" height="20" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59A14.5 14.5 0 0 1 9.5 24c0-1.59.28-3.14.76-4.59l-7.98-6.19A23.99 23.99 0 0 0 0 24c0 3.77.9 7.35 2.56 10.54l7.97-5.95z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 5.95C6.51 42.62 14.62 48 24 48z"/></svg>
                <span style="
                    color: #3c4043;
                    font-size: 1rem;
                    font-weight: 600;
                    font-family: 'Inter', -apple-system, sans-serif;
                    letter-spacing: 0.01em;
                ">Sign in with Google</span>
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # ── How It Works ──
    st.markdown("""
    <div style="text-align: center; margin: 30px auto 10px;">
        <div style="font-size: 1.1rem; font-weight: 700; color: rgba(220, 220, 240, 0.85); margin-bottom: 20px;">
            How It Works
        </div>
    </div>
    """, unsafe_allow_html=True)

    hw1, hw2, hw3 = st.columns(3)
    with hw1:
        st.markdown("""
        <div style="text-align:center; padding: 20px 12px; background: rgba(15,15,35,0.5); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 8px;">📋</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #e8e8f0; margin-bottom: 4px;">1. Paste URL</div>
            <div style="font-size: 0.78rem; color: rgba(160,160,195,0.7);">Drop any YouTube lecture link</div>
        </div>
        """, unsafe_allow_html=True)
    with hw2:
        st.markdown("""
        <div style="text-align:center; padding: 20px 12px; background: rgba(15,15,35,0.5); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 8px;">🤖</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #e8e8f0; margin-bottom: 4px;">2. AI Analyzes</div>
            <div style="font-size: 0.78rem; color: rgba(160,160,195,0.7);">GPT extracts key points & summary</div>
        </div>
        """, unsafe_allow_html=True)
    with hw3:
        st.markdown("""
        <div style="text-align:center; padding: 20px 12px; background: rgba(15,15,35,0.5); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px;">
            <div style="font-size: 2rem; margin-bottom: 8px;">🎯</div>
            <div style="font-size: 0.9rem; font-weight: 700; color: #e8e8f0; margin-bottom: 4px;">3. Learn Fast</div>
            <div style="font-size: 0.78rem; color: rgba(160,160,195,0.7);">Watch shorts & download PDF</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Feature Highlights ──
    st.markdown("""
    <div style="
        max-width: 650px; margin: 30px auto 10px; padding: 28px 32px;
        background: rgba(15, 15, 35, 0.4);
        border: 1px solid rgba(99, 71, 237, 0.12);
        border-radius: 20px;
    ">
        <div style="text-align: center; font-size: 1.1rem; font-weight: 700; color: rgba(220, 220, 240, 0.85); margin-bottom: 20px;">
            Why Trytimeback?
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="font-size: 1.3rem;">⚡</span>
                <div>
                    <div style="font-size: 0.88rem; font-weight: 600; color: #e8e8f0;">60-Second Shorts</div>
                    <div style="font-size: 0.75rem; color: rgba(160,160,195,0.7);">5 key moments auto-clipped from any lecture</div>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="font-size: 1.3rem;">📄</span>
                <div>
                    <div style="font-size: 0.88rem; font-weight: 600; color: #e8e8f0;">Full PDF Summary</div>
                    <div style="font-size: 0.75rem; color: rgba(160,160,195,0.7);">Detailed notes you can study offline</div>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="font-size: 1.3rem;">🌍</span>
                <div>
                    <div style="font-size: 0.88rem; font-weight: 600; color: #e8e8f0;">Any Language</div>
                    <div style="font-size: 0.75rem; color: rgba(160,160,195,0.7);">Works with Korean, English & more</div>
                </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="font-size: 1.3rem;">🎓</span>
                <div>
                    <div style="font-size: 0.88rem; font-weight: 600; color: #e8e8f0;">Built for Students</div>
                    <div style="font-size: 0.75rem; color: rgba(160,160,195,0.7);">Save hours of study time every week</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats Bar ──
    st.markdown("""
    <div style="
        display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;
        margin: 24px auto 10px; padding: 16px 20px;
    ">
        <div style="text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; background: linear-gradient(135deg, #a78bfa, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">15 min</div>
            <div style="font-size: 0.75rem; color: rgba(140,140,170,0.6);">Free every month</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; background: linear-gradient(135deg, #34d399, #6ee7b7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">5 Shorts</div>
            <div style="font-size: 0.75rem; color: rgba(140,140,170,0.6);">Per video analysis</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; background: linear-gradient(135deg, #f472b6, #e879f9); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PDF</div>
            <div style="font-size: 0.75rem; color: rgba(140,140,170,0.6);">Full summary download</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.6rem; font-weight: 800; background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">GPT-4o</div>
            <div style="font-size: 0.75rem; color: rgba(140,140,170,0.6);">Powered by OpenAI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer Links ──
    st.markdown("---")
    fc = st.columns([1, 1, 1, 1])
    with fc[0]:
        if st.button("📋 Terms", use_container_width=True, key="login_terms"):
            st.session_state["login_show"] = "terms"
    with fc[1]:
        if st.button("🔒 Privacy", use_container_width=True, key="login_privacy"):
            st.session_state["login_show"] = "privacy"
    with fc[2]:
        if st.button("💰 Refund", use_container_width=True, key="login_refund"):
            st.session_state["login_show"] = "refund"
    with fc[3]:
        st.link_button("📧 Contact", "mailto:admin@trytimeback.com", use_container_width=True)

    login_show = st.session_state.get("login_show", "")
    if login_show == "terms":
        with st.expander("📋 Terms of Service", expanded=True):
            st.markdown("""
**Article 1 (Purpose)**
These terms govern the conditions and procedures for using the AI-based YouTube summary service provided by 'Trytimeback'.

**Article 2 (Service Description)**
The Service analyzes YouTube lecture videos using AI to extract key points and generate summaries for educational purposes.

**Article 3 (User Obligations)**
Users must not use the Service for illegal purposes or infringe on third-party copyrights.

*Effective Date: April 5, 2026*
            """)
            if st.button("Close", key="login_close_terms"):
                st.session_state["login_show"] = ""
                st.rerun()
    elif login_show == "privacy":
        with st.expander("🔒 Privacy Policy", expanded=True):
            st.markdown("""
**1. Personal Information Collected**
The Service collects your email address, name (nickname), and profile picture through Google Sign-In.

**2. Purpose of Collection**
Used for managing analysis records and user identification.

**3. Retention & Disposal**
Personal information is retained until the user requests withdrawal or the service is terminated.

**4. Third-Party Sharing & Processing**
The Service may transmit audio/text data to the OpenAI API for analysis; no personally identifiable information is included.

**5. User Rights**
Users may request to view, modify, or delete their personal information at any time.

*Effective Date: April 5, 2026*
            """)
            if st.button("Close", key="login_close_privacy"):
                st.session_state["login_show"] = ""
                st.rerun()
    elif login_show == "refund":
        with st.expander("💰 Refund Policy", expanded=True):
            st.markdown("""
At Trytimeback, we want you to be satisfied with our AI video summary services.

**1. Subscription Refunds:**
You are eligible for a full refund within 7 days of your initial purchase, provided that you have not used the premium features.

**2. How to Request a Refund:**
To request a refund, please contact us at admin@trytimeback.com. We will process your request within 3-5 business days.

**3. Automatic Cancellations:**
You can cancel your subscription at any time through your account settings. Once canceled, you will not be charged for the next billing cycle.
            """)
            if st.button("Close", key="login_close_refund"):
                st.session_state["login_show"] = ""
                st.rerun()

    st.markdown("""
    <div style="text-align: center; margin-top: 20px; font-size: 0.72rem; color: rgba(100, 100, 130, 0.5);">
        &copy; 2026 Trytimeback. All rights reserved.
    </div>
    """, unsafe_allow_html=True)

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
    <div style="text-align:center; color:rgba(140,140,170,0.6); font-size:0.78rem; margin-top:-1rem; margin-bottom:1.5rem;">🖥️ Best on desktop · 📱 Mobile supported</div>
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

    # ─── 사용량 표시 ───
    FREE_DAILY_LIMIT = 3
    used_today = db.get_daily_usage(user_email)
    remaining_today = max(0, FREE_DAILY_LIMIT - used_today)
    if not is_admin():
        pct = min(used_today / FREE_DAILY_LIMIT, 1.0)
        st.markdown(f"**오늘 남은 분석:** {remaining_today}/{FREE_DAILY_LIMIT}회")
        st.progress(pct)
        if remaining_today == 0:
            st.error("오늘 무료 횟수 소진! 내일 다시 이용하세요.")

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

    st.divider()
    st.markdown("**How to Use**")
    st.markdown("""
    1. Paste a YouTube URL
    2. Click **Analyze**
    3. View key point shorts!
    """)
    st.divider()
    st.markdown("**Features**")
    st.markdown("- 📝 Subtitle extraction (incl. auto-generated)")
    st.markdown("- 🤖 GPT-4o-mini key point analysis")
    st.markdown("- 🎬 YouTube embedded video playback")
    st.markdown("- 📄 PDF full summary download")

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

st.info("📝 **Subtitle-based analysis:** AI analyzes YouTube subtitles (including auto-generated) to extract key points.")

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

# ─── Analysis Flow (2-step: browser fetches subtitles → server analyzes) ───

if url:
    video_id = extract_video_id(url)
    if video_id:
        # Show video info from YouTube Data API
        video_info = get_video_info(video_id)
        if video_info:
            st.markdown(f"""
            <div style="
                background: rgba(15, 15, 35, 0.6);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
                padding: 20px;
                margin: 16px 0;
            ">
                <div style="font-size: 1.1rem; font-weight: 700; color: #e8e8f0; margin-bottom: 8px;">
                    🎬 {video_info['title']}
                </div>
                <div style="font-size: 0.85rem; color: rgba(160,160,195,0.8); margin-bottom: 4px;">
                    📺 {video_info['channel']}  ·  ⏱ {fmt(video_info['duration'])}  ·  👁 {video_info['view_count']:,}회
                </div>
            </div>
            """, unsafe_allow_html=True)

if analyze:
    if not api_key:
        if is_admin():
            st.error("🔑 Please enter your OpenAI API key in the sidebar.")
        else:
            st.error("🔑 Service is temporarily unavailable. Please contact the administrator.")
    elif not url:
        st.error("Please enter a YouTube URL.")
    elif not is_admin() and remaining_today <= 0:
        st.error("⚠️ 오늘 무료 분석 횟수(3회)를 모두 사용했습니다. 내일 다시 이용해주세요.")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL.")
        else:
            try:
                result = process_video(video_id, api_key)
                if result:
                    if not is_admin():
                        db.increment_daily_usage(user_email)
                        st.toast(f"✅ 분석 완료! 오늘 남은 횟수: {remaining_today - 1}회")
                    st.session_state["result"] = result
            except Exception as e:
                st.error(f"Error: {e}")

# Results
if "result" in st.session_state:
    data = st.session_state["result"]
    vid = data["videoId"]
    points = data["points"]
    source = data["source"]

    st.markdown("---")

    badge = '<span class="source-badge source-subtitle">📝 Extracted from Subtitles</span>'
    st.markdown(
        f"<h2 style='text-align:center;'>Key Point Shorts</h2>"
        f"<p style='text-align:center;'>{badge}  |  {fmt(data['totalDuration'])} total</p>",
        unsafe_allow_html=True,
    )

    # ── Key Point Shorts (videos first) ──
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

                render_youtube_clip(vid, start, end)

    # ── PDF Full Summary Download ──
    st.markdown("---")
    st.markdown("<h3 style='text-align:center;'>📄 Full Video Summary</h3>", unsafe_allow_html=True)
    try:
        summary_pdf = generate_summary_pdf(data)
        st.download_button(
            label="📄 Download Full Summary (.pdf)",
            data=summary_pdf,
            file_name=f"summary_{vid}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
        st.caption("📁 The PDF file will be saved to your Downloads folder.")
    except Exception as e:
        import sys
        print(f"[PDF] Generation failed: {e}", file=sys.stderr, flush=True)
        st.warning(f"⚠️ PDF generation failed: {e}")

    # ── Copyright Disclaimer ──
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

# --- Paddle Pricing (all-in-one HTML component with toggle + cards + checkout) ---
import streamlit.components.v1 as paddle_components

pricing_full_html = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<script>
    // ── Inject Paddle.js into the TOP window (escapes the iframe) ──
    (function() {
        var top = window.top;
        if (top._paddleReady) return;          // already loaded

        // If Paddle SDK not yet in top window, inject it now
        if (!top.document.getElementById('paddle-sdk-script')) {
            var s = top.document.createElement('script');
            s.id = 'paddle-sdk-script';
            s.src = 'https://cdn.paddle.com/paddle/v2/paddle.js';
            s.onload = function() {
                top.Paddle.Initialize({
                    token: 'live_1a8fd1443de5064e970587e81c9',
                    environment: 'production'
                });
                top._paddleReady = true;
                console.log('[Paddle] Injected & initialized on TOP window');
            };
            top.document.head.appendChild(s);
        }
    })();

    function openCheckout(priceId) {
        var top = window.top;
        if (top.Paddle && top._paddleReady) {
            top.Paddle.Checkout.open({
                items: [{ priceId: priceId, quantity: 1 }]
            });
        } else {
            // SDK still loading — retry after 1s
            setTimeout(function() {
                if (top.Paddle) {
                    top.Paddle.Checkout.open({
                        items: [{ priceId: priceId, quantity: 1 }]
                    });
                } else {
                    alert('Payment system could not load. Please refresh the page.');
                }
            }, 1500);
        }
    }
    function toggleBilling() {
        var isYearly = document.getElementById('billingToggle').checked;
        document.getElementById('monthlyView').style.display = isYearly ? 'none' : 'flex';
        document.getElementById('yearlyView').style.display = isYearly ? 'flex' : 'none';
        document.getElementById('labelMonthly').style.color = isYearly ? 'rgba(140,140,170,0.6)' : '#e8e8f0';
        document.getElementById('labelMonthly').style.fontWeight = isYearly ? '400' : '700';
        document.getElementById('labelYearly').style.color = isYearly ? '#f1c40f' : 'rgba(140,140,170,0.6)';
        document.getElementById('labelYearly').style.fontWeight = isYearly ? '700' : '400';
        document.getElementById('promoBar').style.display = isYearly ? 'block' : 'none';
    }
</script>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', -apple-system, sans-serif; }
    .pricing-wrap { max-width: 780px; margin: 0 auto; padding: 10px 16px; }
    .pricing-header { text-align: center; margin-bottom: 24px; }
    .pricing-header h1 { font-size: 2.2rem; font-weight: 900; color: #e8e8f0; margin-bottom: 6px; letter-spacing: -0.03em; }
    .pricing-header p { color: #9090b0; font-size: 1rem; }

    /* Toggle Switch */
    .toggle-wrap { display: flex; align-items: center; justify-content: center; gap: 14px; margin: 20px 0 16px; }
    .toggle-label { font-size: 0.95rem; transition: all 0.3s; cursor: pointer; }
    .toggle-switch { position: relative; width: 56px; height: 30px; }
    .toggle-switch input { opacity: 0; width: 0; height: 0; }
    .toggle-slider {
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(255,255,255,0.1); border-radius: 30px; cursor: pointer;
        transition: 0.3s; border: 1px solid rgba(255,255,255,0.15);
    }
    .toggle-slider::before {
        content: ''; position: absolute; height: 22px; width: 22px;
        left: 3px; bottom: 3px; background: #e8e8f0;
        border-radius: 50%; transition: 0.3s;
    }
    .toggle-switch input:checked + .toggle-slider {
        background: linear-gradient(135deg, #f1c40f, #f39c12);
        border-color: rgba(241,196,15,0.5);
    }
    .toggle-switch input:checked + .toggle-slider::before { transform: translateX(26px); background: #1a1a2e; }

    /* Promo Bar */
    .promo-bar {
        display: none; text-align: center; margin: 0 auto 20px;
        background: linear-gradient(135deg, rgba(241,196,15,0.12), rgba(243,156,18,0.08));
        border: 1px solid rgba(241,196,15,0.25); border-radius: 14px;
        padding: 14px 24px;
    }
    .promo-bar .promo-title { font-size: 1.1rem; font-weight: 800; color: #f1c40f; }
    .promo-bar .promo-sub { font-size: 0.82rem; color: rgba(200,200,230,0.7); margin-top: 4px; }

    /* Cards Container */
    .cards { display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; }
    .card {
        background: rgba(15, 15, 35, 0.8); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 24px; padding: 36px 28px 28px; width: 340px;
        text-align: center; position: relative; transition: all 0.35s ease;
    }
    .card:hover { transform: translateY(-8px); border-color: rgba(99,71,237,0.4); box-shadow: 0 12px 40px rgba(99,71,237,0.12); }
    .card.pro { border: 2px solid #f1c40f; box-shadow: 0 8px 32px rgba(241,196,15,0.15); }
    .card.pro:hover { box-shadow: 0 16px 48px rgba(241,196,15,0.2); border-color: #f1c40f; }

    .badge-pop {
        position: absolute; top: -14px; left: 50%; transform: translateX(-50%);
        background: linear-gradient(135deg, #f1c40f, #f39c12); color: #1a1a2e;
        padding: 5px 18px; border-radius: 20px; font-weight: 800; font-size: 0.82rem;
        box-shadow: 0 4px 12px rgba(241,196,15,0.4); white-space: nowrap;
    }
    .plan-name { font-size: 1.4rem; font-weight: 700; color: #e8e8f0; margin-bottom: 8px; }
    .plan-price { font-size: 3rem; font-weight: 900; color: #e8e8f0; line-height: 1.1; }
    .plan-orig { font-size: 1rem; color: rgba(140,140,170,0.5); text-decoration: line-through; margin-bottom: 2px; }
    .plan-per { color: #9090b0; font-size: 0.88rem; margin-bottom: 4px; }
    .plan-total { font-size: 0.8rem; color: rgba(140,140,170,0.5); margin-bottom: 6px; }
    .save-badge {
        display: inline-block; background: linear-gradient(135deg, rgba(241,196,15,0.15), rgba(243,156,18,0.1));
        color: #f1c40f; padding: 5px 16px; border-radius: 30px;
        font-size: 0.82rem; font-weight: 700; margin-bottom: 16px;
        border: 1px solid rgba(241,196,15,0.25);
    }
    .features { list-style: none; padding: 0; text-align: left; margin-bottom: 24px; }
    .features li { color: #b0b0d0; font-size: 0.9rem; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }
    .features li b { color: #e8e8f0; }

    .btn {
        width: 100%; padding: 14px 0; border: none; border-radius: 12px;
        font-size: 1.05rem; font-weight: 700; cursor: pointer;
        transition: all 0.3s ease; letter-spacing: 0.01em;
    }
    .btn:hover { transform: translateY(-2px); }
    .btn-basic { background: linear-gradient(135deg, #6347ed, #a855f7); color: white; box-shadow: 0 4px 16px rgba(99,71,237,0.3); }
    .btn-basic:hover { box-shadow: 0 8px 28px rgba(99,71,237,0.4); }
    .btn-pro { background: linear-gradient(135deg, #f1c40f, #f39c12); color: #1a1a2e; box-shadow: 0 4px 16px rgba(241,196,15,0.3); }
    .btn-pro:hover { box-shadow: 0 8px 28px rgba(241,196,15,0.4); }
    .secure { text-align: center; margin-top: 20px; font-size: 0.78rem; color: rgba(140,140,170,0.5); }

    @media (max-width: 768px) {
        .cards { flex-direction: column; align-items: center; }
        .card { width: 100%; max-width: 360px; }
        .pricing-header h1 { font-size: 1.6rem; }
        .plan-price { font-size: 2.4rem; }
    }
</style>

<div class="pricing-wrap">
    <div class="pricing-header">
        <h1>Pricing Plans</h1>
        <p>Choose the best plan to save your time</p>
    </div>

    <!-- Toggle -->
    <div class="toggle-wrap">
        <span id="labelMonthly" class="toggle-label" style="color:#e8e8f0; font-weight:700;" onclick="document.getElementById('billingToggle').checked=false; toggleBilling();">Monthly</span>
        <label class="toggle-switch">
            <input type="checkbox" id="billingToggle" onchange="toggleBilling()">
            <span class="toggle-slider"></span>
        </label>
        <span id="labelYearly" class="toggle-label" style="color:rgba(140,140,170,0.6);" onclick="document.getElementById('billingToggle').checked=true; toggleBilling();">
            Yearly <span style="background:linear-gradient(135deg,#f1c40f,#f39c12); color:#1a1a2e; padding:2px 10px; border-radius:10px; font-size:0.75rem; font-weight:700; margin-left:4px;">SAVE 20%</span>
        </span>
    </div>

    <!-- Promo Bar (yearly only) -->
    <div class="promo-bar" id="promoBar">
        <div class="promo-title">🎉 Get 2 Months FREE!</div>
        <div class="promo-sub">Lock in the lowest price for a full year of productivity</div>
    </div>

    <!-- Monthly Cards -->
    <div class="cards" id="monthlyView">
        <div class="card">
            <div class="plan-name">Basic</div>
            <div class="plan-price">$12.99</div>
            <div class="plan-per">per month</div>
            <div style="height: 32px;"></div>
            <ul class="features">
                <li>✅ <b>300 Minutes</b> / month</li>
                <li>✅ Audio Analysis (Whisper)</li>
                <li>✅ PDF Summary Export</li>
                <li>✅ 7-Day Money Back</li>
            </ul>
            <button class="btn btn-basic" onclick="openCheckout('pri_01knn7r684skwj2z54htyseaj2')">Select Basic</button>
        </div>
        <div class="card pro">
            <div class="badge-pop">👑 MOST POPULAR</div>
            <div class="plan-name" style="color:#f1c40f;">Pro</div>
            <div class="plan-price" style="color:#f1c40f;">$29.99</div>
            <div class="plan-per">per month</div>
            <div style="height: 32px;"></div>
            <ul class="features">
                <li>✅ <b>1,200 Minutes</b> / month</li>
                <li>✅ <b>Priority</b> AI Processing</li>
                <li>✅ Unlimited Video Length</li>
                <li>✅ Advanced Insights (Mind-map)</li>
            </ul>
            <button class="btn btn-pro" onclick="openCheckout('pri_01knpry35zcjv6wqxsyjzdma9j')">👑 Go Pro</button>
        </div>
    </div>

    <!-- Yearly Cards -->
    <div class="cards" id="yearlyView" style="display:none;">
        <div class="card">
            <div class="plan-name">Basic</div>
            <div class="plan-orig">$12.99/mo</div>
            <div class="plan-price">$9.99</div>
            <div class="plan-per">per month</div>
            <div class="plan-total">Billed $119.88 / year</div>
            <div class="save-badge">💰 Save 23% Yearly!</div>
            <ul class="features">
                <li>✅ <b>300 Minutes</b> / month</li>
                <li>✅ Audio Analysis (Whisper)</li>
                <li>✅ PDF Summary Export</li>
                <li>✅ 7-Day Money Back</li>
            </ul>
            <button class="btn btn-basic" onclick="openCheckout('pri_01knn7hhdez2seb412f4t34g2c')">Select Basic — Yearly</button>
        </div>
        <div class="card pro">
            <div class="badge-pop">👑 MOST POPULAR</div>
            <div class="plan-name" style="color:#f1c40f;">Pro</div>
            <div class="plan-orig">$29.99/mo</div>
            <div class="plan-price" style="color:#f1c40f;">$23.99</div>
            <div class="plan-per">per month</div>
            <div class="plan-total" style="color:rgba(241,196,15,0.5);">Billed $287.88 / year</div>
            <div class="save-badge">💰 Save 20% Yearly!</div>
            <ul class="features">
                <li>✅ <b>1,200 Minutes</b> / month</li>
                <li>✅ <b>Priority</b> AI Processing</li>
                <li>✅ Unlimited Video Length</li>
                <li>✅ Advanced Insights (Mind-map)</li>
            </ul>
            <button class="btn btn-pro" onclick="openCheckout('pri_01knn7w9ppn9csr86fz0sq47zh')">👑 Go Pro — Yearly</button>
        </div>
    </div>

    <div class="secure">🔒 Secure payment powered by Paddle · Cancel anytime · 7-day money back guarantee</div>
</div>
"""
paddle_components.html(pricing_full_html, height=900, scrolling=True)

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

# ─── Refund Policy ───
st.markdown("---")
st.markdown("""
<div style="
    background: rgba(15, 15, 35, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 28px 32px;
    max-width: 700px;
    margin: 0 auto;
">
    <h3 style="color: #e8e8f0; margin-bottom: 16px;">Refund Policy</h3>
    <div style="font-size: 0.88rem; color: rgba(180, 180, 210, 0.85); line-height: 1.9;">
        <p>At Trytimeback, we want you to be satisfied with our AI video summary services.</p>
        <p><b style="color: rgba(220, 220, 240, 0.9);">1. Subscription Refunds:</b><br>
        You are eligible for a full refund within 7 days of your initial purchase, provided that you have not used the premium features (AI picks or 3D fitting).</p>
        <p><b style="color: rgba(220, 220, 240, 0.9);">2. How to Request a Refund:</b><br>
        To request a refund, please contact us at <a href="mailto:admin@trytimeback.com" style="color: #a78bfa;">admin@trytimeback.com</a>. We will process your request within 3-5 business days.</p>
        <p><b style="color: rgba(220, 220, 240, 0.9);">3. Automatic Cancellations:</b><br>
        You can cancel your subscription at any time through your account settings. Once canceled, you will not be charged for the next billing cycle.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Footer ───
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.85rem;'>"
    "📧 Contact: <a href='mailto:admin@trytimeback.com' style='color: gray;'>admin@trytimeback.com</a>"
    "</div>",
    unsafe_allow_html=True,
)
