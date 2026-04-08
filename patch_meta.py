"""Patch Streamlit's index.html for SEO + Paddle checkout on main page."""
import streamlit as st
import pathlib
import os
import re

# Find Streamlit's index.html
st_dir = pathlib.Path(st.__file__).parent
index_path = st_dir / "static" / "index.html"

PADDLE_TOKEN = os.environ.get(
    "PADDLE_CLIENT_TOKEN", "live_1a8fd1443de5064e970587e81c9"
)

if index_path.exists():
    html = index_path.read_text(encoding="utf-8")
    patched = False

    # ──────────────────────────────────────
    # 1) Set <html lang="ko">
    # ──────────────────────────────────────
    if '<html lang="ko">' not in html and "<html>" in html:
        html = html.replace("<html>", '<html lang="ko">')
        patched = True
    elif '<html lang="ko">' not in html:
        html, n = re.subn(r'<html(?!\s+lang=)', '<html lang="ko"', html, count=1)
        if n:
            patched = True

    # ──────────────────────────────────────
    # 2) Patch <title>
    # ──────────────────────────────────────
    if "<title>Streamlit</title>" in html:
        html = html.replace(
            "<title>Streamlit</title>",
            "<title>세월은간다 - AI 유튜브 요약 · 핵심 숏츠 5개 + PDF 추출 | trytimeback.com</title>",
        )
        patched = True

    # ──────────────────────────────────────
    # 3) SEO meta + Paddle SDK in <head>
    # ──────────────────────────────────────
    MARKER = "<!-- PATCHED-V3 -->"
    if MARKER not in html:
        # Remove any old patches
        html = re.sub(r'<!-- SEO-PATCHED-V2 -->.*?(?=</head>)', '', html, flags=re.DOTALL)
        html = re.sub(r'<!-- PADDLE-PARENT -->.*?(?=</head>)', '', html, flags=re.DOTALL)
        html = re.sub(r'<meta\s+name="description"[^>]*>\n?', '', html)
        html = re.sub(r'<meta\s+property="og:[^"]*"[^>]*>\n?', '', html)

        inject_block = f"""{MARKER}
<!-- ═══ SEO Meta Tags ═══ -->
<meta name="description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다. 학습 시간을 80%% 절약하세요!">
<meta name="keywords" content="유튜브 요약, AI 요약, 유튜브 강의 요약, PDF 요약, 핵심 숏츠, YouTube summary, AI lecture summary, trytimeback">
<meta name="author" content="Trytimeback">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://trytimeback.com">
<meta property="og:type" content="website">
<meta property="og:url" content="https://trytimeback.com">
<meta property="og:title" content="세월은간다 - AI 유튜브 요약 · 핵심 숏츠 + PDF 추출">
<meta property="og:description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다.">
<meta property="og:site_name" content="세월은간다 (Trytimeback)">
<meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="세월은간다 - AI 유튜브 요약 · 핵심 숏츠 + PDF 추출">
<meta name="twitter:description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성. 학습 시간 80%% 절약!">

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "세월은간다 (Trytimeback)",
  "url": "https://trytimeback.com",
  "description": "유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다.",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "Web",
  "offers": {{
    "@type": "AggregateOffer",
    "lowPrice": "9.99",
    "highPrice": "29.99",
    "priceCurrency": "USD",
    "offerCount": "4"
  }}
}}
</script>

<!-- ═══ Paddle.js on MAIN page (not inside iframe) ═══ -->
<script src="https://cdn.paddle.com/paddle/v2/paddle.js"></script>
<script>
  // Initialize Paddle on the main Streamlit page
  Paddle.Initialize({{
    token: '{PADDLE_TOKEN}',
    environment: 'production'
  }});
  console.log('[Paddle] Initialized on MAIN page — production mode');

  // Listen for checkout requests from iframe components
  window.addEventListener('message', function(event) {{
    if (event.data && event.data.type === 'paddle-checkout') {{
      console.log('[Paddle] Opening checkout for:', event.data.priceId);
      Paddle.Checkout.open({{
        items: [{{ priceId: event.data.priceId, quantity: 1 }}]
      }});
    }}
  }});
</script>
"""
        html = html.replace("</head>", inject_block + "\n</head>")
        patched = True

    # ──────────────────────────────────────
    # 4) Patch <noscript>
    # ──────────────────────────────────────
    old_noscript_msgs = [
        "You need to enable JavaScript to run this app.",
    ]
    new_noscript = """
    <div style="font-family:sans-serif; max-width:800px; margin:40px auto; padding:20px; line-height:1.8;">
      <h1>세월은간다 (Trytimeback) - AI 유튜브 요약 서비스</h1>
      <p>유튜브 강의 URL만 붙여넣으면 AI가 <strong>핵심 포인트 숏츠 5개</strong>와 <strong>상세 PDF 요약</strong>을 자동으로 생성합니다.</p>
      <h2>주요 기능</h2>
      <ul>
        <li>AI가 선별한 핵심 포인트 숏츠 5개 자동 추출</li>
        <li>강의 전체 내용을 정리한 상세 PDF 요약 다운로드</li>
        <li>한국어, 영어 등 다국어 자막 자동 감지</li>
        <li>PC, 모바일 반응형 디자인</li>
      </ul>
      <p>Basic $12.99/월 | Pro $29.99/월 — 연간 결제 시 최대 23%% 할인</p>
      <p><a href="https://trytimeback.com">trytimeback.com</a>에서 지금 시작하세요!</p>
    </div>
    """
    for old_msg in old_noscript_msgs:
        if old_msg in html:
            html = html.replace(old_msg, new_noscript)
            patched = True
            break

    # ──────────────────────────────────────
    # Save
    # ──────────────────────────────────────
    if patched:
        index_path.write_text(html, encoding="utf-8")
        print(f"✅ Patched v3 (SEO + Paddle): {index_path}")
    else:
        print(f"ℹ️  Already patched (v3): {index_path}")
else:
    print(f"⚠️  index.html not found at {index_path}")
