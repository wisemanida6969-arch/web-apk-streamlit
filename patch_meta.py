"""Patch Streamlit's index.html for comprehensive SEO (Korean-targeted)."""
import streamlit as st
import pathlib

# Find Streamlit's index.html
st_dir = pathlib.Path(st.__file__).parent
index_path = st_dir / "static" / "index.html"

if index_path.exists():
    html = index_path.read_text(encoding="utf-8")
    patched = False

    # ──────────────────────────────────────
    # 1) Set <html lang="ko">
    # ──────────────────────────────────────
    if '<html lang="ko">' not in html and "<html>" in html:
        html = html.replace("<html>", '<html lang="ko">')
        patched = True
    elif '<html lang="ko">' not in html and "<html " in html:
        # handle cases like <html class="...">
        import re
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
    # 3) Inject full SEO meta block in <head>
    # ──────────────────────────────────────
    SEO_MARKER = "<!-- SEO-PATCHED-V2 -->"
    if SEO_MARKER not in html:
        # Remove old partial meta tags from v1 patch if present
        import re
        html = re.sub(r'<meta\s+name="description"[^>]*>\n?', '', html)
        html = re.sub(r'<meta\s+property="og:[^"]*"[^>]*>\n?', '', html)

        seo_block = f"""{SEO_MARKER}
<!-- Primary Meta Tags -->
<meta name="description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다. 학습 시간을 80% 절약하세요!">
<meta name="keywords" content="유튜브 요약, AI 요약, 유튜브 강의 요약, PDF 요약, 핵심 숏츠, YouTube summary, AI lecture summary, trytimeback">
<meta name="author" content="Trytimeback">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://trytimeback.com">

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://trytimeback.com">
<meta property="og:title" content="세월은간다 - AI 유튜브 요약 · 핵심 숏츠 + PDF 추출">
<meta property="og:description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다. 학습 시간을 80% 절약하세요!">
<meta property="og:site_name" content="세월은간다 (Trytimeback)">
<meta property="og:locale" content="ko_KR">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="세월은간다 - AI 유튜브 요약 · 핵심 숏츠 + PDF 추출">
<meta name="twitter:description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성. 학습 시간 80% 절약!">

<!-- Naver Search Advisor -->
<meta name="naver-site-verification" content="">

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
  }},
  "featureList": [
    "AI 핵심 포인트 숏츠 5개 자동 추출",
    "상세 PDF 요약 다운로드",
    "다국어 자막 지원",
    "모바일 반응형 디자인"
  ]
}}
</script>
"""
        html = html.replace("</head>", seo_block + "\n</head>")
        patched = True

    # ──────────────────────────────────────
    # 4) Patch <noscript> — 구글 크롤러가 이걸 읽음
    # ──────────────────────────────────────
    old_noscript_msgs = [
        "You need to enable JavaScript to run this app.",
        "세월은간다 (Trytimeback) — 유튜브를 요약하고 학습 시간을 단축하는 최고의 AI 도구. "
        "유튜브 강의 URL을 붙여넣으면 핵심 포인트 숏츠 5개와 PDF 전체 요약을 "
        "몇 초 만에 받아보세요. trytimeback.com",
    ]
    new_noscript = """
    <div style="font-family:sans-serif; max-width:800px; margin:40px auto; padding:20px; line-height:1.8;">
      <h1>세월은간다 (Trytimeback) - AI 유튜브 요약 서비스</h1>
      <p>유튜브 강의 URL만 붙여넣으면 AI가 <strong>핵심 포인트 숏츠 5개</strong>와 <strong>상세 PDF 요약</strong>을 자동으로 생성합니다.</p>
      <h2>주요 기능</h2>
      <ul>
        <li>🎬 AI가 선별한 핵심 포인트 숏츠 5개 자동 추출</li>
        <li>📄 강의 전체 내용을 정리한 상세 PDF 요약 다운로드</li>
        <li>🌍 한국어, 영어 등 다국어 자막 자동 감지</li>
        <li>📱 PC · 모바일 반응형 디자인</li>
        <li>⚡ GPT-4o 기반 정확한 분석</li>
      </ul>
      <h2>요금제</h2>
      <p>Basic $12.99/월 (300분) | Pro $29.99/월 (1,200분) — 연간 결제 시 최대 23% 할인</p>
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
        print(f"✅ SEO v2 patched: {index_path}")
    else:
        print(f"ℹ️  Already patched (v2): {index_path}")
else:
    print(f"⚠️  index.html not found at {index_path}")
